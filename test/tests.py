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