import unittest

from pyNTM import Node
from pyNTM import PerformanceModel
from pyNTM import Interface
from pyNTM import ModelException


class TestNode(unittest.TestCase):

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
                                      node_objects=set([self.node_a, self.node_b]),
                                      demand_objects=set([]), rsvp_lsp_objects=set([]))

    def test_eq(self):
        if self.node_a == self.node_a:
            self.assertTrue(True)

    def test_repr(self):
        self.assertEqual(repr(self.node_a), "Node('nodeA')")

    def test_key(self):
        self.assertEqual(self.node_a._key(), "nodeA")

    def test_lat_error(self):
        with self.assertRaises(ValueError):
            Node(name='nodeC', lat='twelve', lon=0)

    def test_lon_error(self):
        with self.assertRaises(ValueError):
            Node(name='nodeC', lat=0, lon='the number two')

    def test_lat_error_2(self):
        with self.assertRaises(ValueError):
            self.node_a.lat = 'twelve'

    def test_lon_error_2(self):
        with self.assertRaises(ValueError):
            self.node_a.lon = 'twelve'

    def test_set_failed(self):
        self.node_a.failed = True
        self.assertEqual(True, self.node_a.failed)

    def test_set_failed_error(self):
        with self.assertRaises(ModelException):
            self.node_a.failed = 100

    def test_interfaces(self):
        iface_list = self.node_a.interfaces(self.model)
        self.assertEqual([self.interface_a], iface_list)

    def test_adjacent_nodes(self):
        node_list = self.node_a.adjacent_nodes(self.model)
        self.assertEqual({self.node_b}, node_list)

    def test_fail_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_node('A')
        model.update_simulation()

        node_a = model.get_node_object('A')

        self.assertTrue(node_a.failed)
