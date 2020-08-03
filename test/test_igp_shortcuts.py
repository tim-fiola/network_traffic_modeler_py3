import unittest
# from pyNTM import FlexModel
from pyNTM import ModelException
from pyNTM import PerformanceModel


class TestIGPShortcuts(unittest.TestCase):

    # def test_traffic_on_shortcut_lsps(self):
    #     model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path.csv')
    #     model.update_simulation()

    # def test_igp_shortcut_node_attributes(self):
    #
    #     #
    #     pass

    def test_igp_shortcut_perf_model(self):

        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        node_a = model.get_node_object('A')
        node_a.igp_shortcuts_enabled = True

        err_msg = 'igp_shortcuts_enabled not allowed in PerformanceModel, but present on these Nodes'

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0][1][0].keys())
