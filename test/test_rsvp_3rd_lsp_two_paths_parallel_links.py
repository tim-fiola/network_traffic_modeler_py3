import unittest

from pyNTM import Parallel_Link_Model


class TestRSVPLSPAddLSP3LSPs(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = Parallel_Link_Model.load_model_file('test/test_rsvp_3rd_lsp_2_paths_parallel_links.csv')
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

    # Once the 2 LSPs that do initially signal for 90 traffic, each will have
    # room to signal for and reserve more traffic: 270 traffic/2 lsps = 135 traffic/lsp
    def test_auto_bw_adjust(self):
        # The 2 LSPs that do set up will have setup_bandwidth of 135
        import pdb
        pdb.set_trace()
        self.assertEqual([self.lsp_a_e_1.reserved_bandwidth,
                          self.lsp_a_e_2.reserved_bandwidth,
                          self.lsp_a_e_3.reserved_bandwidth].count(135.0), 2)
