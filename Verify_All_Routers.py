import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

ROUTERS = [
    "P1",
    "P2",
    "P3",
    "P4",
    "PE1",
    "PE2",
    "PE3",
    "PE4"
]


# =====================================================================================

def Verify_All_Routers():
    """
    Connects to all routers and runs read-only OSPF/MPLS
    verification commands.

    This function does not change or save configuration.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    verification_commands = [
        "show ip interface brief",
        "show ip ospf neighbor",
        "show mpls interfaces",
        "show mpls ldp neighbor",
        "show ip route ospf"
    ]

    successful_routers = []
    failed_routers = []

    for hostname in ROUTERS:

        management_ip = data["nodes"][hostname]["mgmt_ip"]

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        connection = None

        print("\n" + "=" * 75)
        print(f"VERIFYING {hostname} AT {management_ip}")
        print("=" * 75)

        try:
            connection = ConnectHandler(**device)

            print("Connected successfully.")

            for command in verification_commands:

                print("\n" + "-" * 70)
                print(command)
                print("-" * 70)

                output = connection.send_command(
                    command,
                    read_timeout=60
                )

                print(output)

            successful_routers.append(hostname)

        except NetmikoAuthenticationException:
            print(f"Authentication failed for {hostname}.")
            failed_routers.append(hostname)

        except NetmikoTimeoutException:
            print(f"Connection timed out for {hostname}.")
            failed_routers.append(hostname)

        except Exception as error:
            print(f"Unexpected error for {hostname}: {error}")
            failed_routers.append(hostname)

        finally:
            if connection is not None:
                connection.disconnect()
                print(f"\nDisconnected from {hostname}.")

    print("\n" + "=" * 75)
    print("CONNECTION AND COMMAND SUMMARY")
    print("=" * 75)

    print("Successfully verified:")

    for hostname in successful_routers:
        print(f"  - {hostname}")

    if failed_routers:
        print("\nFailed routers:")

        for hostname in failed_routers:
            print(f"  - {hostname}")
    else:
        print("\nVerification commands ran successfully on all eight routers.")

    print("\nNo configurations were changed or saved.")


# =====================================================================================

if __name__ == "__main__":
    Verify_All_Routers()
