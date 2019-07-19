import unittest

from pyNTM import Node
from pyNTM import RSVP_LSP
from pyNTM import Model

import pdb

class TestRSVPLSPFailure(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.model1 = Model.load_model_file('model_test_topology.csv')
        self.lsp_a_d_1 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model1.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model1.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model1.get_interface_object('A-to-C', 'A')
        self.model1.update_simulation()
        self.model1.fail_interface('A-to-B', 'A')
        self.model1.update_simulation()

    # This next section will see if the LSPs behave as expected
    # to the failed interface int_a_c
    def test_fail_interface(self):
        self.assertTrue(self.int_a_b.failed)
        self.model1.update_simulation()

    # Update the simulation and make sure both LSPs are on
    # interface int_a_c
    def test_lsp_failover(self):
        self.assertTrue(self.int_a_b.failed)

        # int_a_b should not have any LSPs
        lsps_on_int_a_b = [lsp for lsp in self.int_a_b.lsps(self.model1)]
        self.assertTrue(len(lsps_on_int_a_b) == 0)

        # int_a_c should have lsp_a_d_1 and lsp_a_d_2
        lsp_names_on_int_a_c = [lsp.lsp_name for lsp in self.int_a_c.lsps(self.model1)]
        self.assertIn('lsp_a_d_1', lsp_names_on_int_a_c)
        self.assertIn('lsp_a_d_2', lsp_names_on_int_a_c)
