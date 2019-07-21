import unittest

from pyNTM import Model


class TestRSVPLSPTraffAdd(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.model = Model.load_model_file('model_test_topology.csv')
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

    # Validate the reserved and setup bandwidths of lsp_a_d_1, lsp_a_d_2
    def test_reserved_bandwidth(self):  # This will not pass with the non-state LSP path routing
        print("lsp_a_d_1.reserved_bandwidth = {}".format(self.lsp_a_d_1.reserved_bandwidth))
        self.assertEqual(self.lsp_a_d_1.reserved_bandwidth, 75.0)
        self.assertEqual(self.lsp_a_d_2.reserved_bandwidth, 75.0)

    def test_setup_bandwidth(self):
        self.assertEqual(self.lsp_a_d_1.setup_bandwidth, 125.0)
        self.assertEqual(self.lsp_a_d_2.setup_bandwidth, 125.0)

    # Validate the reserved and reservable bandwidth on int_a_c
    def test_int_bw(self):  # This will not pass with the non-state LSP path routing
        print("int_a_c reserved and reservable bw = {} and {}".format(self.int_a_c.reserved_bandwidth,
                                                                      self.int_a_c.reservable_bandwidth))
        self.assertEqual(self.int_a_c.reserved_bandwidth, 150.0)
        self.assertEqual(self.int_a_c.reservable_bandwidth, 0.0)
