import unittest

from pyNTM import Node
from pyNTM import PerformanceModel
from pyNTM import Interface
from pyNTM import ModelException


class TestNode(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """
        Set the class

        Args:
            self: (todo): write your description
        """
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
        """
        Test if the node is equal.

        Args:
            self: (todo): write your description
        """
        if self.node_a == self.node_a:
            self.assertTrue(True)

    def test_repr(self):
        """
        Evaluate a node.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(repr(self.node_a), "Node('nodeA')")

    def test_key(self):
        """
        Assigns the key.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(self.node_a._key(), "nodeA")

    def test_lat_error(self):
        """
        Set the error on error

        Args:
            self: (todo): write your description
        """
        with self.assertRaises(ValueError):
            Node(name='nodeC', lat='twelve', lon=0)

    def test_lon_error(self):
        """
        Set the error on the error

        Args:
            self: (todo): write your description
        """
        with self.assertRaises(ValueError):
            Node(name='nodeC', lat=0, lon='the number two')

    def test_lat_error_2(self):
        """
        Test if the error

        Args:
            self: (todo): write your description
        """
        with self.assertRaises(ValueError):
            self.node_a.lat = 'twelve'

    def test_lon_error_2(self):
        """
        Set the error between two node

        Args:
            self: (todo): write your description
        """
        with self.assertRaises(ValueError):
            self.node_a.lon = 'twelve'

    def test_set_failed(self):
        """
        Assigns failed.

        Args:
            self: (todo): write your description
        """
        self.node_a.failed = True
        self.assertEqual(True, self.node_a.failed)

    def test_set_failed_error(self):
        """
        Sets the error for the given test_error.

        Args:
            self: (todo): write your description
        """
        with self.assertRaises(ModelException):
            self.node_a.failed = 100

    def test_interfaces(self):
        """
        Test if the interfaces exist.

        Args:
            self: (todo): write your description
        """
        iface_list = self.node_a.interfaces(self.model)
        self.assertEqual([self.interface_a], iface_list)

    def test_adjacent_nodes(self):
        """
        Test if the adjacency nodes of the adjacency.

        Args:
            self: (todo): write your description
        """
        node_list = self.node_a.adjacent_nodes(self.model)
        self.assertEqual({self.node_b}, node_list)

    def test_fail_node(self):
        """
        Load the test node

        Args:
            self: (todo): write your description
        """
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_node('A')
        model.update_simulation()

        node_a = model.get_node_object('A')

        self.assertTrue(node_a.failed)
