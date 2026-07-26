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

def Save_All_Routers():
    """
    Connects to all eight routers and saves each running
    configuration to startup configuration.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    print("The following routers will be saved:")

    for hostname in ROUTERS:
        management_ip = data["nodes"][hostname]["mgmt_ip"]
        print(f"  - {hostname}: {management_ip}")

    print(
        "\nThis will copy each router's running configuration "
        "to startup configuration."
    )

    confirmation = input(
        '\nType "SAVE ALL" exactly to continue: '
    )

    if confirmation != "SAVE ALL":
        print("Operation cancelled. No configurations were saved.")
        return

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

        print("\n" + "=" * 65)
        print(f"SAVING {hostname} AT {management_ip}")
        print("=" * 65)

        try:
            connection = ConnectHandler(**device)

            print("Connected successfully.")
            print("Saving running configuration...")

            output = connection.save_config()

            print(output)

            error_markers = [
                "% Invalid input",
                "% Incomplete command",
                "% Error",
                "Failed"
            ]

            error_detected = any(
                marker in output
                for marker in error_markers
            )

            if error_detected:
                print(f"{hostname} returned an error while saving.")
                failed_routers.append(hostname)
            else:
                print(f"{hostname} configuration was saved.")
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
                print(f"Disconnected from {hostname}.")

    print("\n" + "=" * 65)
    print("SAVE SUMMARY")
    print("=" * 65)

    print("Successfully saved:")

    for hostname in successful_routers:
        print(f"  - {hostname}")

    if failed_routers:
        print("\nFailed to save:")

        for hostname in failed_routers:
            print(f"  - {hostname}")

        print(
            "\nInvestigate the failed routers before restarting the lab."
        )

    else:
        print("\nAll eight router configurations were saved successfully.")


# =====================================================================================

if __name__ == "__main__":
    Save_All_Routers()
