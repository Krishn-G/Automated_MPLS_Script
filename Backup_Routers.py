import yaml

from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Generate_Backups():
    """
    Connects to P1, P2, P3, P4, PE1, PE2, PE3 and PE4.

    It collects each router's running configuration and
    saves it inside the backups directory.

    This function does not modify any router.
    """

    # Read the Source of Truth file.
    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    routers_to_backup = [
        "P1",
        "P2",
        "P3",
        "P4",
        "PE1",
        "PE2",
        "PE3",
        "PE4",
        "RR1",
        "RR2"
    ]

    # Create the backup directory if it does not already exist.
    backup_directory = Path("backups")
    backup_directory.mkdir(parents=True, exist_ok=True)

    successful_backups = []
    failed_backups = []

    for hostname in routers_to_backup:

        management_ip = data["nodes"][hostname]["mgmt_ip"]

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        backup_file = (
            backup_directory /
            f"{hostname}_before_mpls.cfg"
        )

        connection = None

        print("\n" + "=" * 60)
        print(f"Backing up {hostname} at {management_ip}")
        print("=" * 60)

        try:
            connection = ConnectHandler(**device)

            print("Connected successfully.")
            # print("Collecting running configuration...")

            connection.save_config()

            running_config = connection.send_command(
                "show startup-config",
                read_timeout=60
            )

            backup_file.write_text(
                running_config + "\n",
                encoding="utf-8"
            )

            print(f"Backup saved: {backup_file}")

            successful_backups.append(hostname)

        except NetmikoAuthenticationException:
            print(f"Authentication failed for {hostname}.")
            failed_backups.append(hostname)

        except NetmikoTimeoutException:
            print(f"Connection timed out for {hostname}.")
            failed_backups.append(hostname)

        except Exception as error:
            print(f"Unexpected error for {hostname}: {error}")
            failed_backups.append(hostname)

        finally:
            if connection is not None:
                connection.disconnect()
                print(f"Disconnected from {hostname}.")

    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)

    print("Successful backups:")

    for hostname in successful_backups:
        print(f"  - {hostname}")

    if failed_backups:
        print("\nFailed backups:")

        for hostname in failed_backups:
            print(f"  - {hostname}")
    else:
        print("\nAll seven routers were backed up successfully.")


# =====================================================================================

if __name__ == "__main__":
    Generate_Backups()
    