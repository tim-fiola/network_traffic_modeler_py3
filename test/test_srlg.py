import unittest

from pyNTM import PerformanceModel
from pyNTM import ModelException
from pyNTM import SRLG


class TestSRLG(unittest.TestCase):

    def test_repr(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        new_srlg = SRLG('new_srlg', model)

        self.assertEqual(new_srlg.__repr__(), 'SRLG(Name: new_srlg)')

    def test_failed_boolean(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()
        model.add_srlg('test_srlg')
        node_a.add_to_srlg('test_srlg', model)
        model.update_simulation()
        test_srlg = model.get_srlg_object('test_srlg')

        err_msg = 'must be boolean'
        with self.assertRaises(ModelException) as context:
            test_srlg.failed = 4
        self.assertTrue(err_msg in context.exception.args[0])

    def test_duplicate_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        SRLG('new_srlg', model)
        err_msg = 'SRLG with name new_srlg already exists in Model'
        with self.assertRaises(ModelException) as context:
            SRLG('new_srlg', model)
        self.assertTrue(err_msg in context.exception.args[0])

    def test_duplicate_srlg_2(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.add_srlg('new_srlg')
        err_msg = 'SRLG with name new_srlg already exists in Model'
        with self.assertRaises(ModelException) as context:
            model.add_srlg('new_srlg')
        self.assertTrue(err_msg in context.exception.args[0])

    # Test adding interface to SRLG that exists
    def test_add_interface_to_srlg(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        model.add_srlg('new_srlg')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model)
        model.update_simulation()

        srlg = model.get_srlg_object('new_srlg')

        self.assertIn(int_a_b, srlg.interface_objects)
        self.assertIn(int_b_a, srlg.interface_objects)
        self.assertIn(srlg, int_a_b.srlgs)
        self.assertIn(srlg, int_b_a.srlgs)

    # Test adding interface to SRLG that does not exist already
    def test_add_interface_to_srlg_2(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        int_a_b.add_to_srlg('new_srlg', model, create_if_not_present=True)
        model.update_simulation()

        srlg = model.get_srlg_object('new_srlg')

        self.assertIn(int_a_b, srlg.interface_objects)
        self.assertIn(int_b_a, srlg.interface_objects)
        self.assertIn(srlg, int_a_b.srlgs)
        self.assertIn(srlg, int_b_a.srlgs)

    # Test removing interface from SRLG
    def test_remove_interface_from_srlg(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        model.add_srlg('new_srlg')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model)
        model.update_simulation()

        srlg = model.get_srlg_object('new_srlg')

        self.assertIn(int_a_b, srlg.interface_objects)
        self.assertIn(int_b_a, srlg.interface_objects)
        self.assertIn(srlg, int_a_b.srlgs)
        self.assertIn(srlg, int_b_a.srlgs)

        int_b_a.remove_from_srlg('new_srlg', model)
        model.update_simulation()

        self.assertNotIn(int_a_b, srlg.interface_objects)
        self.assertNotIn(int_b_a, srlg.interface_objects)
        self.assertNotIn(srlg, int_a_b.srlgs)
        self.assertNotIn(srlg, int_b_a.srlgs)

    # Test removing interface from SRLG that does not exist throws error
    def test_remove_interface_from_bad_srlg(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        err_msg = "An SRLG with name bad_srlg does not exist in the Model"
        with self.assertRaises(ModelException) as context:
            int_b_a.remove_from_srlg('bad_srlg', model)
        self.assertTrue(err_msg in context.exception.args[0])

    # Test interface in failed SRLG is failed
    def test_interface_in_failed_srlg(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        model.add_srlg('new_srlg')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model)
        model.update_simulation()

        srlg = model.get_srlg_object('new_srlg')

        self.assertIn(int_a_b, srlg.interface_objects)
        self.assertIn(int_b_a, srlg.interface_objects)
        self.assertIn(srlg, int_a_b.srlgs)
        self.assertIn(srlg, int_b_a.srlgs)
        self.assertFalse(int_a_b.failed)
        self.assertFalse(int_b_a.failed)

        model.fail_srlg('new_srlg')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)

    def test_interface_in_failed_srlg_stays_failed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        model.fail_srlg('new_srlg')
        model.update_simulation()
        self.assertTrue(new_srlg.failed)
        self.assertTrue(int_a_b.failed)

        err_msg = 'Interface must be failed since it is a member of one or more SRLGs that are failed'
        with self.assertRaises(ModelException) as context:
            int_a_b.failed = False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test adding Interface to SRLG that does not exist in
    # model (create_if_not_present defaults to False)
    def test_add_interface_to_new_srlg_dont_create(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        int_a_b = model.get_interface_object('A-to-B', 'A')

        err_msg = "An SRLG with name new_srlg does not exist in the Model"

        with self.assertRaises(ModelException) as context:
            int_a_b.add_to_srlg('new_srlg', model)  # create_if_not_present defaults to False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test adding node to SRLG that does not exist in
    # model (create_if_not_present defaults to False)
    def test_add_node_to_new_srlg_dont_create(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        err_msg = "An SRLG with name new_srlg does not exist in the Model"

        with self.assertRaises(ModelException) as context:
            node_a.add_to_srlg('new_srlg', model)  # create_if_not_present defaults to False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test adding node to SRLG that does not exist in
    # model (create_if_not_present = True)
    def test_add_node_to_new_srlg_create(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        srlg = model.get_srlg_object('new_srlg')

        self.assertIn(node_a, model.get_srlg_object('new_srlg').node_objects)
        self.assertIn(srlg, node_a.srlgs)

    # Test that a failed srlg brings a member node to failed = True
    def test_node_in_failed_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
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
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        model.fail_srlg('new_srlg')
        model.update_simulation()
        self.assertTrue(new_srlg.failed)
        self.assertTrue(node_a.failed)

        err_msg = 'Node must be failed since it is a member of one or more SRLGs that are failed'
        with self.assertRaises(ModelException) as context:
            node_a.failed = False
        self.assertTrue(err_msg in context.exception.args[0])

    # Test that a Node in a non-failed SRLG can be unfailed
    def test_node_in_unfailed_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
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

    # Test that a node added to an SRLG is unique within Model's SRLG
    # node_objects
    def test_node_uniqueness_in_model_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        self.assertTrue(node_a in new_srlg.node_objects)

    # Test that a node added to an SRLG updates its srlgs' SRLG objects
    def test_srlg_uniqueness_in_node_srlgs(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        self.assertTrue(new_srlg in node_a.srlgs)

    # Test that a node can be removed from an SRLG
    def test_remove_node_from_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)

        self.assertTrue(node_a in model.get_srlg_object('new_srlg').node_objects)

        node_a.remove_from_srlg('new_srlg', model)

        model.update_simulation()

        self.assertNotIn(node_a, model.get_srlg_object('new_srlg').node_objects)

    # Test that removing a node from an srlg that does not exist throws error
    def test_remove_node_bad_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')

        err_msg = 'An SRLG with name bad_srlg does not exist in the Model'

        with self.assertRaises(ModelException) as context:
            node_a.remove_from_srlg('bad_srlg', model)
        self.assertTrue(err_msg in context.exception.args[0])

    # Test getting an SRLG that does not exist in Model raises exception
    def test_get_bad_srlg(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        err_msg = 'No SRLG with name bad_srlg exists in Model'
        with self.assertRaises(ModelException) as context:
            model.get_srlg_object('bad_srlg')
        self.assertTrue(err_msg in context.exception.args[0])

    # Test getting an SRLG that does not exist in Model does not raise exception
    def test_get_bad_srlg_no_exception(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        bad_srlg = model.get_srlg_object('bad_srlg', raise_exception=False)

        self.assertEqual(bad_srlg, None)

    # Test unfailing SRLG containing Interface in SRLG but
    # Interface's Node is still failed; Interface should stay failed
    def test_failed_int_node_srlg(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)
        node_a = model.get_node_object('A')

        model.add_srlg('new_srlg')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model)
        model.update_simulation()

        srlg = model.get_srlg_object('new_srlg')

        model.fail_node('A')
        model.fail_srlg('new_srlg')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)

        # Unfail the SRLG, int_a_b and int_b_a should stay failed
        model.unfail_srlg('new_srlg')
        model.update_simulation()

        self.assertFalse(srlg.failed)
        self.assertTrue(node_a.failed)
        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)

    # Test that a failed srlg unfails when removed from the SRLG
    def test_node_in_failed_srlg_unfails_when_removed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
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

        node_a.remove_from_srlg('new_srlg', model)
        model.update_simulation()

        self.assertNotIn(node_a, new_srlg.node_objects)

        self.assertFalse(node_a.failed)

    # Test that a node in a failed SRLG unfails when the SRLG unfails
    def test_node_unfails_when_srlg_unfails(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        model.fail_srlg('new_srlg')
        model.update_simulation()

        self.assertTrue(new_srlg.failed)
        self.assertTrue(node_a.failed)

        model.unfail_srlg('new_srlg')
        model.update_simulation()

        self.assertFalse(node_a.failed)

    # Test that a node in 2 failed SRLGs stays failed when one SRLG unfails
    def test_node_in_two_srlgs(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()

        node_a.add_to_srlg('new_srlg', model, create_if_not_present=True)
        node_a.add_to_srlg('new_srlg_2', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')
        new_srlg_2 = model.get_srlg_object('new_srlg_2')

        model.fail_srlg('new_srlg')
        model.fail_srlg('new_srlg_2')
        model.update_simulation()

        self.assertTrue(new_srlg.failed)
        self.assertTrue(new_srlg_2.failed)
        self.assertTrue(node_a.failed)

        model.unfail_srlg('new_srlg')
        model.update_simulation()

        # node_a should stay failed since it's part of another SRLG
        # that is still failed
        self.assertTrue(node_a.failed)

    # Test that an interface in 2 failed SRLGs stays failed when
    # one SRLG unfails
    def test_int_in_two_SRLGs(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        model.update_simulation()

        int_a_b.add_to_srlg('new_srlg', model, create_if_not_present=True)
        int_a_b.add_to_srlg('new_srlg_2', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')
        new_srlg_2 = model.get_srlg_object('new_srlg_2')

        model.fail_srlg('new_srlg')
        model.fail_srlg('new_srlg_2')
        model.update_simulation()

        self.assertTrue(new_srlg.failed)
        self.assertTrue(new_srlg_2.failed)
        self.assertTrue(int_a_b.failed)

        model.unfail_srlg('new_srlg')
        model.update_simulation()

        # node_a should stay failed since it's part of another SRLG
        # that is still failed
        self.assertTrue(int_a_b.failed)

    # Test that an interface in 1 failed SRLG stays failed when
    # SRLG unfails if its local node is also failed
    def test_int_in_SRLG_failed_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = int_a_b.get_remote_interface(model)

        int_a_b.add_to_srlg('new_srlg', model, create_if_not_present=True)
        int_a_b.add_to_srlg('new_srlg_2', model, create_if_not_present=True)
        new_srlg = model.get_srlg_object('new_srlg')

        model.fail_node('A')
        model.fail_srlg('new_srlg')
        model.update_simulation()

        self.assertTrue(new_srlg.failed)
        self.assertTrue(int_a_b.failed)

        model.unfail_srlg('new_srlg')
        model.update_simulation()

        # int_a_b and int_b_a should stay failed since Node('A') is also failed
        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)
