import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Count_Operational_LDP_Neighbors(ldp_output):
    """
    Counts MPLS LDP neighbors whose session state is operational.

    Cisco IOS normally displays an operational neighbor as:

        State: Oper; Msgs sent/rcvd: ...
    """

    neighbor_count = 0

    for line in ldp_output.splitlines():

        if "State: Oper" in line:
            neighbor_count += 1

    return neighbor_count


# =====================================================================================

def Verify_All_LDP_Neighbors():
    """
    Connects to every router and checks whether it has the expected
    number of operational MPLS LDP neighbors.

    This function does not modify or save router configuration.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    routers = list(data["nodes"].keys())

    passed_routers = []
    failed_routers = []

    for hostname in routers:

        management_ip = data["nodes"][hostname]["mgmt_ip"]

        # Every core link should produce one direct LDP neighbor.
        expected_neighbors = len(
            data["node_interfaces"][hostname]["intf"]
        )

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        connection = None

        print("\n" + "=" * 70)
        print(f"VERIFYING MPLS LDP ON {hostname}")
        print("=" * 70)

        try:
            print(f"Connecting to {management_ip}...")

            connection = ConnectHandler(**device)

            ldp_output = connection.send_command(
                "show mpls ldp neighbor",
                read_timeout=60
            )

            actual_neighbors = Count_Operational_LDP_Neighbors(
                ldp_output
            )

            print(f"Expected operational LDP neighbors: {expected_neighbors}")
            print(f"Actual operational LDP neighbors:   {actual_neighbors}")

            if actual_neighbors == expected_neighbors:

                print(
                    f"PASS: {hostname} has all expected "
                    f"operational LDP neighbors."
                )

                passed_routers.append(hostname)

            else:

                print(
                    f"FAIL: {hostname} is missing one or more "
                    f"operational LDP neighbors."
                )

                print("\nRaw LDP output:")
                print(ldp_output)

                failed_routers.append(hostname)

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

    print("\n" + "=" * 70)
    print("MPLS LDP AUTOMATED VERIFICATION SUMMARY")
    print("=" * 70)

    print("\nPassed routers:")

    for hostname in passed_routers:
        print(f"  - {hostname}")

    if failed_routers:

        print("\nFailed routers:")

        for hostname in failed_routers:
            print(f"  - {hostname}")

        print(
            "\nOVERALL RESULT: FAIL — one or more routers "
            "have an MPLS LDP problem."
        )

    else:

        print(
            "\nOVERALL RESULT: PASS — all routers have "
            "the expected operational LDP neighbors."
        )


# =====================================================================================

if __name__ == "__main__":
    Verify_All_LDP_Neighbors()
