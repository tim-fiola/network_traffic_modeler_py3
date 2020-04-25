import sys
sys.path.append('../')

import networkx as nx


from pprint import pprint

from pyNTM import Parallel_Link_Model


def route_demands(model):

    edge_names = ((interface.node_object.name,
                   interface.remote_node_object.name,
                   {'cost': interface.cost, 'interface': interface})
                  for interface in model.interface_objects)

    G = nx.MultiDiGraph()

    G.add_edges_from(edge_names)

    for demand in model.demand_objects:
        src = demand.source_node_object.name
        dest = demand.dest_node_object.name

        # Shortest path in networkx multidigraph
        nx_sp = list(nx.all_shortest_paths(G,  src, dest, weight='cost'))

        # Find demand's load to interfaces it touches
        num_paths = len(nx_sp)
        demand_load_per_path = demand.traffic / num_paths

        # all_paths is list of paths from source to destination; these paths
        # may include paths that have multiple links between nodes
        all_paths = []

        for path in nx_sp:
            current_hop = path[0]
            this_path = []
            for next_hop in path[1:]:
                this_hop = []
                values_source_hop = G[current_hop][next_hop].values()
                min_weight = min(d['cost'] for d in values_source_hop)
                print('min_weight = {}'.format(min_weight))
                ecmp_links = [interface_index for interface_index, interface_item in G[current_hop][next_hop].items() if
                              interface_item['cost'] == min_weight]
                num_ecmp_links = len(ecmp_links)
                # Add Interface(s) to this_hop list and add traffic to Interfaces
                # import pdb
                # pdb.set_trace()
                for link_index in ecmp_links:
                    G[current_hop][next_hop][link_index]['interface'].traffic += int(demand_load_per_path) / int(
                        num_ecmp_links)
                    this_hop.append(G[current_hop][next_hop][link_index]['interface'])
                this_path.append(this_hop)
                current_hop = next_hop
            all_paths.append(this_path)

        print("all_paths = ")
        pprint(all_paths)
        print()
        print()

        path_list = Parallel_Link_Model._normalize_multidigraph_paths(model, all_paths)
        demand.path = path_list

        print("Interface traffic:")
        for i in model.interface_objects:
            print([i, i.traffic])
        print()
        print()

        print()
        print("path_list:")
        pprint(path_list)

    return model


# Make the Parallel_Link_Model
model = Parallel_Link_Model.load_model_file('multidigraph_topology.csv')
model.update_simulation()

# for interface in model.interface_objects:
#     interface.traffic = 0
#
# for demand in model.demand_objects:
#     demand.path = []

# G = nx.MultiDiGraph()

# edge_names = ((interface.node_object.name,
#                            interface.remote_node_object.name,
#                            {'cost': interface.cost, 'interface': interface})
#                            for interface in model.interface_objects)
# G.add_edges_from(edge_names)


# nx_sp = list(nx.all_shortest_paths(G, 'A', 'D', weight='cost'))

# demand = 100
#
# # Add demand's load to interfaces it touches
# num_paths = len(nx_sp)
# demand_load_per_path = demand / num_paths
#
# # Find the demand's path(s)
# all_paths = []
# for path in nx_sp:
#     current_hop = path[0]
#     this_path = []
#     for next_hop in path[1:]:
#         this_hop = []
#         values_source_hop = G[current_hop][next_hop].values()
#         min_weight = min(d['cost'] for d in values_source_hop)
#         print('min_weight = {}'.format(min_weight))
#         ecmp_links = [interface_index for interface_index, interface_item in G[current_hop][next_hop].items() if
#                       interface_item['cost'] == min_weight]
#         num_ecmp_links = len(ecmp_links)
#         # Add Interface(s) to this_hop list and add traffic to Interfaces
#         for link_index in ecmp_links:
#             G[current_hop][next_hop][link_index]['interface'].traffic += int(demand_load_per_path) / int(num_ecmp_links)
#             this_hop.append(G[current_hop][next_hop][link_index]['interface'])
#         this_path.append(this_hop)
#         current_hop = next_hop
#     all_paths.append(this_path)
#
# print("all_paths = ")
# pprint(all_paths)
# print()
# print()
#
# print("Interface traffic:")
# for i in model.interface_objects:
#     print([i, i.traffic])
# print()
# print()
#
# path_list = Parallel_Link_Model._normalize_multidigraph_paths(model, all_paths)
# print()
# print("path_list:")
# pprint(path_list)

# model = route_demands(model)

model.display_interfaces_traffic()
