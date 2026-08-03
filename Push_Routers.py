import yaml

from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

ROUTERS_TO_CONFIGURE = [
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


# =====================================================================================

def Load_Router_Commands(hostname):
    """
    Reads one router's generated .cfg file and returns
    its commands as a Python list.
    """

    config_file = Path("generated_configs") / f"{hostname}.cfg"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file is missing: {config_file}"
        )

    commands = []

    with config_file.open("r", encoding="utf-8") as file:
        for line in file:
            command = line.strip()

            if command:
                commands.append(command)

    if not commands:
        raise ValueError(
            f"{config_file} is empty"
        )

    return commands


# =====================================================================================

def Validate_Router_Commands(hostname, commands):
    """
    Performs safety checks before sending a configuration.
    """

    protected_interfaces = {
        "interface e0/0",
        "interface Ethernet0/0",
        "interface ethernet0/0",
        "interface g0/0",
        "interface GigabitEthernet0/0",
        "interface gigabitethernet0/0"
    }

    for command in commands:
        if command in protected_interfaces:
            raise ValueError(
                f"{hostname}: management interface found in configuration"
            )

    if f"hostname {hostname}" not in commands:
        raise ValueError(
            f"{hostname}: hostname command is missing"
        )

    if "interface Loopback0" not in commands:
        raise ValueError(
            f"{hostname}: Loopback0 configuration is missing"
        )

    # if "mpls ldp router-id Loopback0 force" not in commands:
    #     raise ValueError(
    #         f"{hostname}: MPLS LDP router ID is missing"
    #     )


# =====================================================================================

def Preflight_Check():
    """
    Confirms that every configuration and backup file exists
    before any router is changed.
    """

    prepared_configs = {}

    for hostname in ROUTERS_TO_CONFIGURE:

        backup_file = (
            Path("backups") /
            f"{hostname}_before_mpls.cfg"
        )

        if not backup_file.exists():
            raise FileNotFoundError(
                f"Backup is missing for {hostname}: {backup_file}"
            )

        commands = Load_Router_Commands(hostname)

        Validate_Router_Commands(
            hostname,
            commands
        )

        prepared_configs[hostname] = commands

    return prepared_configs


# =====================================================================================

def Push_Routers():
    """
    Pushes generated configurations to the remaining seven routers.

    The configurations are applied to running-config only.
    They are not saved to startup-config in this step.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    print("Running preflight safety checks...")

    prepared_configs = Preflight_Check()

    print("All preflight checks passed.\n")

    print("The following routers will be configured:")

    for hostname in ROUTERS_TO_CONFIGURE:
        management_ip = data["nodes"][hostname]["mgmt_ip"]
        command_count = len(prepared_configs[hostname])

        print(
            f"  {hostname}: {management_ip} "
            f"({command_count} commands)"
        )

    print(
        "\nThis will modify the running configuration "
        "of all seven routers."
    )

    print("The configurations will NOT be saved yet.")

    confirmation = input(
        '\nType "PUSH ALL" exactly to continue: '
    )

    if confirmation != "PUSH ALL":
        print("Operation cancelled. No configurations were sent.")
        return

    successful_routers = []
    failed_routers = []

    for hostname in ROUTERS_TO_CONFIGURE:

        management_ip = data["nodes"][hostname]["mgmt_ip"]
        commands = prepared_configs[hostname]

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        connection = None

        print("\n" + "=" * 65)
        print(f"CONFIGURING {hostname} AT {management_ip}")
        print("=" * 65)

        try:
            connection = ConnectHandler(**device)

            print("Connected successfully.")
            print(f"Sending {len(commands)} commands...\n")

            output = connection.send_config_set(
                config_commands=commands,
                read_timeout=120
            )

            print(output)

            error_markers = [
                "% Invalid input",
                "% Incomplete command",
                "% Ambiguous command",
                "% Unrecognized command"
            ]

            detected_errors = [
                marker
                for marker in error_markers
                if marker in output
            ]

            if detected_errors:
                print(
                    f"\n{hostname} returned Cisco IOS "
                    f"configuration errors."
                )

                for marker in detected_errors:
                    print(f"  - {marker}")

                failed_routers.append(hostname)

            else:
                print(
                    f"\n{hostname} running configuration "
                    f"was updated successfully."
                )

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
    print("CONFIGURATION PUSH SUMMARY")
    print("=" * 65)

    print("Successfully updated:")

    for hostname in successful_routers:
        print(f"  - {hostname}")

    if failed_routers:
        print("\nFailed or returned errors:")

        for hostname in failed_routers:
            print(f"  - {hostname}")

        print(
            "\nDo not save any configurations until "
            "the failures have been investigated."
        )

    else:
        print("\nAll eight routers were updated successfully.")
        print("The configurations have NOT been saved yet.")


# =====================================================================================

if __name__ == "__main__":
    Push_Routers()