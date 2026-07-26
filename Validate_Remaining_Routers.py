import yaml

from pathlib import Path
from collections import Counter

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

ROUTERS_TO_VALIDATE = [
    "P2",
    "P3",
    "P4",
    "PE1",
    "PE2",
    "PE3",
    "PE4"
]


# =====================================================================================

def Get_Expected_Core_Interfaces(data, hostname):
    """
    Reads the expected core interfaces for one router
    from the node_interfaces section of Topology.yaml.
    """

    interface_entries = data["node_interfaces"][hostname]["intf"]

    expected_interfaces = []

    for interface_entry in interface_entries:
        interface_name = next(iter(interface_entry))
        expected_interfaces.append(interface_name)

    return expected_interfaces


# =====================================================================================

def Read_Config_File(hostname):
    """
    Reads one generated configuration file and returns
    all non-empty commands.
    """

    config_path = Path("generated_configs") / f"{hostname}.cfg"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {config_path}"
        )

    commands = []

    with config_path.open("r", encoding="utf-8") as config_file:
        for line in config_file:
            command = line.strip()

            if command:
                commands.append(command)

    if not commands:
        raise ValueError(
            f"{config_path} is empty"
        )

    return commands


# =====================================================================================

def Validate_Config_File(data, hostname, commands):
    """
    Performs local safety checks on one generated configuration.
    """

    errors = []

    expected_core_interfaces = Get_Expected_Core_Interfaces(
        data,
        hostname
    )

    # Collect all interface configuration sections.
    configured_interfaces = []

    for command in commands:
        if command.startswith("interface "):
            interface_name = command.split(maxsplit=1)[1]
            configured_interfaces.append(interface_name)

    # Check for duplicate interface sections.
    interface_counts = Counter(configured_interfaces)

    for interface_name, count in interface_counts.items():
        if count > 1:
            errors.append(
                f"Duplicate interface section: {interface_name}"
            )

    # Protect the management interface.
    protected_interfaces = {
        "e0/0",
        "ethernet0/0",
        "g0/0",
        "gigabitethernet0/0"
    }

    for interface_name in configured_interfaces:
        if interface_name.lower() in protected_interfaces:
            errors.append(
                f"Management interface is included: {interface_name}"
            )

    # Loopback0 must be present.
    if "Loopback0" not in configured_interfaces:
        errors.append("Loopback0 configuration is missing")

    # Every expected core interface must be present.
    for interface_name in expected_core_interfaces:
        if interface_name not in configured_interfaces:
            errors.append(
                f"Expected core interface is missing: {interface_name}"
            )

    # No unexpected physical interface should be present.
    allowed_interfaces = set(expected_core_interfaces)
    allowed_interfaces.add("Loopback0")

    for interface_name in configured_interfaces:
        if interface_name not in allowed_interfaces:
            errors.append(
                f"Unexpected interface found: {interface_name}"
            )

    expected_mpls_count = len(expected_core_interfaces)
    actual_mpls_count = commands.count("mpls ip")

    if actual_mpls_count != expected_mpls_count:
        errors.append(
            f"Expected {expected_mpls_count} 'mpls ip' commands, "
            f"but found {actual_mpls_count}"
        )

    expected_ospf_count = len(expected_core_interfaces) + 1
    actual_ospf_count = commands.count("ip ospf 1 area 0")

    if actual_ospf_count != expected_ospf_count:
        errors.append(
            f"Expected {expected_ospf_count} OSPF interface commands, "
            f"but found {actual_ospf_count}"
        )

    expected_loopback_ip = data["nodes"][hostname]["loop_ip"]

    expected_loopback_command = (
        f"ip address {expected_loopback_ip} 255.255.255.255"
    )

    if expected_loopback_command not in commands:
        errors.append(
            f"Expected Loopback0 address is missing: "
            f"{expected_loopback_command}"
        )

    expected_router_id = f"router-id {expected_loopback_ip}"

    if expected_router_id not in commands:
        errors.append(
            f"Expected OSPF router ID is missing: {expected_router_id}"
        )

    return errors, expected_core_interfaces


# =====================================================================================

def Check_Interfaces_On_Router(
    connection,
    hostname,
    expected_core_interfaces
):
    """
    Runs a read-only show command for every expected core interface.
    """

    errors = []

    invalid_markers = [
        "% Invalid input",
        "% Incomplete command",
        "% Ambiguous command",
        "Invalid interface",
        "No such interface"
    ]

    for interface_name in expected_core_interfaces:

        output = connection.send_command(
            f"show interfaces {interface_name}",
            read_timeout=30
        )

        interface_is_invalid = any(
            marker in output
            for marker in invalid_markers
        )

        if interface_is_invalid:
            errors.append(
                f"{hostname}: interface {interface_name} "
                f"was not recognized by Cisco IOS"
            )
        else:
            print(
                f"  Interface confirmed on router: {interface_name}"
            )

    return errors


# =====================================================================================

def Validate_Remaining_Routers():
    """
    Validates the generated configuration files and confirms
    the expected physical interfaces exist on all remaining routers.

    No router configuration is changed.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    passed_routers = []
    failed_routers = []

    for hostname in ROUTERS_TO_VALIDATE:

        management_ip = data["nodes"][hostname]["mgmt_ip"]
        connection = None

        print("\n" + "=" * 65)
        print(f"VALIDATING {hostname} AT {management_ip}")
        print("=" * 65)

        try:
            commands = Read_Config_File(hostname)

            config_errors, expected_interfaces = Validate_Config_File(
                data,
                hostname,
                commands
            )

            if config_errors:
                print("Configuration-file validation failed:")

                for error in config_errors:
                    print(f"  ERROR: {error}")

                failed_routers.append(hostname)
                continue

            print("Generated configuration file passed all checks.")

            device = {
                "device_type": "cisco_ios",
                "host": management_ip,
                "username": username,
                "password": password
            }

            print("Connecting to verify physical interfaces...")

            connection = ConnectHandler(**device)

            interface_errors = Check_Interfaces_On_Router(
                connection,
                hostname,
                expected_interfaces
            )

            if interface_errors:
                for error in interface_errors:
                    print(f"  ERROR: {error}")

                failed_routers.append(hostname)
            else:
                print(
                    f"{hostname} passed all local and remote checks."
                )
                passed_routers.append(hostname)

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
    print("VALIDATION SUMMARY")
    print("=" * 65)

    print("Passed routers:")

    for hostname in passed_routers:
        print(f"  - {hostname}")

    if failed_routers:
        print("\nFailed routers:")

        for hostname in failed_routers:
            print(f"  - {hostname}")

        print(
            "\nDo not push configurations until every router passes."
        )

    else:
        print("\nAll seven routers passed validation.")
        print("No router configuration was changed.")


# =====================================================================================

if __name__ == "__main__":
    Validate_Remaining_Routers()
