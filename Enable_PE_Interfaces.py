import time
import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

PE_ROUTERS = [
    "PE1",
    "PE2",
    "PE3",
    "PE4"
]


# =====================================================================================

def Enable_PE_Interfaces():
    """
    Enables GigabitEthernet2 and GigabitEthernet3
    on every PE router.

    The configurations are not saved in this step.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    successful_routers = []
    failed_routers = []

    for hostname in PE_ROUTERS:

        management_ip = data["nodes"][hostname]["mgmt_ip"]

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        commands = [
            "interface GigabitEthernet2",
            "no shutdown",
            "exit",
            "interface GigabitEthernet3",
            "no shutdown",
            "exit"
        ]

        connection = None

        print("\n" + "=" * 65)
        print(f"ENABLING CORE INTERFACES ON {hostname}")
        print("=" * 65)

        try:
            connection = ConnectHandler(**device)

            print(f"Connected to {hostname} at {management_ip}.")

            output = connection.send_config_set(
                commands,
                read_timeout=60
            )

            print(output)

            error_markers = [
                "% Invalid input",
                "% Incomplete command",
                "% Ambiguous command"
            ]

            if any(marker in output for marker in error_markers):
                print(f"FAIL: {hostname} returned a configuration error.")
                failed_routers.append(hostname)
                continue

            print("Waiting five seconds for interfaces to initialize...")
            time.sleep(5)

            interface_output = connection.send_command(
                "show ip interface brief | "
                "include GigabitEthernet2|GigabitEthernet3",
                read_timeout=30
            )

            print("\nInterface status:")
            print(interface_output)

            successful_routers.append(hostname)

        except NetmikoAuthenticationException:
            print(f"FAIL: Authentication failed for {hostname}.")
            failed_routers.append(hostname)

        except NetmikoTimeoutException:
            print(f"FAIL: Connection timed out for {hostname}.")
            failed_routers.append(hostname)

        except Exception as error:
            print(f"FAIL: Unexpected error for {hostname}: {error}")
            failed_routers.append(hostname)

        finally:
            if connection is not None:
                connection.disconnect()
                print(f"Disconnected from {hostname}.")

    print("\n" + "=" * 65)
    print("INTERFACE ENABLEMENT SUMMARY")
    print("=" * 65)

    print("Successfully processed:")

    for hostname in successful_routers:
        print(f"  - {hostname}")

    if failed_routers:
        print("\nFailed routers:")

        for hostname in failed_routers:
            print(f"  - {hostname}")
    else:
        print("\nAll PE core interfaces were enabled successfully.")

    print("\nThe configurations have NOT been saved yet.")


# =====================================================================================

if __name__ == "__main__":
    Enable_PE_Interfaces()
