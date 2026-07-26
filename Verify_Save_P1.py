import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Verify_And_Save_P1():
    """
    Connects to P1, runs verification commands,
    and saves the configuration after confirmation.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]
    management_ip = data["nodes"]["P1"]["mgmt_ip"]

    device = {
        "device_type": "cisco_ios",
        "host": management_ip,
        "username": username,
        "password": password
    }

    verification_commands = [
        "show ip interface brief",
        "show ip ospf interface brief",
        "show ip ospf neighbor",
        "show mpls interfaces",
        "show mpls ldp discovery",
        "show running-config | section router ospf",
        "show running-config | include mpls ldp router-id"
    ]

    connection = None

    try:
        print(f"Connecting to P1 at {management_ip}...")

        connection = ConnectHandler(**device)

        print("Connected successfully.")

        for command in verification_commands:

            print("\n" + "=" * 70)
            print(command)
            print("=" * 70)

            output = connection.send_command(
                command,
                read_timeout=60
            )

            print(output)

        print("\nVerification commands completed.")
        print(
            "OSPF and LDP neighbors may be empty because "
            "the other routers are not configured yet."
        )

        confirmation = input(
            '\nType "SAVE" exactly to save P1 configuration: '
        )

        if confirmation != "SAVE":
            print("Configuration was not saved.")
            return

        print("\nSaving P1 configuration...")

        save_output = connection.save_config()

        print(save_output)
        print("\nP1 configuration was saved successfully.")

    finally:
        if connection is not None:
            connection.disconnect()
            print("Disconnected from P1.")


# =====================================================================================

if __name__ == "__main__":

    try:
        Verify_And_Save_P1()

    except NetmikoAuthenticationException:
        print("Authentication failed. Check the username and password.")

    except NetmikoTimeoutException:
        print("Connection timed out. Check network connectivity and SSH.")

    except Exception as error:
        print(f"An unexpected error occurred: {error}")
