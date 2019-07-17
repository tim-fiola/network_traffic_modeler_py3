"""
Client code to demonstrate how to use the pyNTM network_modeling classes.

Requires sample_network_model_file.csv to be in same directory.

"""

from pyNTM import Model
from pyNTM import Node

from graph_network import graph_network_interactive

from pprint import pprint
import time

t1 = time.time()

# Load a network Model file with info on nodes, interfaces, and demands
model1 = Model.load_model_file('sample_network_model_file.csv')
print('model1 is type', type(model1))
print()

# Define source and dest nodes for testing
source = 'A'
dest = 'B'

# Find all paths between source and destination nodes
print("Find the number of loop free, unique paths from Node A to Node B:")
good_paths = model1.get_feasible_paths(source, dest)
print("There are %i unique paths between %s and %s" % (len(good_paths),
                                                       source, dest))
print()

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
int_to_fail = model1.get_interface_object('A-to-B', 'A')
int_to_fail.fail_interface(model1)

# Calculate new traffic on interfaces and display
# the new traffic after the failure
print('Here is the traffic after the failure:')
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# Add a node to the model
print("Adding Node('Z') to model")
new_node = Node('Z')
model1.add_node(new_node)
new_node.lat = 40
new_node.lon = 50
print()

# Display all the nodes without interfaces
print("Here are the nodes without any interfaces:",
      model1.get_orphan_node_objects())
print()

# Add a circuit from new_node to node A
print("Add a circuit between Node('A') and Node('Z')")
model1.add_circuit(Node('A'), Node('Z'), 'a-to-z', 'z-to-a')
print()


# Add traffic to the model
shortest_paths_B_D = model1.get_shortest_path('B', 'D')
print('The shortest paths between nodes B and D are:')
for path in shortest_paths_B_D['path']:
    pprint(path)
    print()
print('These paths both have a cost of', shortest_paths_B_D['cost'])
print()
print('Adding 100 traffic from Node B to Node D:')
model1.add_demand('B', 'D', 100)
model1.update_simulation()
print('Here is the interface traffic after adding the traffic:')
print('Notice the difference in traffic - ')
print('Each path has 50 additional traffic: B-to-D and (B-to-E and E-to-D)')
model1.display_interfaces_traffic()
print()
print()


# Return an interface object
print("Get an interface object via interface name and node name:")
interface_object = model1.get_interface_object('A-to-B', 'A')
print('Interface(Node("A"), "A-to-B") = ', interface_object)
print()

# Find the circuit for the interface
print("The circuit for Interface(Node('A'), 'A-to-B') is")
ckt_object = interface_object.get_circuit_object(model1)
print(ckt_object)
print()

# Fail a node
print("Fail Node('D')")
model1.fail_node('D')
model1.update_simulation()
print()
print("Here is Node('D')'s failure status:",
      model1.get_node_object('D').failed)
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
model1.update_simulation()


print("Here is the interface traffic after Node('D') is restored:")
print(model1.display_interfaces_traffic())
print()

# Unfail the B-to-A interface and display traffic
print('Unfail the interface from Node B to Node A')
model1.unfail_interface('B-to-A', 'B', True)
model1.update_simulation()
model1.display_interfaces_traffic()
print()

# test get_circuit call from Interface object
int1 = model1.get_interface_object('A-to-B', 'A')
ckt1 = int1.get_circuit_object(model1)
print("The circuit associated with %s is %s" % (int1, ckt1))
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
print("Failing node E and interface B-to-D on node B and displaying "
       "a network graph:")
model1.fail_node('E')
model1.fail_interface('B-to-D', 'B')
model1.update_simulation()

# Get a demand and view its path
print("Get a demand and view its path.")
dmd_A_D = model1.get_demand_object('A', 'D', "''")
print("Demand from A to D is")
print(dmd_A_D)
print()
print("The path for dmd_A_D is:")
for hop in dmd_A_D.path:
    pprint(hop)
print()


t2 = time.time()
tot_time = t2 - t1
print('tot_time = ', tot_time)
print()

print("Making interactive network graph in browser.")
graph_network_interactive.make_interactive_network_graph(model1)
