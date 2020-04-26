import sys
sys.path.append('../')

from pyNTM import Node
from pyNTM import Demand
from pyNTM import Model
from pyNTM import Parallel_Link_Model
from pyNTM import Interface
from pyNTM import RSVP_LSP

node_a = Node(name='nodeA', lat=0, lon=0)
node_b = Node(name='nodeB', lat=0, lon=0)
node_d = Node(name='nodeD')
interface_a = Interface(name='interfaceA-to-B', cost=4, capacity=100,
                        node_object=node_a, remote_node_object=node_b, circuit_id=1)
interface_b = Interface(name='interfaceB-to-A', cost=4, capacity=100,
                        node_object=node_b, remote_node_object=node_a, circuit_id=1)
dmd_a_b = Demand(node_a, node_b, traffic=10)

lsp_a_b_1 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_1')
lsp_a_b_2 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_2')

model = Parallel_Link_Model(interface_objects=set([interface_a, interface_b]),
              node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_b]),
              rsvp_lsp_objects=set([lsp_a_b_1, lsp_a_b_2]))

model.update_simulation()

for lsp in model.rsvp_lsp_objects:
    print(lsp.traffic_on_lsp(model))
# self.assertEqual(str(dmd_a_b.path), "[RSVP_LSP(source = nodeA, dest = nodeB, lsp_name = 'lsp_a_b')]")
