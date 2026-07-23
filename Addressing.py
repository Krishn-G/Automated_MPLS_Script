import ipaddress

#=====================================================================================

def Define_IPs(matrix, base_subnet = "172.16.1.0/24"):
    subnets = list(ipaddress.ip_network(base_subnet).subnets(new_prefix=30))        #Creates /30 subnets from the /24

    Router_IPs = {}                                                                 #Dictionary to store router IP addresses
    
    subnet_id = 0
    n = len(matrix)

    for i in range(n):                                                              #Iterating only through upper triangle to avoid double links
        for j in range(i+1, n):
            link = matrix[i][j]

            if link != None:                                                        #If a link exists between these routers
                if (subnet_id >= len(subnets)):
                    raise ValueError("Not enough subnets to assign IP addresses to all routers")
            
                sub = subnets[subnet_id]                                            #Deriving Host IPs and assigning to router interfaces
                hosts = list(sub.hosts())

                rx_int = link[0]
                rx_ip = f"{hosts[0]}/30"
                ry_int = link[1]
                ry_ip = f"{hosts[1]}/30"

                for r_id, r_int, r_ip in [(i, rx_int, rx_ip), (j, ry_int, ry_ip)]:
                    if r_id not in Router_IPs:
                        Router_IPs[r_id] = {}
                    Router_IPs[r_id][r_int] = r_ip
                
                subnet_id += 1
    
    return Router_IPs
#=====================================================================================

if __name__ == '__main__':
    pass