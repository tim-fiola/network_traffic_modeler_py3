import unittest
# from pyNTM import FlexModel
from pyNTM import ModelException
from pyNTM import PerformanceModel


class TestIGPShortcuts(unittest.TestCase):

    # def test_traffic_on_shortcut_lsps(self):
    #     # The demands should take LSPs starting on the first
    #     # node that has shortcuts and should take the LSP that
    #     # leads it closest to the demand destination
    #     model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path.csv')
    #     model.update_simulation()

    # def test_igp_shortcut_node_attributes(self):
    #     # The IGP shortcut attribute should be True
    #     #
    #     pass #

    def test_demands_no_shortcuts(self):
        """
        The demand should take the LSP if the IGP shortcut attribute is True.
        When the IGP shortcut attribute is turned to False, the demand should
        only IGP route
        """

        pass

    def test_igp_shortcut_perf_model(self):

        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        node_a = model.get_node_object('A')
        node_a.igp_shortcuts_enabled = True

        err_msg = 'igp_shortcuts_enabled not allowed in PerformanceModel, but present on these Nodes'

        with self.assertRaises(ModelException) as context:
            model.update_simulation()
        self.assertIn(err_msg, context.exception.args[0][1][0].keys())
