import yaml

from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Load_P1_Commands():
    """
    Reads P1's generated configuration file and returns
    its commands as a Python list.
    """

    config_file = Path("generated_configs/P1.cfg")

    if not config_file.exists():
        raise FileNotFoundError(
            "generated_configs/P1.cfg does not exist"
        )

    commands = []

    with config_file.open("r", encoding="utf-8") as file:

        for line in file:
            command = line.strip()

            # Ignore empty lines.
            if command:
                commands.append(command)

    if not commands:
        raise ValueError("P1.cfg is empty")

    return commands


# =====================================================================================

def Validate_P1_Commands(commands):
    """
    Performs safety checks before sending the commands.
    """

    protected_interfaces = {
        "interface e0/0",
        "interface Ethernet0/0",
        "interface ethernet0/0"
    }

    for command in commands:

        if command in protected_interfaces:
            raise ValueError(
                "Safety check failed: P1.cfg contains "
                "the management interface Ethernet0/0"
            )

    if "interface Loopback0" not in commands:
        raise ValueError(
            "Safety check failed: Loopback0 is missing"
        )

    if "mpls ldp router-id Loopback0 force" not in commands:
        raise ValueError(
            "Safety check failed: the MPLS LDP router ID is missing"
        )

    print("Configuration safety checks passed.")


# =====================================================================================

def Push_P1():
    """
    Connects to P1 and applies its generated configuration
    to the running configuration.

    This function does not save the configuration.
    """

    # Read the Source of Truth.
    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]
    management_ip = data["nodes"]["P1"]["mgmt_ip"]

    commands = Load_P1_Commands()

    Validate_P1_Commands(commands)

    print("\nCommands that will be sent to P1:\n")

    for command in commands:
        print(command)

    print(f"\nTotal commands: {len(commands)}")
    print(f"Target router: P1 at {management_ip}")
    print("\nThis will modify P1's running configuration.")

    confirmation = input(
        'Type "PUSH" exactly to continue: '
    )

    if confirmation != "PUSH":
        print("Operation cancelled. Nothing was sent to P1.")
        return

    device = {
        "device_type": "cisco_ios",
        "host": management_ip,
        "username": username,
        "password": password
    }

    connection = None

    try:
        print(f"\nConnecting to P1 at {management_ip}...")

        connection = ConnectHandler(**device)

        print("Connected successfully.")
        print("Sending the configuration...\n")

        output = connection.send_config_set(
            config_commands=commands,
            read_timeout=120
        )

        print(output)
        print("\nP1 running configuration was updated.")
        print("The configuration has NOT been saved yet.")

    finally:
        if connection is not None:
            connection.disconnect()
            print("Disconnected from P1.")


# =====================================================================================

if __name__ == "__main__":

    try:
        Push_P1()

    except NetmikoAuthenticationException:
        print(
            "Authentication failed. "
            "Check the username and password."
        )

    except NetmikoTimeoutException:
        print(
            "Connection timed out. "
            "Check network connectivity and SSH."
        )

    except Exception as error:
        print(f"An unexpected error occurred: {error}")
