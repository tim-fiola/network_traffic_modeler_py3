import unittest

from pyNTM import Model


class TestRSVPLSPIntFailure(unittest.TestCase):

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

        # Fail an interface to test failover behavior
        self.model.fail_interface('A-to-B', 'A')
        self.model.update_simulation()

    # This next section will see if the LSPs behave as expected
    # to the failed interface int_a_c
    def test_fail_interface(self):
        self.assertTrue(self.int_a_b.failed)
        self.model.update_simulation()

    # Update the simulation and make sure both LSPs are on
    # interface int_a_c
    def test_lsp_failover(self):
        self.assertTrue(self.int_a_b.failed)

        # int_a_b should not have any LSPs
        lsps_on_int_a_b = [lsp for lsp in self.int_a_b.lsps(self.model)]
        self.assertTrue(len(lsps_on_int_a_b) == 0)

        # int_a_c should have lsp_a_d_1 and lsp_a_d_2
        lsp_names_on_int_a_c = [lsp.lsp_name for lsp in self.int_a_c.lsps(self.model)]
        self.assertIn('lsp_a_d_1', lsp_names_on_int_a_c)
        self.assertIn('lsp_a_d_2', lsp_names_on_int_a_c)

        # reservable_bandwidth on int_a_c
        self.assertEqual(self.int_a_c.reserved_bandwidth, 150.0)
        self.assertEqual(self.int_a_c.reservable_bandwidth, 0.0)
