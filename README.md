# Automated MPLS Service Provider Lab

This project automatically generates, deploys, and verifies an MPLS service-provider underlay in Cisco CML.

## Topology

The MPLS core contains eight routers:

- P1
- P2
- P3
- P4
- PE1
- PE2
- PE3
- PE4

The routers use a separate out-of-band management network for SSH access.

## Technologies

- Python 3
- YAML
- Netmiko
- Cisco IOS and IOS XE
- OSPF
- MPLS LDP
- Cisco Modeling Labs

## Source of Truth

The network information is stored in:

`Topology.yaml`

It contains:

- Management IP addresses
- Loopback IP addresses
- Authentication information
- Router-to-router interface mappings
- Infrastructure subnet

## Addressing

The infrastructure subnet is:

`172.16.1.0/24`

The Python IPAM logic divides this subnet into `/30` point-to-point networks.

Loopback addresses use `/32` prefixes.

## Main Python Files

### Topology.py

Builds the network adjacency matrix from `Topology.yaml`.

### Addressing.py

Divides the infrastructure subnet into `/30` networks and assigns IP addresses to both ends of every link.

### SP_Controller.py

Loads the Source of Truth, builds the topology, calculates interface addresses, and generates router configurations.

### Configuration.py

Generates Cisco IOS configuration commands for:

- Hostnames
- Loopback0
- OSPF
- MPLS LDP
- Core-facing interfaces

It also saves one configuration file for each router.

## Generated Configurations

Generated router configurations are stored in:

`generated_configs/`

The folder contains:

- P1.cfg
- P2.cfg
- P3.cfg
- P4.cfg
- PE1.cfg
- PE2.cfg
- PE3.cfg
- PE4.cfg

## Backups

Router configurations taken before MPLS deployment are stored in:

`backups/`

## Deployment Scripts

The following scripts were used to deploy the configurations:

- Push_P1.py
- Push_Remaining_Routers.py
- Enable_PE_Interfaces.py
- Save_All_Routers.py

## Verification Scripts

The following scripts verify the MPLS underlay:

- Automated_Verification.py
- Verify_LDP.py
- Verify_Loopback_Reachability.py
- Final_Verification_Report.py

Verification includes:

- OSPF neighbor state
- MPLS LDP neighbor state
- End-to-end loopback reachability
- SSH connectivity
- Final PASS/FAIL reporting

## Verification Reports

Timestamped verification reports are stored in:

`verification_reports/`

## Python Environment

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate

'''
Install the required packages:

python -m pip install -r requirements.txt
Generate Configurations

Run:

python3 SP_Controller.py

Review the files inside generated_configs/ before pushing anything to the routers.

Run Final Verification

Run:

python3 Final_Verification_Report.py
Current Status

The MPLS underlay is operational.

The following checks passed:

OSPF adjacencies
MPLS LDP sessions
Loopback reachability
SSH connections
Router configuration saves

The individual MPLS-interface verification step was skipped by choice.

Security Note

Do not publish real usernames or passwords stored in Topology.yaml.

For a production-quality version, credentials should be stored in environment variables or a secure secrets manager.