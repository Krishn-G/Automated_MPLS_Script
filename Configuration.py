import ipaddress
from pathlib import Path


# =====================================================================================

def Convert_Address(cidr_address):

    interface = ipaddress.ip_interface(cidr_address)

    ip_address = str(interface.ip)
    subnet_mask = str(interface.network.netmask)

    return ip_address, subnet_mask

# =====================================================================================

def Generate_Core_Interface(interface_name, cidr_address):

    ip_address, subnet_mask = Convert_Address(cidr_address)

    commands = [
        f"interface {interface_name}",
        f"ip address {ip_address} {subnet_mask}",
        "ip ospf 1 area 0",
        "mpls ip",
        "no shutdown",
        "exit"
    ]

    return commands

# =====================================================================================

def Generate_Loopback(cidr_address):
    ip_address, subnet_mask = Convert_Address(cidr_address)

    commands = [
        "interface Loopback0",
        f"ip address {ip_address} {subnet_mask}",
        "ip ospf 1 area 0",
        "no shutdown",
        "exit"
    ]

    return commands

# =====================================================================================
# =====================================================================================

def Generate_Global_Config(hostname, loopback_cidr):

    loopback_ip, _ = Convert_Address(loopback_cidr)

    commands = [
        f"hostname {hostname}",
        "mpls label protocol ldp",
        "router ospf 1",
        f"router-id {loopback_ip}",
        "exit",
        "mpls ldp router-id Loopback0 force"
    ]

    return commands

# =====================================================================================

def Generate_Router_Config(hostname, interface_addresses):

    if "Lo0" not in interface_addresses:
        raise ValueError(f"{hostname} does not have a Lo0 address")

    loopback_cidr = interface_addresses["Lo0"]

    commands = []

    # Add router-wide configuration commands.
    commands.extend(
        Generate_Global_Config(hostname, loopback_cidr)
    )

    # Add Loopback0 configuration commands.
    commands.extend(
        Generate_Loopback(loopback_cidr)
    )

    # Add configuration for every physical core interface.
    for interface_name, cidr_address in interface_addresses.items():

        # Loopback0 was already configured above,
        # so skip it in this loop.
        if interface_name == "Lo0":
            continue

        commands.extend(
            Generate_Core_Interface(
                interface_name,
                cidr_address
            )
        )

    return commands

# =====================================================================================

def Generate_All_Router_Configs(router_ips):

    all_configs = {}

    for hostname, interface_addresses in router_ips.items():

        router_commands = Generate_Router_Config(hostname, interface_addresses)

        all_configs[hostname] = router_commands

    return all_configs

# =====================================================================================

def Save_All_Configs(all_configs, output_directory="generated_configs"):
    """
    Saves every router configuration into a separate .cfg file.

    Example files:
        generated_configs/P1.cfg
        generated_configs/PE1.cfg
    """

    output_path = Path(output_directory)

    # Create the directory if it does not already exist.
    output_path.mkdir(parents=True, exist_ok=True)

    for hostname, commands in all_configs.items():

        file_path = output_path / f"{hostname}.cfg"

        with open(file_path, "w", encoding="utf-8") as config_file:

            for command in commands:
                config_file.write(command + "\n")

        print(f"Saved configuration: {file_path}")

# =====================================================================================

if __name__ == '__main__':

    test_p1_interfaces = {
        "e0/1": "172.16.1.1/30",
        "e0/2": "172.16.1.5/30",
        "e0/3": "172.16.1.9/30",
        "e2/2": "172.16.1.13/30",
        "e2/3": "172.16.1.17/30",
        "Lo0": "10.10.100.101/32"
    }

    test_commands = Generate_Router_Config(
        hostname="P1",
        interface_addresses=test_p1_interfaces
    )

    for command in test_commands:
        print(command)
