from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

#=====================================================================================

BGP_Rs = ["RR1", "RR2", "PE1", "PE2", "PE3", "PE4"]
Routers = {"RR": ["RR1", "RR2"],
           "Clients": ["PE1", "PE2", "PE3", "PE4"]}

#=====================================================================================

def BGP_Config(asn, hostname, Router_IPs, data):
    """
    Generates BGP Config for a specific router
    """
    lines = [f"router bgp {asn}",
        " bgp log-neighbor-changes",
        " no bgp default ipv4-unicast"
        ]
    
    if hostname in Routers["RR"]:
        peers = [rr for rr in Routers["RR"] if rr!=hostname] + Routers["Clients"]
    elif hostname in Routers["Clients"]:
        peers = Routers["RR"]
    else:
        return []
    
    for peer in peers:
        peer_ip = data['nodes'][peer]['loop_ip']

        lines.extend([
            f" neighbor {peer_ip} remote-as {asn}",
            f" neighbor {peer_ip} update-source Loopback0"
        ])

    lines.append(" address-family vpnv4")

    for peer in peers:
        peer_ip = data['nodes'][peer]['loop_ip']
        lines.append(f"  neighbor {peer_ip} activate")
        lines.append(f"  neighbor {peer_ip} send-community extended")
        
        # If this router is an RR and the peer is a client, set route-reflector-client
        if hostname in Routers["RR"] and peer in Routers["Clients"]:
            lines.append(f"  neighbor {peer_ip} route-reflector-client")
            
    lines.append(" exit-address-family")

    return lines


def All_BGP_Generate_Config(asn, Router_IPs, data):
    All_BGP_Configs = {}
    for hostname in BGP_Rs:
        bgp_config = BGP_Config(asn, hostname, Router_IPs, data)

        All_BGP_Configs[hostname] = bgp_config

    return All_BGP_Configs

def BGP_Setup(asn, Router_IPs, username, password, data):
    configs = All_BGP_Generate_Config(asn, Router_IPs, data)

    for hostname, config_lines in configs.items():

        device_ip = data["nodes"][hostname]["mgmt_ip"]

        device = {
            'device_type': 'cisco_ios',
            'host': device_ip,
            'username': username,
            'password': password,
        }

        print(f"--- Attempting connection to {hostname} ({device_ip}) ---")

        try:
            # 1. Establish the SSH connection
            net_connect = ConnectHandler(**device)
            
            # (Optional) Enter enable mode if your user doesn't log in at privilege level 15
            # net_connect.enable()
            
            print(f"Successfully connected to {hostname}. Pushing BGP configuration...")
            
            # 2. Push the configuration list
            # send_config_set automatically enters 'conf t', sends the lines, and exits
            output = net_connect.send_config_set(config_lines)
            
            # Print the router's CLI output so you can verify it worked
            print(output)
            
            # 3. Save the running config to startup config (copy run start)
            net_connect.save_config()
            print(f"Saved running configuration on {hostname}.")

            # 4. Gracefully close the connection
            net_connect.disconnect()

        except NetmikoAuthenticationException:
            print(f"ERROR: Authentication failed for {hostname}. Check username/password.")
        except NetmikoTimeoutException:
            print(f"ERROR: Connection timed out. {hostname} ({device_ip}) is unreachable.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred on {hostname}: {e}")
        
        print("-" * 50)


#=====================================================================================

if __name__ == '__main__':
    BGP_Setup()