import unittest

from pyNTM import PerformanceModel


class TestRSVPLSPPathSelection(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """
        Set up the lsp class.

        Args:
            self: (todo): write your description
        """
        self.model = PerformanceModel.load_model_file('test/model_test_topology_2.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_e_a_1 = self.model.get_rsvp_lsp('E', 'A', 'lsp_e_a_1')
        self.int_a_d = self.model.get_interface_object('A-to-D', 'A')
        self.dmd_a_d_1 = self.model.get_demand_object('A', 'D', 'dmd_a_d_1')

        self.model.update_simulation()

    def test_lsp_no_route(self):
        """
        Test if a lsp lsp : lsp is true.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(self.lsp_e_a_1.path, 'Unrouted')

    def test_unrouted_lsp_res_bw(self):
        """
        Test if the lsp ising.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(self.lsp_e_a_1.reserved_bandwidth, 'Unrouted')

    def test_single_demand_on_lsp(self):
        """
        Test if the single single lsp model.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(self.lsp_a_d_1.traffic_on_lsp(self.model), 40)

    def test_random_path_selection(self):
        """
        Load a random test test files.

        Args:
            self: (todo): write your description
        """
        model = PerformanceModel.load_model_file('test/multiple_rsvp_paths.csv')
        model.update_simulation()

        lsp_a_d_1_path_info = [(interface.name, interface.node_object.name)
                               for interface in self.lsp_a_d_1.path['interfaces']]

        path_list = [[('A-to-B', 'A'), ('B-to-D', 'B')],
                     [('A-to-C', 'A'), ('C-to-D', 'C')]]

        self.assertIn(lsp_a_d_1_path_info, path_list)
