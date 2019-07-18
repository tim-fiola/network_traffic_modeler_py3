import unittest

from pyNTM import Node
from pyNTM import RSVP_LSP
from pyNTM import Model



class TestRSVPLSP(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.model = Model.load_model_file('model_test_topology.csv')
        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.model.update_simulation()
        # self.node_a = Node(name='nodeA', lat=0, lon=0)
        # self.node_b = Node(name='nodeB', lat=0, lon=0)
        # self.rsvp_lsp = RSVP_LSP(source_node_object=self.node_a, dest_node_object=self.node_b, lsp_name='A-to-B')

    def test_lsp_instance(self):
        self.assertIsInstance(self.lsp_a_d_1, RSVP_LSP)

    def test_lsp_path_instance(self):
        self.assertIsInstance(self.lsp_a_d_1.path, dict)

    def test_lsp_effective_metric(self):
        self.assertEqual(40.0, self.lsp_a_d_1.effective_metric(self.model))

    def test_lsp_repr(self):
        self.assertEqual(repr(self.lsp_a_d_1), "RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_1')")

    def test_lsp_reserved_bw(self):
        self.assertEqual(self.lsp_a_d_1.reserved_bandwidth, 75.0)