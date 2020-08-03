import unittest

from pyNTM import Circuit
from pyNTM import Interface
from pyNTM import PerformanceModel
from pyNTM import Model
from pyNTM import ModelException
from pyNTM import Node


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = PerformanceModel.load_model_file('test/model_test_topology.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.dmd_a_d_1 = self.model.get_demand_object('A', 'D', 'dmd_a_d_1')
        self.dmd_a_d_2 = self.model.get_demand_object('A', 'D', 'dmd_a_d_2')
        self.dmd_a_f_1 = self.model.get_demand_object('A', 'F', 'dmd_a_f_1')
        self.model.update_simulation()

    def test_lat_lon(self):
        node_g = self.model.get_node_object('G')
        self.assertEqual(node_g.lat, 35)
        self.assertEqual(node_g.lon, 30)

    def test_demand_add(self):
        self.model.add_demand('A', 'B', 40, 'dmd_a_b')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'PerformanceModel(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 3)')

    def test_rsvp_lsp_add(self):
        self.model.add_rsvp_lsp('A', 'B', 'lsp_a_b_1')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'PerformanceModel(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 4)')

    def test_node_source_demands(self):
        dmd_a_b = self.model.get_demand_object('A', 'B', 'dmd_a_b')
        self.assertTrue(dmd_a_b in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_d_1 in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_d_2 in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_f_1 in self.model.get_demand_objects_source_node('A'))

    def test_node_dest_demands(self):
        dmd_a_b = self.model.get_demand_object('A', 'B', 'dmd_a_b')
        self.assertEqual(self.model.get_demand_objects_dest_node('B'), [dmd_a_b])

    # No interfaces are failed
    def test_get_failed_ints_1(self):
        self.assertEqual(self.model.get_failed_interface_objects(), [])

    def test_get_unfailed_ints(self):
        self.assertTrue(len(self.model.get_unfailed_interface_objects()), 18)

    # Fail interface; 2 interfaces should be down
    def test_get_failed_ints_2(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')
        failed_int_list = model.get_failed_interface_objects()
        self.assertEqual(set(failed_int_list), set([int_a_b, int_b_a]))

    def test_get_unfailed_ints_2(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()
        self.assertEqual(len(model.get_unfailed_interface_objects()), 16)

    def test_unfail_interface(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        model.update_simulation()
        self.assertTrue(int_a_b.failed)
        model.unfail_interface('A-to-B', 'A')
        model.update_simulation()
        self.assertFalse(int_a_b.failed)

    # When Node A fails, all of its Interfaces and adjacent Interfaces
    # should also fail
    def test_fail_node(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertTrue(model.get_node_object('A').failed)

    def test_failed_node_interfaces(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertEqual(len(model.get_failed_interface_objects()), 8)

    # When a Node is failed, all of its Interfaces must stay failed
    # until the Node is unfailed
    def test_int_stays_down(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertTrue(model.get_node_object('A').failed)
        model.unfail_interface('A-to-B', 'A')
        self.assertTrue(int_a_b.failed)
        model.unfail_interface('B-to-A', 'B')
        model.update_simulation()
        self.assertTrue(int_b_a.failed)

    def test_int_comes_up(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertTrue(model.get_node_object('A').failed)
        model.unfail_interface('A-to-B', 'A')
        self.assertTrue(int_a_b.failed)
        model.unfail_interface('B-to-A', 'B')
        model.update_simulation()
        self.assertTrue(int_b_a.failed)
        model.unfail_node('A')
        model.update_simulation()
        self.assertFalse(model.get_node_object('A').failed)
        self.assertFalse(model.get_node_object('B').failed)

    # Find all simple paths less than 2 hops from A to D; no required
    # bandwidth needed
    def test_all_paths_cutoff(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        all_paths = model.get_all_paths_reservable_bw('A', 'D', False, 2, 0)
        self.assertEqual(len(all_paths['path']), 3)
        path_lengths = [len(path) for path in all_paths['path']]
        path_lengths.sort()
        self.assertEqual(path_lengths, [1, 2, 2])

    # Find all simple paths from A to D with at least 10 unit of
    # reservable bandwidth
    def test_all_paths_needed_bw(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        all_paths = model.get_all_paths_reservable_bw('A', 'D', False, 10)
        self.assertEqual(len(all_paths['path']), 4)
        path_lengths = [len(path) for path in all_paths['path']]
        path_lengths.sort()
        self.assertEqual(path_lengths, [1, 2, 2, 3])

    def test_get_failed_nodes(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_node('A')
        model.fail_node('G')
        model.update_simulation()

        node_a = model.get_node_object('A')
        node_g = model.get_node_object('G')

        self.assertEqual(set(model.get_failed_node_objects()), set([node_a, node_g]))

    def test_get_non_failed_nodes(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_node('A')
        model.fail_node('G')
        model.update_simulation()

        node_b = model.get_node_object('B')
        node_c = model.get_node_object('C')
        node_d = model.get_node_object('D')
        node_e = model.get_node_object('E')
        node_f = model.get_node_object('F')

        unfailed_node_list = [node_b, node_c, node_d, node_e, node_f]

        self.assertEqual(set(model.get_non_failed_node_objects()), set(unfailed_node_list))

    def test_interface_fields_missing_model_file_load(self):
        err_msg = 'node_name, remote_node_name, name, cost, and capacity must be defined for line'
        with self.assertRaises(ModelException) as context:
            PerformanceModel.load_model_file('test/interface_field_info_missing_routing_topology.csv')
        self.assertTrue(err_msg in err_msg in context.exception.args[0])

    def test_ckt_mismatch_int_capacity_file_load(self):
        err_msg = 'circuits_with_mismatched_interface_capacity'
        model = PerformanceModel.load_model_file('test/mismatched_ckt_int_capacity_topology_file.csv')
        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertTrue(err_msg in context.exception.args[0][1][0].keys())

    def test_get_bad_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        err_msg = 'No node with name ZZ exists in the model'

        with self.assertRaises(ModelException) as context:
            model.get_node_object('ZZ')
        self.assertTrue(err_msg in context.exception.args[0])

    def test_add_duplicate_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_a = Node('A')

        err_msg = 'A node with name A already exists in the model'

        with self.assertRaises(ModelException) as context:
            model.add_node(node_a)
        self.assertTrue(err_msg in context.exception.args[0])

    def test_add_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_z = Node('Z')

        model.add_node(node_z)
        model.update_simulation()

        self.assertIn(node_z, model.node_objects)

    def test_get_bad_interface(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        with self.assertRaises(ModelException) as context:
            model.get_interface_object('A-to-Z', 'A')
        self.assertTrue('specified interface does not exist' in context.exception.args[0])

    def test_bad_ckt(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        with self.assertRaises(ModelException) as context:
            model.get_circuit_object_from_interface('A-to-Z', 'A')
        self.assertTrue('specified interface does not exist' in context.exception.args[0])

    def test_get_ckt(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        ckt = model.get_circuit_object_from_interface('A-to-B', 'A')

        self.assertIn(ckt, model.circuit_objects)

    def test_get_unrouted_dmds(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        model.fail_node('D')
        model.update_simulation()
        dmd_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')

        self.assertTrue(dmd_a_f, model.get_unrouted_demand_objects())

    def test_get_bad_dmd(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        with self.assertRaises(ModelException) as context:
            model.get_demand_object('F', 'A', 'bad_demand')
        self.assertIn('no matching demand', context.exception.args[0])

    def test_get_bad_lsp(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        err_msg = "LSP with source node A, dest node B, and name bad_lsp does not exist in model"

        with self.assertRaises(ModelException) as context:
            model.get_rsvp_lsp('A', 'B', 'bad_lsp')
        self.assertIn(err_msg, context.exception.args[0])

    def test_add_duplicate_lsp(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()

        err_msg = 'already exists in rsvp_lsp_objects'

        with self.assertRaises(ModelException) as context:
            model.add_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.assertIn(err_msg, context.exception.args[0])

    def test_node_orphan(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        zz = Node('ZZ')
        model.add_node(zz)
        model.update_simulation()
        node_a = model.get_node_object('A')

        self.assertTrue(model.is_node_an_orphan(zz))
        self.assertFalse(model.is_node_an_orphan(node_a))

    def test_ckt_add(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_zz = Node('ZZ')
        model.add_node(node_zz)
        model.update_simulation()

        node_a = model.get_node_object('A')

        model.add_circuit(node_a, node_zz, 'A-to-ZZ', 'ZZ-to-A', 20, 20, 1000)
        model.update_simulation()

        ckt = model.get_circuit_object_from_interface('ZZ-to-A', 'ZZ')

        self.assertTrue(isinstance(ckt, Circuit))

    def test_add_duplicate_int(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_a = model.get_node_object('A')
        node_b = model.get_node_object('B')
        duplicate_int = Interface('A-to-B', 100, 125, node_a, node_b, 80)
        model.interface_objects.add(duplicate_int)

        err_msg = 'multiple links between nodes detected; not allowed in Model object(use Parallel_Link_Model)'

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0][1][0].keys())

    def test_int_not_in_ckt(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_f = model.get_node_object('F')
        node_b = model.get_node_object('B')
        new_int = Interface('F-to-B', 100, 100, node_f, node_b, 80)
        model.interface_objects.add(new_int)

        err_msg = "WARNING: These interfaces were not matched into a circuit [('F', 'B', {"

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0])

    def test_int_name_change(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        interface = model.get_interface_object('A-to-B', 'A')

        model.change_interface_name('A', 'A-to-B', 'A-to-B-changed')

        self.assertEqual(interface.name, 'A-to-B-changed')

    def test_duplicate_int_near_side(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_a_2 = Node('A')
        node_b_2 = Node('B')
        err_msg = 'already exists in model'

        with self.assertRaises(ModelException) as context:
            model.add_circuit(node_a_2, node_b_2, 'A-to-B', 'B-to-A', 40, 40, 100)
        self.assertIn(err_msg, context.exception.args[0])

    def test_duplicate_int_remote_side(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        node_d_2 = Node('D')
        node_b_2 = Node('B')
        err_msg = 'already exists in model'

        with self.assertRaises(ModelException) as context:
            model.add_circuit(node_d_2, node_b_2, 'D-to-B', 'B-to-A', 40, 40, 100)
        self.assertIn(err_msg, context.exception.args[0])

    def test_for_bad_node_in_demand_data(self):

        err_msg = "No Node with name Y in Model"

        with self.assertRaises(ModelException) as context:
            PerformanceModel.load_model_file('test/model_bad_node_in_demand.csv')
        self.assertIn(err_msg, context.exception.args[0])

    def test_for_bad_node_in_lsp_data(self):

        err_msg = "No Node with name Y in Model"

        with self.assertRaises(ModelException) as context:
            PerformanceModel.load_model_file('test/model_bad_node_in_lsp.csv')
        self.assertIn(err_msg, context.exception.args[0])

    def test_sim_diagnostics(self):
        """
        Validates data returned by simulation_diagnostics() call
        """
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()

        sim_diags = model.simulation_diagnostics()

        # Expand the generators into lists
        dmds_riding_lsps = [lsp for lsp in sim_diags['demands riding LSPs generator']]
        routed_lsps_w_demands = [lsp for lsp in sim_diags['routed LSPs with demands generator']]
        routed_lsps_no_demands = [lsp for lsp in sim_diags['routed LSPs with no demands generator']]

        # Get some demands and LSPs
        dmd_a_d_1 = model.get_demand_object('A', 'D', 'dmd_a_d_1')
        dmd_a_d_2 = model.get_demand_object('A', 'D', 'dmd_a_d_2')
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')

        # Validate
        self.assertEqual(sim_diags['Number of Demands not riding LSPs'], 2)
        self.assertEqual(sim_diags['Number of Demands riding LSPs'], 2)
        self.assertEqual(sim_diags['Number of routed LSPs carrying Demands'], 2)
        self.assertEqual(sim_diags['Number of routed LSPs with no Demands'], 0)
        self.assertEqual(sim_diags['Number of unrouted Demands'], 0)
        self.assertEqual(sim_diags['Number of unrouted LSPs'], 1)

        self.assertTrue(dmd_a_d_1 in dmds_riding_lsps)
        self.assertTrue(dmd_a_d_2 in dmds_riding_lsps)
        self.assertEqual(len(dmds_riding_lsps), 2)

        self.assertTrue(lsp_a_d_1 in routed_lsps_w_demands)
        self.assertTrue(lsp_a_d_2 in routed_lsps_w_demands)
        self.assertEqual(len(routed_lsps_w_demands), 2)
        self.assertEqual(routed_lsps_no_demands, [])

    def test_legacy_model_repr(self):
        """
        Tests the legacy Model class instantiation
        """
        model = Model.load_model_file('test/model_test_topology.csv')
        self.assertEqual(model.__repr__(), 'PerformanceModel(Interfaces: 18, Nodes: 7, Demands: 4, RSVP_LSPs: 3)')
