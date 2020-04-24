import sys
sys.path.append('../')

import itertools
import networkx as nx


from pprint import pprint

from pyNTM import Parallel_Link_Model

# Make the Parallel_Link_Model
model = Parallel_Link_Model.load_model_file('multidigraph_topology.csv')
model.update_simulation()

G = nx.MultiDiGraph()

# node_list = model.node_objects
# for node in node_list:
#     for interface in node.interfaces:
#         if not interface._failed:
#             G.add_edge(node, interface.target, **interface._networkX(), data=interface)

# G = model._make_weighted_network_graph()

# edge_names = ((interface.node_object.name,
#                            interface.remote_node_object.name,
#                            {'cost': interface.cost, 'circuit_id': interface.circuit_id})
#                           for interface in model.interface_objects)

# edge_names = ((interface.node_object.name,
#                            interface.remote_node_object.name,
#                            data=interface)
#                           for interface in model.interface_objects)
#
# for node in model.node_objects:
#     for interface in node.interfaces(model):
#         G.add_edge(node, )

# for interface in model.interface_objects:
#     G.add_edge(interface.node_object.name, interface.remote_node_object.name, {'interface': [interface]})

edge_names = ((interface.node_object.name,
                           interface.remote_node_object.name,
                           {'key': interface._key, 'cost': interface.cost, 'interface': interface})
                           for interface in model.interface_objects)
G.add_edges_from(edge_names)

sp_a_b = list(nx.all_shortest_paths(G, 'A', 'D', weight='cost'))

demand = 100

# Add demand's load to interfaces it touches
num_paths = len(sp_a_b)
demand_load_per_path = demand / num_paths

# for path in sp_a_b:
#     current_hop = path[0]
#     for next_hop in path[1:]:
#         values_source_hop = G[current_hop][next_hop].values()
#         min_weight = min(d['cost'] for d in values_source_hop)
#         print('min_weight = {}'.format(min_weight))
#         ecmp_links = [k for k, d in G[current_hop][next_hop].items() if d['cost'] == min_weight]
#         num_ecmp_links = len(ecmp_links)
#         for link_index in ecmp_links:
#             G[current_hop][next_hop][link_index]['interface'].traffic += int(demand_load_per_path) / int(num_ecmp_links)
#         current_hop = next_hop

# Find the demand's path(s)
all_paths = []
for path in sp_a_b:
    current_hop = path[0]
    this_path = []
    for next_hop in path[1:]:
        this_hop = []
        values_source_hop = G[current_hop][next_hop].values()
        min_weight = min(d['cost'] for d in values_source_hop)
        print('min_weight = {}'.format(min_weight))
        ecmp_links = [k for k, d in G[current_hop][next_hop].items() if d['cost'] == min_weight]
        num_ecmp_links = len(ecmp_links)
        # Add Interface(s) to this_hop list and add traffic to Interfaces
        for link_index in ecmp_links:
            G[current_hop][next_hop][link_index]['interface'].traffic += int(demand_load_per_path) / int(num_ecmp_links)
            this_hop.append(G[current_hop][next_hop][link_index]['interface'])
        this_path.append(this_hop)
        current_hop = next_hop
    all_paths.append(this_path)

print("all_paths = ")
pprint(all_paths)
print()
print()

print("Interface traffic:")
for i in model.interface_objects:
    print([i, i.traffic])
print()
print()

path_list = Parallel_Link_Model._normalize_multidigraph_paths(model, all_paths)
print()
print("path_list:")
pprint(path_list)