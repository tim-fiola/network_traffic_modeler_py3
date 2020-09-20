import unittest
from pyNTM import FlexModel
from pyNTM import ModelException
from pyNTM import PerformanceModel


class TestIGPShortcuts(unittest.TestCase):

    def verify_demand_paths(self):
        """
        Verify demand paths in baseline model
        """
        pass

    def test_traffic_on_shortcut_lsps(self):
        """
        Verify Interface and LSP traffic when IGP shortcuts enabled
        in baseline model.
        """

        # The demands should take LSPs starting on the first
        # node that has shortcuts and should take the LSP that
        # leads it closest to the demand destination
        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')
        model.update_simulation()

        # Get all the interface objects
        int_a_b = model.get_interface_object('A-B', 'A')
        int_b_c = model.get_interface_object('B-C', 'B')
        int_c_d = model.get_interface_object('C-D', 'C')
        int_d_e = model.get_interface_object('D-E', 'D')
        int_e_f = model.get_interface_object('E-F', 'E')
        int_a_g = model.get_interface_object('A-G', 'A')
        int_g_f = model.get_interface_object('G-F', 'G')

        # Get all LSP objects
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_c_e_1 = model.get_rsvp_lsp('C', 'E', 'lsp_c_e_1')
        lsp_d_f_1 = model.get_rsvp_lsp('D', 'F', 'lsp_d_f_1')

        # Verify traffic on LSPs
        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 2.5)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 2.5)
        self.assertEqual(lsp_c_e_1.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_d_f_1.traffic_on_lsp(model), 13.0)

        # Verify demand paths

        # Verify interface traffic
        self.assertEqual(int_a_b.traffic, 5.0)
        self.assertEqual(int_b_c.traffic, 5.0)
        self.assertEqual(int_c_d.traffic, 5.0)
        self.assertEqual(int_d_e.traffic, 13.0)
        self.assertEqual(int_e_f.traffic, 13.0)
        self.assertEqual(int_a_g.traffic, 5.0)
        self.assertEqual(int_g_f.traffic, 5.0)

    def test_igp_shortcut_node_attributes(self):
        # The IGP shortcut attribute should be True
        #
        pass

    # Remove igp_shortcuts_enabled on node B, traffic should appear on lsp_c_e_1
    # and disappear from lsp_b_d_1/2 and lsp_d_f_1
    def remove_shortcuts_node_b(self):
        pass

    def test_demands_no_shortcuts(self):
        """
        The demand should take the LSP if the IGP shortcut attribute is True.
        When the IGP shortcut attribute is turned to False, the demand should
        only IGP route.  Change all igp_shortcuts_enabled flags to False.
        Test LSP and Interface traffic.
        """

        pass

    def test_igp_shortcut_perf_model(self):

        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        node_a = model.get_node_object('A')
        node_a.igp_shortcuts_enabled = True

        err_msg = 'igp_shortcuts_enabled not allowed in PerformanceModel, but present on these Nodes'

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0][1][0].keys())
