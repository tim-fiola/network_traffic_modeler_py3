import unittest

from pyNTM import FlexModel


class TestRSVPLSPAddLSP3LSPs(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = FlexModel.load_model_file('test/test_rsvp_3rd_lsp_2_paths_parallel_links.csv')
        self.lsp_a_e_1 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
        self.lsp_a_e_2 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
        self.lsp_a_e_3 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')
        self.model.update_simulation()

    # Each LSP will attempt to signal for 270 traffic/3 LSPs = 90 traffic/lsp.
    # Since any path from A to E cannot fit 90*2 traffic, only 2 of the LSPs
    # will be able to signal and reserve a setup bandwidth of 90 traffic
    def test_1_lsp_unrouted(self):
        # One of the 3 LSPs will not set up
        self.assertEqual([self.lsp_a_e_1.reserved_bandwidth,
                          self.lsp_a_e_2.reserved_bandwidth,
                          self.lsp_a_e_3.reserved_bandwidth].count('Unrouted'), 1)

    def test_auto_bw_adjust(self):
        # Once the 2 LSPs that do initially signal for 90 traffic,
        # each will have room to signal for and reserve more
        # traffic: 270 traffic/2 lsps = 135 traffic/lsp
        self.assertEqual([self.lsp_a_e_1.reserved_bandwidth,
                          self.lsp_a_e_2.reserved_bandwidth,
                          self.lsp_a_e_3.reserved_bandwidth].count(135.0), 2)
        int_a_b_1 = self.model.get_interface_object('A-to-B_1', 'A')
        int_a_b_2 = self.model.get_interface_object('A-to-B_2', 'A')
        # The 2 LSPs that do set up will have setup_bandwidth
        # of 135 units
        self.assertEqual(int_a_b_1.reserved_bandwidth, 135.0)
        self.assertEqual(int_a_b_2.reserved_bandwidth, 135.0)

    def test_auto_bw_adjust_2(self):
        # Add 4th LSP from A to E
        self.model.add_rsvp_lsp('A', 'E', 'lsp_a_e_4')
        self.model.update_simulation()

        lsp_a_e_4 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_4')
        int_a_b_1 = self.model.get_interface_object('A-to-B_1', 'A')
        int_a_b_2 = self.model.get_interface_object('A-to-B_2', 'A')

        # Each LSP should have 67.5 units of reserved bandwidth
        self.assertEqual([self.lsp_a_e_1.reserved_bandwidth,
                          self.lsp_a_e_2.reserved_bandwidth,
                          self.lsp_a_e_3.reserved_bandwidth,
                          lsp_a_e_4.reserved_bandwidth].count(67.5), 4)

        # Each LSP should have 67.5 units of traffic
        self.assertEqual([self.lsp_a_e_1.traffic_on_lsp(self.model),
                          self.lsp_a_e_2.traffic_on_lsp(self.model),
                          self.lsp_a_e_3.traffic_on_lsp(self.model),
                          lsp_a_e_4.traffic_on_lsp(self.model)].count(67.5), 4)

        # At least one of the interfaces from A to B will have a
        # reserved_bandwidth of 135.0 units
        self.assertTrue([int_a_b_1.reserved_bandwidth,
                         int_a_b_2.reserved_bandwidth].count(135.0) >= 1)

    def test_add_more_traffic(self):
        # Add 4th LSP from A to E (use an isolated model for this)
        model = FlexModel.load_model_file('test/test_rsvp_3rd_lsp_2_paths_parallel_links.csv')
        model.add_rsvp_lsp('A', 'E', 'lsp_a_e_4')
        model.update_simulation()

        # Add more traffic from A to E; total now is 270 + 60 units
        model.add_demand('A', 'E', 60, 'dmd_a_e_2')
        model.update_simulation()

        lsp_a_e_1 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
        lsp_a_e_2 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
        lsp_a_e_3 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')
        lsp_a_e_4 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_4')

        # Each LSP will try to signal for 330/4 = 82.5 units of
        # setup bandwidth; there will only be 2 paths that can
        # accommodate 82.5 units of reserved_bandwidth.

        # All LSPs will attempt to setup at 82.5 units of traffic
        self.assertEqual([lsp_a_e_1.setup_bandwidth,
                          lsp_a_e_2.setup_bandwidth,
                          lsp_a_e_3.setup_bandwidth,
                          lsp_a_e_4.setup_bandwidth].count(82.5), 4)

        # 2 of the 4 LSPs will successfully reserve 82.5 units of traffic
        reserved_bandwidth_list = [lsp_a_e_1.reserved_bandwidth,
                                   lsp_a_e_2.reserved_bandwidth,
                                   lsp_a_e_3.reserved_bandwidth,
                                   lsp_a_e_4.reserved_bandwidth]

        self.assertEqual(reserved_bandwidth_list.count(82.5), 2)

        # 2 of the 4 LSPs will not route
        self.assertEqual(reserved_bandwidth_list.count('Unrouted'), 2)

        # The 330 units of traffic from A to E will load balance
        # over those 2 LSPs, so each LSP will carry 165 units of
        # traffic
        self.assertEqual([lsp_a_e_1.traffic_on_lsp(model),
                          lsp_a_e_2.traffic_on_lsp(model),
                          lsp_a_e_3.traffic_on_lsp(model),
                          lsp_a_e_4.traffic_on_lsp(model)].count(165.0), 2)
