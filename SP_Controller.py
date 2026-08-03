import yaml
import json
import Addressing
import Topology
import Configuration
import BGP_Setup
import Backup_Routers
import Save_All_Routers
import Push_Routers
import Verify_Loopback_Reachability

#=====================================================================================

def All_IPs(Raw_Router_IPs, id_host_map, data):
    Router_IPs = {}

    for r_id, intf in Raw_Router_IPs.items():
        host = id_host_map[r_id]
        Router_IPs[host] = intf

        loop_ip = data['nodes'][host]['loop_ip']
        Router_IPs[host]['Lo0'] = f"{loop_ip}/32"

    return Router_IPs
    
#=====================================================================================

if __name__ == '__main__':
    with open('Topology.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    
    matrix, host_id_map, id_host_map = Topology.Matrix(data)
    
    infra_subnet = data['global']['infra_subnet']
    Raw_Router_IPs = Addressing.Define_IPs(matrix, infra_subnet)

    Router_IPs = All_IPs(Raw_Router_IPs, id_host_map, data)
    
    # print(json.dumps(Router_IPs, indent=4))

    All_Configs = Configuration.Generate_All_Router_Configs(Router_IPs)
    Configuration.Save_All_Configs(All_Configs)

    asn = data['bgp']['asn']
    username = data['global']['auth']['user']
    password = data['global']['auth']['pass']
    BGP_Setup.BGP_Setup(asn, Router_IPs, username, password, data)

    Backup_Routers.Generate_Backups()

    Push_Routers.Push_Routers()
    Save_All_Routers.Save_All_Routers()

    Verify_Loopback_Reachability.Verify_Loopback_Reachability()
