import unittest

from pyNTM import Node
from pyNTM import PerformanceModel
from pyNTM import Circuit
from pyNTM import Interface


class TestCircuit(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, circuit_id=1)
        self.model = PerformanceModel(interface_objects=set([self.interface_a, self.interface_b]),
                                      node_objects=set([self.node_a, self.node_b]), demand_objects=set([]),
                                      rsvp_lsp_objects=set([]))
        self.circuit = Circuit(self.interface_a, self.interface_b)

    def test_repr(self):
        self.assertEqual(repr(self.circuit), "Circuit(Interface(name = 'inerfaceA-to-B', cost = 4, capacity = 100, node_object = Node('nodeA'), remote_node_object = Node('nodeB'), circuit_id = 1), Interface(name = 'inerfaceB-to-A', cost = 4, capacity = 100, node_object = Node('nodeB'), remote_node_object = Node('nodeA'), circuit_id = 1))")  # noqa E501

    def test_key(self):
        self.assertEqual(self.circuit._key(), (('inerfaceA-to-B', 'nodeA'), ('inerfaceB-to-A', 'nodeB')))

    def test_get_circuit_interfaces(self):
        (interface_a, interface_b) = self.circuit.get_circuit_interfaces(self.model)
        self.assertEqual(interface_a, self.interface_a)
        self.assertEqual(interface_b, self.interface_b)
