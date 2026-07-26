import yaml

from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Backup_P1():
    """
    Connects to P1, collects the running configuration,
    and saves it locally before any changes are made.
    """

    # Read the Source of Truth file.
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

    # Create the backups directory if it does not exist.
    backup_directory = Path("backups")
    backup_directory.mkdir(parents=True, exist_ok=True)

    backup_file = backup_directory / "P1_before_mpls.cfg"

    connection = None

    try:
        print(f"Connecting to P1 at {management_ip}...")

        connection = ConnectHandler(**device)

        print("Connected successfully.")
        print("Collecting the running configuration...")

        running_config = connection.send_command(
            "show running-config",
            read_timeout=60
        )

        backup_file.write_text(
            running_config + "\n",
            encoding="utf-8"
        )

        print(f"Backup saved successfully: {backup_file}")

    finally:
        if connection is not None:
            connection.disconnect()
            print("Disconnected from P1.")


# =====================================================================================

if __name__ == "__main__":

    try:
        Backup_P1()

    except NetmikoAuthenticationException:
        print("Authentication failed. Check the username and password.")

    except NetmikoTimeoutException:
        print("Connection timed out. Check P1 connectivity and SSH.")

    except Exception as error:
        print(f"An unexpected error occurred: {error}")
