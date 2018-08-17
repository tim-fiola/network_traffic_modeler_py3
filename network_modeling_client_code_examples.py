"""
Client code to demonstrate how to use the network_modeling classes
"""

from network_modeling import Model
from network_modeling import Circuit
from network_modeling import Demand
from network_modeling import graph_network
from network_modeling import Interface
from network_modeling import ModelException
from network_modeling import Node

from pprint import pprint
import time

t1 = time.time()

network_interfaces = [
    {'name':'A-to-B', 'cost':4,'capacity':100, 'node':'A',
     'remote_node': 'B', 'address': 1, 'failed': False},
    {'name':'A-to-C', 'cost':1,'capacity':200, 'node':'A',
     'remote_node': 'C', 'address': 3, 'failed': False},
    {'name':'A-to-D', 'cost':8,'capacity':150, 'node':'A',
     'remote_node': 'D', 'address': 4, 'failed': False},
    {'name':'B-to-A', 'cost':4,'capacity':100, 'node':'B',
     'remote_node': 'A', 'address': 1, 'failed': False},
    {'name':'B-to-D', 'cost':7,'capacity':200, 'node':'B',
     'remote_node': 'D', 'address': 5, 'failed': False},
    {'name':'B-to-E', 'cost':3,'capacity':200, 'node':'B',
     'remote_node': 'E', 'address': 8, 'failed': False},
    {'name':'D-to-B', 'cost':7,'capacity':200, 'node':'D',
     'remote_node': 'B', 'address': 5, 'failed': False},
    {'name':'D-to-C', 'cost':6,'capacity':150, 'node':'D',
     'remote_node': 'C', 'address': 6, 'failed': False},
    {'name':'D-to-A', 'cost':8,'capacity':150, 'node':'D',
     'remote_node': 'A', 'address': 4, 'failed': False},
    {'name':'D-to-E', 'cost':4,'capacity':100, 'node':'D',
     'remote_node': 'E', 'address': 9, 'failed': False},
    {'name':'D-to-F', 'cost':3,'capacity':100, 'node':'D',
     'remote_node': 'F', 'address': 10, 'failed': False},
    {'name':'C-to-A', 'cost':1,'capacity':200, 'node':'C',
     'remote_node': 'A', 'address': 3, 'failed': False},
    {'name':'C-to-D', 'cost':6,'capacity':150, 'node':'C',
     'remote_node': 'D', 'address': 6, 'failed': False},
    {'name':'E-to-B', 'cost':3,'capacity':200, 'node':'E',
     'remote_node': 'B', 'address': 8, 'failed': False},
    {'name':'E-to-D', 'cost':4,'capacity':100, 'node':'E',
     'remote_node': 'D', 'address': 9, 'failed': False},
    {'name':'F-to-D', 'cost':3,'capacity':100, 'node':'F',
     'remote_node': 'D', 'address': 10, 'failed': False},
]


network_interfaces_w_errors = [
    {'name':'A-to-B', 'cost':4.1,'capacity':100, 'node':'A',
     'remote_node': 'B', 'address': 1, 'failed': 'moo'}, # bad 'failed', non int metric
    {'name':'A-to-Bv2', 'cost':50,'capacity':150, 'node':'A',
     'remote_node': 'B', 'address': 2, 'failed': False},
    {'name':'A-to-C', 'cost':1,'capacity':'100', 'node':'A', # invalid capacity
     'remote_node': 'C', 'address': 3, 'failed': False},
    {'name':'A-to-D', 'cost':8,'capacity':150, 'node':'A',
     'remote_node': 'D', 'address': 4, 'failed': False},
    {'name':'B-to-A', 'cost':4,'capacity':100, 'node':'B',
     'remote_node': 'A', 'address': 1, 'failed': False},
    {'name':'B-to-Av2', 'cost':40,'capacity':150, 'node':'B',
     'remote_node': 'A', 'address': 2, 'failed': False},    
    {'name':'B-to-D', 'cost':7,'capacity':200, 'node':'B',
     'remote_node': 'D', 'address': 5, 'failed': False},
    {'name':'B-to-E', 'cost':3,'capacity':200, 'node':'B',
     'remote_node': 'E', 'address': 8, 'failed': False},
    {'name':'D-to-B', 'cost':7,'capacity':200, 'node':'D',
     'remote_node': 'B', 'address': 5, 'failed': False},
    {'name':'D-to-C', 'cost':6,'capacity':150, 'node':'D',
     'remote_node': 'C', 'address': 6, 'failed': False},
    {'name':'D-to-C_v2', 'cost':6,'capacity':200, 'node':'D',
     'remote_node': 'C', 'address': 11, 'failed': False},
    {'name':'D-to-A', 'cost':8,'capacity':150, 'node':'D',
     'remote_node': 'A', 'address': 4, 'failed': False},
    {'name':'D-to-E', 'cost':4,'capacity':100, 'node':'D',
     'remote_node': 'E', 'address': 9, 'failed': False},
    {'name':'D-to-F', 'cost':3,'capacity':100, 'node':'D',
     'remote_node': 'F', 'address': 10, 'failed': False},
    {'name':'C-to-A', 'cost':1,'capacity':200, 'node':'C',
     'remote_node': 'A', 'address': 3, 'failed': False},
    {'name':'C-to-D', 'cost':6,'capacity':150, 'node':'C',
     'remote_node': 'D', 'address': 6, 'failed': False},
    {'name':'C-to-D_v2', 'cost':6,'capacity':200, 'node':'C',
     'remote_node': 'D', 'address': 11, 'failed': False},
    {'name':'E-to-B', 'cost':3,'capacity':200, 'node':'E',
     'remote_node': 'B', 'address': 8, 'failed': False},
    {'name':'E-to-D', 'cost':4,'capacity':100, 'node':'E',
     'remote_node': 'D', 'address': 9, 'failed': False},
    {'name':'F-to-D', 'cost':3,'capacity':100, 'node':'F', # non unique int
     'remote_node': 'D', 'address': 10, 'failed': False},
    {'name':'F-to-D', 'cost':3,'capacity':120, 'node':'F', # non unique int
     'remote_node': 'D', 'address': 10, 'failed': False},
    {'name':'Z-to-D', 'cost':3,'capacity':100, 'node':'Z',
     'remote_node': 'D', 'address': 10, 'failed': False},# no remote interface   
]


demands = [ {'source': 'A', 'dest': 'B', 'traffic': 50},
            {'source': 'A', 'dest': 'F', 'traffic': 22},
            {'source': 'A', 'dest': 'E', 'traffic': 24},
            {'source': 'F', 'dest': 'E', 'traffic': 80},
            {'source': 'F', 'dest': 'B', 'traffic': 50},
            {'source': 'A', 'dest': 'D', 'traffic': 120}
    ]


source = 'A'
dest = 'B'

# Define a network model and load interfaces 
model1 = Model()
model1.add_network_interfaces_from_list(network_interfaces)
print('model1 is type', type(model1))
print()

# Assign lat/lon info to nodes
print('Assigning lat/lon info to nodes')
lat_lon_info = [(180, 20), (30, 40), (120, 50), (35, 67), (77, 88), (45, 56)]
node_names = [node.name for node in model1.node_objects]
counter = 0
for name in node_names:
    node = model1.get_node_object(name)
    lat, lon = lat_lon_info[counter]
    node.lat = lat
    node.lon = lon
    counter = counter + 1
print()

# Find all paths between source and destination nodes

print("Find all paths from Node A to Node B:")
good_paths = model1.get_feasible_paths(source, dest)
print("There are %i unique paths between %s and %s"%(len(good_paths),
                                                     source, dest))
print()

# create demand objects from list of demands
##demand_objects = Demand.create_demand_objects(demands)
for demand in demands:
    model1.add_demand(demand['source'], demand['dest'],
                      demand['traffic'])

# find the best path from node A to B
best_A_B = model1.get_shortest_path(source, dest)
print("The best path from Node A to Node B is:", best_A_B)
print()

# display the traffic
print('Interface traffic with no failures:')
model1.update_simulation()
model1.display_interfaces_traffic()
print()
print()

# Find the remote interface for Node F, interface F-to-D
print("Find the remote interface for Node F, interface F-to-D:")
f_to_d = model1.get_interface_object('F-to-D', 'F')
remote_int = f_to_d.get_remote_interface(model1)
print("Remote interface is", remote_int)
print()

# Fail interface on node A, interface A-to-B
print('Failing interface A-to-B on node A')
int_to_fail = model1.get_interface_object('A-to-B','A')
int_to_fail.fail_interface(model1)

# Calculate new traffic on interfaces and display
# the new traffic after the failure
print('Here is the traffic after the failure:')
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# Add a node to the model
print("Adding Node('G') to model")
new_node = Node('G')
model1.add_node(new_node)
print()

# Display all the nodes without interfaces
print("Here are the nodes without any interfaces:", \
      model1.get_orphan_node_objects())
print()

# Add a circuit from new_node to node A
print("Add a circuit between Node('A') and Node('G')")
model1.add_circuit(Node('A'), Node('G'), 'a-to-g', 'g-to-a')
print()

# Add traffic to the model
print('Adding 100 traffic from Node B to Node D:')
model1.add_demand('B', 'D', 100)
model1.update_simulation()
print('Here is the interface traffic after adding the traffic:')
model1.display_interfaces_traffic()
print()

# Return an interface object
print("Get an interface object via interface name and node name:")
interface_object = model1.get_interface_object('A-to-B', 'A')
print('Interface(Node("A"), "A-to-B") = ', interface_object)
print()

# Find the circuit for the interface
print("The circuit for Interface(Node('A'), 'A-to-B') is")
ckt_object = interface_object.get_circuit(model1)
print(ckt_object)
print()

# Fail a node
print("Fail Node('D')")
model1.fail_node('D')
model1.update_simulation()
print()
print("Here is Node('D')'s failure status:", model1.get_node_object('D').failed)
print()

# Get Node('D')'s interfaces
print("Here are Node('D')'s interfaces:")
pprint(model1.get_node_interfaces('D'))
model1.update_simulation()
print()
print("Here is the network traffic after Node('D') failed:")
print(model1.display_interfaces_traffic())
print()

# Get unrouted demands
print("Here are the unrouted demands:")
for demand in model1.get_unrouted_demand_objects():
    pprint(demand)
print()

# Unfail Node('D')
print("Now unfail Node('D')")
model1.unfail_node('D')
print()

# Get Node('D')'s interfaces
print("Here are Node('D')'s interfaces:")
pprint(model1.get_node_interfaces('D'))
print()

model1.update_simulation()

print("Here is the interface traffic after Node('D') is restored:")
print(model1.display_interfaces_traffic())
print()

# Unfail the B-to-A interface and display traffic
print('Unfail the interface from Node B to Node A')
model1.unfail_interface('B-to-A', 'B', True )
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# Fail Nodes 'A' and 'G' and display traffic
print('Fail Nodes A and G and display the interface traffic:')
model1.fail_node('G')
model1.fail_node('A')
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# Unfail Node('G') and display traffic
print('Unfail Node("G") and display traffic:')
model1.unfail_node('G')
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# Unfail Node('A') and display traffic
print("Unfail Node('A') and display traffic:")
model1.unfail_node('A')
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# test get_circuit call from Interface object
int1 = model1.get_interface_object('A-to-B', 'A')
ckt1 = int1.get_circuit(model1)
print("The circuit associated with %s is %s"%(int1, ckt1))
print()

# test a demand path before and after an interface it traverses fails;
# should go from 2 paths to one path
dmd_B_D = model1.get_demand_object('B', 'D')
print("dmd_B_D path before failing interface B-to-D is")
for path in dmd_B_D.path:
    pprint(path)
    print()
print()
model1.fail_interface('B-to-D', 'B')
model1.update_simulation()
print("dmd_B_D path after failing interface B-to-D is")
pprint(dmd_B_D.path)
print()


# Fail a node and interface and display a utilization graph
print("Failing node E and interface B-to-D on node B and displaying \
a network graph:")
model1.fail_node('E')
model1.fail_interface('B-to-D', 'B')
model1.update_simulation()

# Get a demand and view its path
print("Get a demand and view its path.")
dmd_A_D = model1.get_demand_object('A', 'D')
print("Demand from A to D is")
print(dmd_A_D)
print()
print("The path for dmd_A_D is:")
for hop in dmd_A_D.path:
    pprint(hop)
print()



t2 = time.time()
tot_time = t2-t1
print('tot_time = ', tot_time)

graph_network.make_utilization_graph_neat(model1, 
                                        'node_e_and_link_B-to-D_failed',
                                          display_plot=True)





