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

        # Get demand objects
        dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')
        dmd_d_f_1 = model.get_demand_object('D', 'F', 'dmd_d_f_1')

        # Verify traffic on LSPs
        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 2.5)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 2.5)
        self.assertEqual(lsp_c_e_1.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_d_f_1.traffic_on_lsp(model), 13.0)

        # Verify demand paths
        self.assertIn([int_a_g, int_g_f], dmd_a_f_1.path)
        self.assertIn([int_a_b, lsp_b_d_1, lsp_d_f_1], dmd_a_f_1.path)
        self.assertIn([int_a_b, lsp_b_d_2, lsp_d_f_1], dmd_a_f_1.path)

        self.assertEqual(dmd_d_f_1.path, [lsp_d_f_1])

        # Verify interface traffic
        self.assertEqual(int_a_b.traffic, 5.0)
        self.assertEqual(int_b_c.traffic, 5.0)
        self.assertEqual(int_c_d.traffic, 5.0)
        self.assertEqual(int_d_e.traffic, 13.0)
        self.assertEqual(int_e_f.traffic, 13.0)
        self.assertEqual(int_a_g.traffic, 5.0)
        self.assertEqual(int_g_f.traffic, 5.0)

        # Verify LSPs on interfaces
        self.assertIn(lsp_b_d_1, int_b_c.lsps(model))
        self.assertIn(lsp_b_d_2, int_b_c.lsps(model))
        self.assertIn(lsp_b_d_1, int_c_d.lsps(model))
        self.assertIn(lsp_b_d_2, int_c_d.lsps(model))
        self.assertIn(lsp_b_d_2, int_c_d.lsps(model))
        self.assertIn(lsp_c_e_1, int_c_d.lsps(model))

    def test_igp_shortcut_node_attributes(self):
        # The IGP shortcut attribute should be True
        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')

        node_b = model.get_node_object('B')

        self.assertTrue(node_b.igp_shortcuts_enabled)

    # Remove igp_shortcuts_enabled on node B, traffic should appear on lsp_c_e_1
    # and disappear from lsp_b_d_1/2 and lsp_d_f_1
    def remove_shortcuts_node_b(self):

        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')

        node_b = model.get_node_object('B')

        node_b.igp_shortcuts_enabled = False

        model.update_simulation()

        # Get LSP objects
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_c_e_1 = model.get_rsvp_lsp('C', 'E', 'lsp_c_e_1')
        lsp_d_f_1 = model.get_rsvp_lsp('D', 'F', 'lsp_d_f_1')

        dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')
        dmd_d_f_1 = model.get_demand_object('D', 'F', 'dmd_d_f_1')

        # Half the traffic from dmd_a_f_1 should be on lsp_c_e_1
        self.assertEqual(lsp_c_e_1.traffic_on_lsp, 5.0)

        # dmd_a_f_1 should be the only demand on lsp_c_e_1
        self.assertEqual(lsp_c_e_1.demands_on_lsp(model), [dmd_a_f_1])

        # dmd_d_f_1 should be the only demand on lsp_d_f_1
        self.assertEqual(lsp_d_f_1.demands_on_lsp(model), [dmd_d_f_1])

        # LSPs from B to D should have no demands and no traffic
        self.assertEqual(lsp_b_d_1.demands_on_lsp(model), [])
        self.assertEqual(lsp_b_d_2.demands_on_lsp(model), [])
        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 0)

    def test_demands_no_shortcuts(self):
        """
        The demand should take the LSP if the IGP shortcut attribute is True on node B.
        When the IGP shortcut attribute is turned to False, the demand should
        only IGP route.  Change all igp_shortcuts_enabled flags to False.
        Test LSP and Interface traffic.
        """

        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')
        model.update_simulation()

        # Get all LSP objects
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_c_e_1 = model.get_rsvp_lsp('C', 'E', 'lsp_c_e_1')
        lsp_d_f_1 = model.get_rsvp_lsp('D', 'F', 'lsp_d_f_1')

        # Get some node objects
        node_b = model.get_node_object('B')
        node_c = model.get_node_object('C')
        node_d = model.get_node_object('D')
        node_e = model.get_node_object('E')

        # Get LSP object
        dmd_d_f_1 = model.get_demand_object('D', 'F', 'dmd_d_f_1')

        # Set the node igp_shortcuts_enabled attribute to False
        node_b.igp_shortcuts_enabled = False
        node_c.igp_shortcuts_enabled = False
        node_d.igp_shortcuts_enabled = False
        node_e.igp_shortcuts_enabled = False
        model.update_simulation()

        # Only lsp_d_f_1 should have traffic/demands
        self.assertEqual(lsp_b_d_1.demands_on_lsp(model), [])
        self.assertEqual(lsp_b_d_2.demands_on_lsp(model), [])
        self.assertEqual(lsp_c_e_1.demands_on_lsp(model), [])
        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_c_e_1.traffic_on_lsp(model), 0)

        self.assertEqual(lsp_d_f_1.demands_on_lsp(model), [dmd_d_f_1])
        self.assertEqual(lsp_d_f_1.traffic_on_lsp(model), 8.0)

    def test_igp_shortcut_perf_model(self):

        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        node_a = model.get_node_object('A')
        node_a.igp_shortcuts_enabled = True

        err_msg = 'igp_shortcuts_enabled not allowed in PerformanceModel, but present on these Nodes'

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0][1][0].keys())

    # If the LSPs from B to D are assigned a lower metric, traffic should
    # not split at A
    def changed_metric(self):

        pass
