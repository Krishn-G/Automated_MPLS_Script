##

#=====================================================================================

def Matrix(data):
    id_host_map = list(data['nodes'].keys())

    host_id_map = {name: id for id, name in enumerate(id_host_map)}

    n = len(host_id_map)
    matrix = [[None] * n for _ in range(n)]                                             # Empty Adjacency Matrix

    for node, intf in data['node_interfaces'].items():                                  #For rach node, i = Local Node, j = Remote Node
        i = host_id_map[node]

        for item in intf['intf']:
            for l_intf, r_node in item.items():
                j = host_id_map[r_node]

                if matrix[i][j] is None:
                    matrix[i][j] = [None, None]
                if matrix[j][i] is None:
                    matrix[j][i] = [None, None]

                matrix[i][j][0] = l_intf
                matrix[j][i][1] = l_intf

    for i in range(n):                                                                  #Converting to Tuples for Permanence
        for j in range(n):
            if matrix[i][j] != None:
                matrix[i][j] = tuple(matrix[i][j])

    return matrix, host_id_map, id_host_map

#=====================================================================================

if __name__ == '__main__':
    pass
