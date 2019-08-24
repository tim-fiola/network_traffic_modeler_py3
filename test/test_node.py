import unittest

from pyNTM import Node
from pyNTM import Model
from pyNTM import Interface
from pyNTM import ModelException


class TestNode(unittest.TestCase):

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
            Node(name='nodeC', lat=100, lon=0)

    def test_lon_error(self):
        with self.assertRaises(ValueError):
            Node(name='nodeC', lat=0, lon=200)

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
        model = Model.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_node('A')
        model.update_simulation()

        node_a = model.get_node_object('A')

        self.assertTrue(node_a.failed)

    # Test adding node to SRLG that does not exist in
    # model (create_if_not_present defaults to False)
    def test_add_node_to_new_srlg_dont_create(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        err_msg = "An SRLG with name new_srlg does not exist in the Model"

        with self.assertRaises(ModelException) as context:
            node_a.add_to_srlg('new_srlg', model)  # create_if_not_present defaults to False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test adding node to SRLG that does not exist in
    # model (create_if_not_present = True)
    def test_add_node_to_new_srlg_create(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)

        self.assertEqual(model.get_srlg_object('new_srlg').__repr__(), "SRLG(Name: new_srlg, Circuits: 0, Nodes: 1)")
        self.assertTrue(node_a in model.get_srlg_object('new_srlg').node_objects)

    # Test get_srlgs_with_self call
    def test_srlgs_with_self(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        self.assertEqual(node_a.get_srlgs_with_self(model), [new_srlg])

    # Test that a failed srlg brings a member node to failed = True
    def test_node_in_failed_srlg(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        self.assertFalse(node_a.failed)
        self.assertTrue(node_a in new_srlg.node_objects)

        model.fail_srlg('new_srlg')
        self.assertTrue(new_srlg.failed)
        model.update_simulation()

        self.assertTrue(node_a.failed)

    # Test that a Node in a failed SRLG will stay failed
    def test_node_in_failed_srlg_stays_failed(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        model.fail_srlg('new_srlg')
        model.update_simulation()
        self.assertTrue(new_srlg.failed)
        self.assertTrue(node_a.failed)

        err_msg = 'Node must be failed since it is a member of an SRLG that is failed'
        with self.assertRaises(ModelException) as context:
            node_a.failed = False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test that a Node in a non-failed SRLG can be unfailed
    def test_node_in_unfailed_srlg(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')
        node_a.failed = True
        model.update_simulation()
        self.assertFalse(new_srlg.failed)
        self.assertTrue(node_a.failed)

        # Now unfail node_a
        node_a.failed = False
        self.assertFalse(node_a.failed)

    # TODO - test node unfail when node is in SRLG that is not failed
    # TODO - test node unfail when node is in SRLG that is failed
    # TODO - test node.failed when node is in SRLG that is failed
    # TODO - test node uniqueness (node in model.srlg_objects.node_objects)
