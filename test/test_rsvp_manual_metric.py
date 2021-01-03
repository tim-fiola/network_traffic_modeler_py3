# TODO - add the unit tests for rsvp manual metric for both Flex and Performance Models
import unittest
from pyNTM import FlexModel
from pyNTM import ModelException
from pyNTM import PerformanceModel


class TestIGPShortcutsFlexModel(unittest.TestCase):
    # Load FlexModel, verify LSP metrics
    def test_model_load_flex_model(self):
        model = FlexModel.load_model_file('test/lsp_manual_metric_test_flex_model.csv')
        model.update_simulation()
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_b_d_3 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_3')
        lsp_b_d_4 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_4')

        self.assertEqual(lsp_b_d_1.manual_metric, 10)
        self.assertEqual(lsp_b_d_1.effective_metric(model), 10)
        self.assertEqual(lsp_b_d_1.topology_metric(model), 20)
        self.assertNotEqual(lsp_b_d_1.path, 'Unrouted')
        self.assertEqual(lsp_b_d_1.configured_setup_bandwidth, 2)
        self.assertEqual(lsp_b_d_1.setup_bandwidth, 2)

        self.assertEqual(lsp_b_d_2.manual_metric, 9)
        self.assertEqual(lsp_b_d_2.effective_metric(model), 9)
        self.assertEqual(lsp_b_d_2.topology_metric(model), 20)
        self.assertNotEqual(lsp_b_d_2.path, 'Unrouted')
        self.assertIsNone(lsp_b_d_2.configured_setup_bandwidth)

        self.assertEqual(lsp_b_d_3.manual_metric, 'not set')
        self.assertEqual(lsp_b_d_3.topology_metric(model), 20)
        self.assertEqual(lsp_b_d_3.effective_metric(model), 20)
        self.assertEqual(lsp_b_d_3.configured_setup_bandwidth, 3)
        self.assertEqual(lsp_b_d_3.setup_bandwidth, 3)
        self.assertNotEqual(lsp_b_d_3.path, 'Unrouted')

        self.assertEqual(lsp_b_d_4.manual_metric, 'not set')
        self.assertEqual(lsp_b_d_4.topology_metric(model), 20)
        self.assertEqual(lsp_b_d_4.effective_metric(model), 20)
        self.assertNotEqual(lsp_b_d_4.path, 'Unrouted')

    # Parallel LSPs in IGP shortcuts, but one with a lower metric;
    # traffic should only take lower metric LSP
    def test_lsp_metric_efficacy(self):
        model = FlexModel.load_model_file('test/lsp_manual_metric_test_flex_model.csv')
        model.update_simulation()
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_b_d_3 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_3')
        lsp_b_d_4 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_4')

        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 10)  # lowest metric LSP
        self.assertEqual(lsp_b_d_3.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_b_d_4.traffic_on_lsp(model), 0)

    # Parallel LSPs source-dest, but one with a lower metric;
    # traffic should only take lower metric LSP
    def test_lsp_metric_efficacy_2(self):
        model = FlexModel.load_model_file('test/flex_model_parallel_source_dest_lsps.csv')
        model.update_simulation()

        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')  # lower metric
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')  # default metric (higher)

        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 22)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 0)

    # 2 LSP source-dest, but with higher than default metric;
    # traffic should take LSPs due to better protocol preference;
    def test_lsp_metric_higher_than_igp_metric(self):
        model = FlexModel.load_model_file('test/flex_model_parallel_source_dest_lsps.csv')
        model.update_simulation()

        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')

        lsp_b_d_1.manual_metric = 1000
        lsp_b_d_2.manual_metric = 1000

        model.update_simulation()

        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 11)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 11)

    # Reset a manual metric to default using -1
    def test_lsp_reset_manual_metric(self):
        model = FlexModel.load_model_file('test/flex_model_parallel_source_dest_lsps.csv')
        model.update_simulation()

        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')  # this has manual_metric set to 20 from model file
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')

        lsp_b_d_1.manual_metric = -1

        model.update_simulation()

        self.assertEqual(lsp_b_d_1.topology_metric(model), 40)
        self.assertEqual(lsp_b_d_1.traffic_on_lsp(model), 11)
        self.assertEqual(lsp_b_d_2.traffic_on_lsp(model), 11)

    # Assign a bad LSP metric (float, string); make sure it fails
    def test_lsp_bad_manual_metric(self):
        model = FlexModel.load_model_file('test/flex_model_parallel_source_dest_lsps.csv')
        model.update_simulation()
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')  # this has manual_metric set to 20 from model file

        err_msg = "RSVP LSP metric must be positive integer value.  Or, set manual_metric to -1 "

        with self.assertRaises(ModelException) as context:
            lsp_b_d_1.manual_metric = 20.1
        self.assertTrue(err_msg in context.exception.args[0])


class TestIGPShortcutsPerfModel(unittest.TestCase):
    # Load PerformanceModel, verify LSP metrics and LSP routing
    def test_model_load_perf_model(self):
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
        self.assertEqual(lsp_a_d_1.setup_bandwidth, 4)
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
        self.assertEqual(lsp_a_d_4.setup_bandwidth, 4)
        self.assertNotEqual(lsp_a_d_4.path, 'Unrouted')

    # Parallel LSPs source-dest, but one with a lower metric;
    # traffic should only take lower metric LSP
    def test_perf_model_metric_efficacy(self):
        model = PerformanceModel.load_model_file('test/lsp_manual_metric_test_model.csv')
        model.update_simulation()

        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        lsp_a_d_4 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_4')

        self.assertEqual(lsp_a_d_1.traffic_on_lsp(model), 150)
        self.assertEqual(lsp_a_d_2.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_a_d_3.traffic_on_lsp(model), 0)
        self.assertEqual(lsp_a_d_4.traffic_on_lsp(model), 0)
