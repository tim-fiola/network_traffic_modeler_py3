# TODO - add the unit tests for rsvp manual metric for both Flex and Performance Models
import unittest
# from pyNTM import FlexModel
# from pyNTM import ModelException
from pyNTM import PerformanceModel


class TestIGPShortcuts(unittest.TestCase):
    # Load FlexModel, verify LSP metrics

    # Load PerformanceModel, verify LSP metrics and LSP routing
    def test_unequal_metric_lsps_perf_model(self):
        model = PerformanceModel.load_model_file('test/lsp_manual_metric_test_model.csv')
        model.update_simulation()
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        lsp_a_d_4 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_4')

        self.assertEqual(lsp_a_d_1.effective_metric(model), 5)
        self.assertEqual(lsp_a_d_1.manual_metric, 5)
        self.assertEqual(lsp_a_d_1.topology_metric(model), 40)
        self.assertEqual(lsp_a_d_1.configured_setup_bandwidth, 4)
        self.assertNotEqual(lsp_a_d_1.path, 'Unrouted')

        self.assertEqual(lsp_a_d_2.effective_metric(model), 10)
        self.assertEqual(lsp_a_d_2.manual_metric, 10)
        self.assertEqual(lsp_a_d_2.topology_metric(model), 40)
        self.assertNotEqual(lsp_a_d_2.path, 'Unrouted')

        self.assertEqual(lsp_a_d_3.effective_metric(model), 40)
        self.assertEqual(lsp_a_d_3.topology_metric(model), 40)
        self.assertEqual(lsp_a_d_3.manual_metric, 'not set')
        self.assertNotEqual(lsp_a_d_3.path, 'Unrouted')

        self.assertEqual(lsp_a_d_4.effective_metric(model), 40)
        self.assertEqual(lsp_a_d_4.manual_metric, 'not set')
        self.assertEqual(lsp_a_d_4.topology_metric(model), 40)
        self.assertEqual(lsp_a_d_4.configured_setup_bandwidth, 4)
        self.assertNotEqual(lsp_a_d_4.path, 'Unrouted')
    # 2 parallel LSPs source-dest, but one with a lower than default metric;
    # traffic should only take lower metric LSP

    # 2 parallel LSPs source-dest, but one with a lower than default metric;
    # traffic should only take lower metric LSP

    # 1 LSP source-dest, but with higher than default metric;
    # traffic should take that LSP due to better protocol preference;
    # if that LSP fails, IGP routing

    # 2 parallel LSPs source-dest, one with more hops than the other;
    # the one with fewer hops has the highest metric; traffic should
    # take the lower-metric LSP

    # 2 parallel LSPs source-dest, both with higher than default metric, but
    # one LSP with a higher metric than the other.  Traffic should take lower
    # metric LSP

    # Put a bad LSP metric in the model file (float, string); make sure it errors

    # Assign a bad LSP metric (float, string); make sure it fails
