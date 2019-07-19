import unittest

from pyNTM import Node
from pyNTM import RSVP_LSP
from pyNTM import Model

import pdb

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


    def test_reserved_bandwidth(self):
