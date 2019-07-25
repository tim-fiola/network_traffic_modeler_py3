import unittest

from pyNTM import Node
from pyNTM import Interface
from pyNTM import Model


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, address=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, address=1)
        self.model = Model(interface_objects=set([self.interface_a, self.interface_b]),
                           node_objects=set([self.node_a, self.node_b]), demand_objects=set([]),
                           rsvp_lsp_objects=set([]))


    # TODO - set model.add_rsvp_lsp call; it does not work
    # TODO - in fact, adding an LSP to any model that already has run update_simulation fails due to interface traffic utilization errors . .