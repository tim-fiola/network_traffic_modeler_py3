import unittest

from pyNTM import RSVP_LSP
from pyNTM import PerformanceModel
from pyNTM import ModelException


class TestRSVPLSPInitial(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = PerformanceModel.load_model_file('test/model_test_topology.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.dmd_a_d_1 = self.model.get_demand_object('A', 'D', 'dmd_a_d_1')
        self.dmd_a_d_2 = self.model.get_demand_object('A', 'D', 'dmd_a_d_2')
        self.model.update_simulation()

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

    # lsp_a_d_1 and lsp_a_d_2 each carry part of dmd_a_d_1 and dmd_a_d_2 but
    # do not carry any other demands
    def test_demands_on_lsp(self):
        self.assertIn(self.dmd_a_d_1, self.lsp_a_d_1.demands_on_lsp(self.model))
        self.assertIn(self.dmd_a_d_2, self.lsp_a_d_2.demands_on_lsp(self.model))
        self.assertEqual(len(self.lsp_a_d_1.demands_on_lsp(self.model)), 2)
        self.assertEqual(len(self.lsp_a_d_2.demands_on_lsp(self.model)), 2)

    def test_traffic_on_lsp(self):
        self.assertEqual(self.lsp_a_d_1.traffic_on_lsp(self.model), 75)

    # lsp_a_d_1 and lsp_a_d_2 take different paths, so topology_metric values
    # should not be equal; one path topology_metric is 40, the other path's
    # actual metric is 60
    def test_lsp_actual_metrics(self):
        self.assertNotEqual(self.lsp_a_d_1.topology_metric(self.model),
                            self.lsp_a_d_2.topology_metric(self.model))
        self.assertIn(self.lsp_a_d_1.topology_metric(self.model), [40, 60])
        self.assertIn(self.lsp_a_d_2.topology_metric(self.model), [40, 60])

    # lsp_f_e_1 should not be routed because
    # 1. It is trying to initially signal
    # 2. It has a setup_bandwidth of 400
    # 3. There are no available paths to support that setup_bandwidth
    def test_lsp_setup_bandwidth_failure(self):
        self.assertEqual(self.lsp_f_e_1.path, 'Unrouted')
        self.assertEqual(self.lsp_f_e_1.setup_bandwidth, 400.0)

    def test_unrouted_lsp_actual_metric(self):
        self.assertEqual(self.lsp_f_e_1.topology_metric(self.model), 'Unrouted')

    # Validate reserved and reservable bandwidth on int_a_b, int_a_c
    def test_reserved_bandwidth(self):
        self.assertEqual(self.int_a_b.reserved_bandwidth, 75.0)
        self.assertEqual(self.int_a_b.reservable_bandwidth, 50.0)

        self.assertEqual(self.int_a_c.reserved_bandwidth, 75.0)
        self.assertEqual(self.int_a_c.reservable_bandwidth, 75.0)

    # Test for setup bandwidth must be >= 0
    def test_bad_setup_bw(self):
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()

        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')

        msg = "setup_bandwidth must be 0 or greater"

        with self.assertRaises(ModelException) as context:
            lsp_a_d_1.setup_bandwidth = -1

        self.assertTrue(msg in context.exception.args[0])
