# TODO - add the unit tests for rsvp manual metric for both Flex and Performance Models
import unittest
from pyNTM import FlexModel
# from pyNTM import ModelException
# from pyNTM import PerformanceModel


class TestIGPShortcuts(unittest.TestCase):
    # Load FlexModel, verify LSP metrics

    # Load PerformanceModel, verify LSP metrics

    # 2 parallel LSPs source-dest, but one with a lower than default metric;
    # traffic should only take lower metric LSP
    def test_unequal_metric_lsps_flex_model(self):
        model = FlexModel.load_model_file('test/lsp_manual_metric_test_model.csv')
        model.update_simulation()

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
