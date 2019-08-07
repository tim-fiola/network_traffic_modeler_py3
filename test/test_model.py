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
        self.model.update_simulation()

    def test_demand_add(self):
        # node_a = Node(name='nodeA', lat=0, lon=0)
        # node_b = Node(name='nodeB', lat=0, lon=0)
        # interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
        #                              node_object=node_a, remote_node_object=node_b, address=1)
        # interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
        #                              node_object=node_b, remote_node_object=node_a, address=1)
        # model = Model(interface_objects=set([interface_a, interface_b]),
        #               node_objects=set([node_a, node_b]), demand_objects=set([]),
        #               rsvp_lsp_objects=set([]))
        # model.update_simulation()
        self.model.add_demand('nodeA', 'nodeB', 40, 'dmd_a_b')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 2, Nodes: 2, Demands: 1, RSVP_LSPs: 0)')

    def test_rsvp_lsp_add(self):
        # node_a = Node(name='nodeA', lat=0, lon=0)
        # node_b = Node(name='nodeB', lat=0, lon=0)
        # interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
        #                              node_object=node_a, remote_node_object=node_b, address=1)
        # interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
        #                              node_object=node_b, remote_node_object=node_a, address=1)
        # dmd_a_b = Demand(node_a, node_b, 40, 'dmd_a_b_1')
        # model = Model(interface_objects=set([interface_a, interface_b]),
        #               node_objects=set([node_a, node_b]), demand_objects=set([dmd_a_b]),
        #               rsvp_lsp_objects=set([]))
        # model.update_simulation()
        # model.add_demand('nodeA', 'nodeB', 40, 'dmd_a_b')
        # model.update_simulation()
        self.model.add_rsvp_lsp('nodeA', 'nodeB', 'lsp_a_b_1')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 2, Nodes: 2, Demands: 1, RSVP_LSPs: 1)')

    # TODO - test fail interface

    # TODO - test unfail interface when one of the Nodes is failed
