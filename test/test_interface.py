import unittest

from pyNTM import Node
from pyNTM import Interface


class TestInterface(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, address=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, address=1)

    def test_repr(self):
        self.assertEqual(repr(self.interface_a), "Interface(name = 'inerfaceA-to-B', cost = 4, capacity = 100, node_object = Node('nodeA'), remote_node_object = Node('nodeB'), address = 1)")  # noqa E501

    def test_key(self):
        self.assertEqual(self.interface_a._key, ('inerfaceA-to-B', 'nodeA'))

    def test_eq(self):
        if self.interface_a == self.interface_a:
            self.assertTrue(True)

    def test_init_fail_neg_cost(self):
        with self.assertRaises(ValueError):
            Interface(name='inerfaceA-to-B', cost=-1, capacity=100,
                      node_object=self.node_a, remote_node_object=self.node_b, address=1)

    def test_init_fail_neg_capacity(self):
        with self.assertRaises(ValueError):
            Interface(name='inerfaceA-to-B', cost=4, capacity=-1,
                      node_object=self.node_a, remote_node_object=self.node_b, address=1)

    def test_reservable_bandwidth(self):
        self.assertEqual(100, self.interface_a.reservable_bandwidth)

    # TODO - test interface will be down when node fails

