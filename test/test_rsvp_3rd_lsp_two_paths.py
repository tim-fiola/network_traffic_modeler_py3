import unittest

from pyNTM import Model


class TestRSVPLSPAddLSP(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.model = Model.load_model_file('test/model_test_topology.csv')
        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.model.update_simulation()

        # Fail an interface
        self.model.fail_interface('A-to-B', 'A')
        self.model.update_simulation()

        # Add additional traffic from A to D
        self.model.add_demand('A', 'D', 100, 'demand_a_d_3')
        self.model.update_simulation()

        # Unfail interface int_a_b
        self.model.unfail_interface('A-to-B', 'A')
        self.model.update_simulation()

        # Add 3rd lsp from Node('A') to Node('D'); this LSP
        # will be the 3rd LSP signaled over two possible paths;
        # this LSP should cause one of the 3 to not signal
        self.model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        self.model.update_simulation()
        self.lsp_a_d_3 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

    def test_reserved_bandwidth(self):
        """
        The 3rd LSP from Node('A') to Node('D') should cause one of
        the lsp_a_d_[1-3] to not signal.
        This LSP will be the 3rd LSP signaled over two possible paths,
        with the 2 existing LSPs each taking up the majority of
        reservable bandwidth on each path.
        """

        # One of the 3 LSPs will not set up
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)

        # The 2 LSPs that do set up will have setup_bandwidth of 125
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count(125.0), 2)

    def test_setup_bandwidth(self):
        """
        Each of the 3 LSPs from A to D will try to signal
        for (traffic/num_lsps) = 250/3 = 83.3.  The first two to signal will
        succeed.  The last one will fail due to lack of available bandwidth.
        When this happens, the traffic will then be split across 2 LSPs.
        So each LSP will try to resignal to carry more traffic (125 units).
        The LSP taking the A-to-B, B-to-D path
        """
