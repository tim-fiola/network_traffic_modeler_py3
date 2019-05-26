import unittest

from pyNTM import Node
from pyNTM import Model
from pyNTM import Circuit
from pyNTM import Interface


class TestCircuit(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object='nodeA', remote_node_object='nodeB', address=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object='nodeB', remote_node_object='nodeA', address=1)
        self.model = Model(interface_objects=set([self.interface_a, self.interface_b]),
                           node_objects=set([node_a, node_b]), demand_objects=set([]), rsvp_lsp_objects=set([]))
        self.circuit = Circuit(self.interface_a, self.interface_b)

    def test_get_circuit_interfaces(self):
        (interface_a, interface_b) = self.circuit.get_circuit_interfaces(self.model)
        self.assertEqual(interface_a, self.interface_a)
        self.assertEqual(interface_b, self.interface_b)
