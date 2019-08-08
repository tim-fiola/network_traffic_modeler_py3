import unittest

from pyNTM import Node
from pyNTM import Interface
from pyNTM import Model
from pyNTM import ModelException


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

    # def test_repr(self):
    #     self.assertEqual(repr(self.interface_a), "Interface(name = 'inerfaceA-to-B', cost = 4, capacity = 100, node_object = Node('nodeA'), remote_node_object = Node('nodeB'), address = 1)")  # noqa E501

    def test_bad_int_cost(self):
        with self.assertRaises(ModelException) as context:
            (Interface('test_int', -5, 40, self.node_a, self.node_b, 50))

            self.assertTrue('Interface cost cannot be less than 1' in context.exception)

    def test_key(self):
        self.assertEqual(self.interface_a._key, ('inerfaceA-to-B', 'nodeA'))

    def test_eq(self):
        if self.interface_a == self.interface_a:
            self.assertTrue(True)

    def test_init_fail_neg_cost(self):
        with self.assertRaises(ModelException):
            Interface(name='inerfaceA-to-B', cost=-1, capacity=100,
                      node_object=self.node_a, remote_node_object=self.node_b, address=1)

    def test_init_fail_neg_capacity(self):
        with self.assertRaises(ModelException):
            Interface(name='inerfaceA-to-B', cost=4, capacity=-1,
                      node_object=self.node_a, remote_node_object=self.node_b, address=1)

    def test_reservable_bandwidth(self):
        self.assertEqual(100, self.interface_a.reservable_bandwidth)

    def test_int_fail(self):  # TODO - don't use load model file here
        model = Model.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertFalse(int_a_b.failed)

        model.fail_interface('B-to-A', 'B')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)

    def test_int_fail_2(self):   # TODO - don't use load model file here
        model = Model.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')

        self.assertFalse(int_a_b.failed)
        self.assertFalse(int_b_a.failed)

        model.fail_node('A')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)
