import unittest
from pyNTM import FlexModel

class TestDemand(unittest.TestCase):

    def test_traffic_on_shortcut_lsps(self):
        model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path.csv')
        model.update_simulation()

    def test_igp_shortcut_node_attributes(self):

        #
        pass
