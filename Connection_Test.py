import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Test_Connection():
    """
    Connects to P1 using information stored in Topology.yaml,
    runs a show command, and disconnects.
    """

    # Open and read the YAML Source of Truth file.
    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    # Get the shared username and password.
    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    # Get P1's management IP address.
    p1_management_ip = data["nodes"]["P1"]["mgmt_ip"]

    # Netmiko requires the device information in a dictionary.
    p1_device = {
        "device_type": "cisco_ios",
        "host": p1_management_ip,
        "username": username,
        "password": password
    }

    print(f"Connecting to P1 at {p1_management_ip}...")

    connection = ConnectHandler(**p1_device)

    print("Connected successfully.\n")

    output = connection.send_command(
        "show ip interface brief"
    )

    print(output)

    connection.disconnect()

    print("\nDisconnected from P1.")


# =====================================================================================

if __name__ == "__main__":

    try:
        Test_Connection()

    except NetmikoAuthenticationException:
        print("Authentication failed. Check the username and password.")

    except NetmikoTimeoutException:
        print("Connection timed out. Check network connectivity and SSH.")

    except Exception as error:
        print(f"An unexpected error occurred: {error}")
