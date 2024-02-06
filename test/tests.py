import unittest
from pyNTM import Model

class SourceDestNodes(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.model = Model.load_model_file("csv_flex_model_parallel_source_dest_lsps.csv")
        self.model.converge_model()

    def lsp_setup_bandwidth(self):
        """
        Make sure the calculated _setup_bandwidth is the expected value
        """
        # Index by lsp _key and then find _setup_bandwidth for the lsp with the specific _key
        lsp_setup_bw = self.model.lsps_dataframe.set_index('_key').loc['B__D__lsp_b_d_1']['_setup_bandwidth']
        self.assertEqual(lsp_setup_bw, 20)

    # Make sure demand _src_dest_nodes groups are valid

    # Make sure demands _src_dest_nodes_agg_traffic values are valid

    # Make sure demand _key values are valid

    # Make sure LSP _src_dest_nodes groups are valid

    # Make sure LSP _key values are valid

    # Make sure LSP _setup_bandwidth values  are valid

    # Make sure interface _circuit_failed column is valid
    # True/True, True/False, False/False scenarios

    # Make sure interface _interface_failed column is valid
    # True/True, True/False, False/False scenarios





