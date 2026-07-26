import re
import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException
)


# =====================================================================================

def Get_Ping_Success_Rate(ping_output):
    """
    Extracts the success percentage from Cisco ping output.

    Example:
        Success rate is 100 percent (3/3)

    Returns:
        100
    """

    match = re.search(
        r"Success rate is (\d+) percent",
        ping_output
    )

    if match:
        return int(match.group(1))

    return 0


# =====================================================================================

def Verify_Loopback_Reachability():
    """
    Connects to every router and pings every other router's
    loopback address using Loopback0 as the source.

    This function does not modify or save any configuration.
    """

    with open("Topology.yaml", "r", encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file)

    username = data["global"]["auth"]["user"]
    password = data["global"]["auth"]["pass"]

    routers = list(data["nodes"].keys())

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for source_router in routers:

        management_ip = data["nodes"][source_router]["mgmt_ip"]

        device = {
            "device_type": "cisco_ios",
            "host": management_ip,
            "username": username,
            "password": password
        }

        connection = None

        print("\n" + "=" * 72)
        print(f"TESTING FROM {source_router}")
        print("=" * 72)

        try:
            print(f"Connecting to {management_ip}...")

            connection = ConnectHandler(**device)

            for destination_router in routers:

                # A router does not need to ping itself.
                if destination_router == source_router:
                    continue

                destination_loopback = (
                    data["nodes"][destination_router]["loop_ip"]
                )

                command = (
                    f"ping {destination_loopback} "
                    f"source Loopback0 repeat 3 timeout 1"
                )

                output = connection.send_command(
                    command,
                    read_timeout=30
                )

                success_rate = Get_Ping_Success_Rate(output)

                total_tests += 1

                if success_rate == 100:

                    print(
                        f"PASS: {source_router} → "
                        f"{destination_router} "
                        f"({destination_loopback})"
                    )

                    passed_tests += 1

                else:

                    print(
                        f"FAIL: {source_router} → "
                        f"{destination_router} "
                        f"({destination_loopback}) "
                        f"Success rate: {success_rate}%"
                    )

                    failed_tests.append(
                        {
                            "source": source_router,
                            "destination": destination_router,
                            "destination_ip": destination_loopback,
                            "success_rate": success_rate,
                            "output": output
                        }
                    )

        except NetmikoAuthenticationException:

            print(
                f"FAIL: Authentication failed for "
                f"{source_router}."
            )

            failed_tests.append(
                {
                    "source": source_router,
                    "destination": "ALL",
                    "destination_ip": "N/A",
                    "success_rate": 0,
                    "output": "Authentication failed"
                }
            )

        except NetmikoTimeoutException:

            print(
                f"FAIL: Connection timed out for "
                f"{source_router}."
            )

            failed_tests.append(
                {
                    "source": source_router,
                    "destination": "ALL",
                    "destination_ip": "N/A",
                    "success_rate": 0,
                    "output": "Connection timed out"
                }
            )

        except Exception as error:

            print(
                f"FAIL: Unexpected error for "
                f"{source_router}: {error}"
            )

            failed_tests.append(
                {
                    "source": source_router,
                    "destination": "ALL",
                    "destination_ip": "N/A",
                    "success_rate": 0,
                    "output": str(error)
                }
            )

        finally:

            if connection is not None:
                connection.disconnect()
                print(f"Disconnected from {source_router}.")

    print("\n" + "=" * 72)
    print("END-TO-END LOOPBACK REACHABILITY SUMMARY")
    print("=" * 72)

    print(f"Total ping tests:  {total_tests}")
    print(f"Passed ping tests: {passed_tests}")
    print(f"Failed ping tests: {len(failed_tests)}")

    if failed_tests:

        print("\nFailed tests:")

        for failure in failed_tests:

            print(
                f"  {failure['source']} → "
                f"{failure['destination']} "
                f"({failure['destination_ip']}): "
                f"{failure['success_rate']}%"
            )

        print(
            "\nOVERALL RESULT: FAIL — one or more "
            "loopback reachability tests failed."
        )

    else:

        print(
            "\nOVERALL RESULT: PASS — every router can "
            "reach every other router's loopback."
        )


# =====================================================================================

if __name__ == "__main__":
    Verify_Loopback_Reachability()
