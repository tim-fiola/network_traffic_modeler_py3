import unittest

from network_modeling import Node
from network_modeling import Interface
from network_modeling import Model


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object='nodeA', remote_node_object='nodeB', address=1)
        interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object='nodeB', remote_node_object='nodeA', address=1)
        self.model = Model(interface_objects=set([interface_a, interface_b]),
                           node_objects=set([node_a, node_b]), demand_objects=set([]), rsvp_lsp_objects=set([]))
