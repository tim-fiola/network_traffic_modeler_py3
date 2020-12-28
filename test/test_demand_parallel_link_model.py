"""
Confirming behavior of Demand in Parallel_Link_Model
"""

import unittest

from pyNTM import Node
from pyNTM import Demand
from pyNTM import FlexModel
from pyNTM import Interface
from pyNTM import RSVP_LSP


class TestDemand(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, circuit_id=1)
        self.rsvp_lsp_a = RSVP_LSP(source_node_object=self.node_a, dest_node_object=self.node_b, lsp_name='A-to-B')
        self.model = FlexModel(interface_objects=set([self.interface_a, self.interface_b]),
                               node_objects=set([self.node_a, self.node_b]), demand_objects=set([]),
                               rsvp_lsp_objects=set([self.rsvp_lsp_a]))
        self.demand = Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=10, name='A-to-B')

    def test_init_fail_neg_traffic(self):
        with self.assertRaises(ValueError):
            Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=-1, name='A-to-B')

    def test_repr(self):
        self.assertEqual(repr(self.demand), "Demand(source = nodeA, dest = nodeB, traffic = 10, name = 'A-to-B')")

    def test_key(self):
        self.assertEqual(self.demand._key, (Node('nodeA').name, Node('nodeB').name, 'A-to-B'))

    def test_demand_behavior(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology.csv')

        model.update_simulation()

        dmd_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')
        # int_a_b = model.get_interface_object('A-to-B', 'A')
        # int_b_d = model.get_interface_object('B-to-D', 'B')
        # int_b_g = model.get_interface_object('B-to-G', 'B')
        # int_g_d = model.get_interface_object('G-to-D', 'G')
        # int_d_f = model.get_interface_object('D-to-F', 'D')
        # int_a_c = model.get_interface_object('A-to-C', 'A')
        # int_c_d = model.get_interface_object('C-to-D', 'C')
        # int_a_d = model.get_interface_object('A-to-D', 'A')

        # Demand routes initially
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

        # Demand should not route if source node is down
        model.fail_node('A')
        model.update_simulation()
        self.assertEqual(dmd_a_f.path, 'Unrouted')

        # Demand should route when source node unfails
        model.unfail_node('A')
        model.update_simulation()
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

        # Demand should not route when dest node fails
        model.fail_node('F')
        model.update_simulation()
        self.assertEqual(dmd_a_f.path, 'Unrouted')

        # Demand should route when dest node unfails
        model.unfail_node('F')
        model.update_simulation()
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

    def test_unroutable_demand(self):
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        node_d = Node(name='nodeD')
        interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=node_a, remote_node_object=node_b, circuit_id=1)
        interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=node_b, remote_node_object=node_a, circuit_id=1)
        dmd_a_d = Demand(node_a, node_d, traffic=10)
        model = FlexModel(interface_objects=set([interface_a, interface_b]),
                          node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_d]),
                          rsvp_lsp_objects=set([]))
        model.update_simulation()

        self.assertEqual(dmd_a_d.path, 'Unrouted')

    def test_demand_on_lsp(self):
        """
        Ensure the demand takes an available LSP
        :return:
        """
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        node_d = Node(name='nodeD')
        interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                node_object=node_a, remote_node_object=node_b, circuit_id=1)
        interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                node_object=node_b, remote_node_object=node_a, circuit_id=1)
        dmd_a_b = Demand(node_a, node_b, traffic=10)

        lsp_a_b = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b')

        model = FlexModel(interface_objects=set([interface_a, interface_b]),
                          node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_b]),
                          rsvp_lsp_objects=set([lsp_a_b]))

        model.update_simulation()

        self.assertEqual(str(dmd_a_b.path), "[[RSVP_LSP(source = nodeA, dest = nodeB, lsp_name = 'lsp_a_b')]]")
