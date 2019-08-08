import unittest

from pyNTM import Model

class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = Model.load_model_file('test/model_test_topology.csv')

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
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 3)')

    def test_rsvp_lsp_add(self):
        self.model.add_rsvp_lsp('A', 'B', 'lsp_a_b_1')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 4)')

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
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()
        failed_int_list = model.get_failed_interface_objects()
        self.assertEqual(len(failed_int_list), 2)

    def test_get_unfailed_ints_2(self):
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()
        self.assertEqual(len(model.get_unfailed_interface_objects()), 16)

    def test_unfail_interface(self):
        model = Model.load_model_file('test/model_test_topology.csv')
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
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertTrue(model.get_node_object('A').failed)

    def test_failed_node_interfaces(self):
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        model.fail_node('A')
        model.update_simulation()
        self.assertEqual(len(model.get_failed_interface_objects()), 8)

    # When a Node is failed, all of its Interfaces must stay failed
    # until the Node is unfailed
    def test_int_stays_down(self):
        model = Model.load_model_file('test/model_test_topology.csv')
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
        model = Model.load_model_file('test/model_test_topology.csv')
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
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        all_paths = model.get_all_paths_reservable_bw('A', 'D', False, 2, 0)
        self.assertEqual(len(all_paths['path']), 3)
        path_lengths = [len(path) for path in all_paths['path']]
        path_lengths.sort()
        self.assertEqual(path_lengths, [1, 2, 2])

    # Find all simple paths from A to D with at least 10 unit of
    # reservable bandwidth
    def test_all_paths_needed_bw(self):
        model = Model.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        all_paths = model.get_all_paths_reservable_bw('A', 'D', False, 10)
        self.assertEqual(len(all_paths['path']), 4)
        path_lengths = [len(path) for path in all_paths['path']]
        path_lengths.sort()
        self.assertEqual(path_lengths, [1, 2, 2, 3])
