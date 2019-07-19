import unittest

from pyNTM import Node
from pyNTM import RSVP_LSP
from pyNTM import Model

import pdb



class TestRSVPLSP(unittest.TestCase):

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
        # self.node_a = Node(name='nodeA', lat=0, lon=0)
        # self.node_b = Node(name='nodeB', lat=0, lon=0)
        # self.rsvp_lsp = RSVP_LSP(source_node_object=self.node_a, dest_node_object=self.node_b, lsp_name='A-to-B')

    def test_lsp_instance(self):
        self.assertIsInstance(self.lsp_a_d_1, RSVP_LSP)

    def test_lsp_path_instance(self):
        self.assertIsInstance(self.lsp_a_d_1.path, dict)

    def test_lsp_effective_metric_value(self):
        self.assertEqual(40.0, self.lsp_a_d_1.effective_metric(self.model))

    def test_lsp_repr(self):
        self.assertEqual(repr(self.lsp_a_d_1), "RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_1')")

    def test_lsp_reserved_bw(self):
        self.assertEqual(self.lsp_a_d_1.reserved_bandwidth, 75.0)

    # lsp_a_d_1 and lsp_a_d_2 take different paths, so actual_metric values
    # should not be equal; one path actual_metric is 40, the other path's
    # actual metric is 60
    def test_lsp_actual_metrics(self):
        print(self.lsp_a_d_1.actual_metric(self.model),
                            self.lsp_a_d_2.actual_metric(self.model))
        pdb.set_trace()
        self.assertNotEqual(self.lsp_a_d_1.actual_metric(self.model),
                            self.lsp_a_d_2.actual_metric(self.model))
        self.assertIn(self.lsp_a_d_1.actual_metric(self.model), [40, 60])
        self.assertIn(self.lsp_a_d_2.actual_metric(self.model), [40, 60])

    # lsp_f_e_1 should not be routed because
    # 1. It is trying to initially signal
    # 2. It has a setup_bandwidth of 400
    # 3. There are no available paths to support that setup_bandwidth
    def test_lsp_setup_bandwidth_failure(self):
        self.assertEqual(self.lsp_f_e_1.path, 'Unrouted')
        self.assertEqual(self.lsp_f_e_1.setup_bandwidth, 400.0)

    # This next section will fail an interface and see if
    # the LSPs react as expected
    def test_fail_interface(self):
        self.model.fail_interface('A-to-B', 'A')
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






