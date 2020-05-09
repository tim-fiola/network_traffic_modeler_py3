import unittest

from pyNTM import PerformanceModel


class TestRSVPLSPAddLSP3LSPs(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = PerformanceModel.load_model_file('test/model_test_topology.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')

        self.model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        self.lsp_a_d_3 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        self.model.add_demand('A', 'D', 100, 'dmd_a_d_3')
        self.model.update_simulation()

    # Each LSP will attempt to signal for 250 traffic/3 LSPs = 83.3 traffic/lsp.
    # Since any path from A to D cannot fit 83.3*2 traffic, only 2 of the LSPs
    # will be able to signal and reserve a setup bandwidth of 83.3 traffic
    def test_1_lsp_unrouted(self):
        # One of the 3 LSPs will not set up
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count('Unrouted'), 1)

    # Once the 2 LSPs that do initially signal for 83.3 traffic, each will have
    # room to signal for and reserve more traffic: 250 traffic/2 lsps = 125 traffic/lsp
    def test_auto_bw_adjust(self):
        # The 2 LSPs that do set up will have setup_bandwidth of 125
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count(125.0), 2)
