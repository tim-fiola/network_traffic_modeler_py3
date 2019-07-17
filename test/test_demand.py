import unittest

from pyNTM import Node
from pyNTM import Demand
from pyNTM import Model
from pyNTM import Interface
from pyNTM import RSVP_LSP


class TestDemand(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, address=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, address=1)
        self.rsvp_lsp_a = RSVP_LSP(source_node_object=self.node_a, dest_node_object=self.node_b, lsp_name='A-to-B')
        self.model = Model(interface_objects=set([self.interface_a, self.interface_b]),
                           node_objects=set([self.node_a, self.node_b]), demand_objects=set([]),
                           rsvp_lsp_objects=set([self.rsvp_lsp_a]))
        self.demand = Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=10, name='A-to-B')

    def test_init_fail_neg_traffic(self):
        with self.assertRaises(ValueError):
            Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=-1, name='A-to-B')

    def test_repr(self):
        self.assertEqual(repr(self.demand), "Demand(source = nodeA, dest = nodeB, traffic = 10, name = 'A-to-B')")

    def test_key(self):
        self.assertEqual(self.demand._key, (Node('nodeA'), Node('nodeB'), 'A-to-B'))

    def test_add_demand_path(self):
        self.demand._add_demand_path(self.model)
