import sys
sys.path.append('../')

from pprint import pprint

from pyNTM import Parallel_Link_Model

model8 = Parallel_Link_Model.load_model_file('multidigraph_topology_2.csv')


model8.update_simulation()

dmd_a_d_1 = model8.get_demand_object('A', 'D', 'dmd_a_d_1')

model8.display_interfaces_traffic()

model2 = Parallel_Link_Model.load_model_file('igp_routing_topology.csv')
model2.update_simulation()

model2.display_interfaces_traffic()
