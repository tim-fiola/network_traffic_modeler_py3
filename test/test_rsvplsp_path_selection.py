import unittest

from pyNTM import Model


class TestRSVPLSPPathSelection(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = Model.load_model_file('test/model_test_topology_2.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_e_a_1 = self.model.get_rsvp_lsp('E', 'A', 'lsp_e_a_1')
        self.int_a_d = self.model.get_interface_object('A-to-D', 'A')

        self.model.update_simulation()

    def test_choose_random_path_selection(self):
        lsp_a_d_1_path_info = [(interface.name, interface.node_object.name)
                               for interface in self.lsp_a_d_1.path['interfaces']]

        path_list = [[('A-to-B', 'A'), ('B-to-D', 'B')],
                     [('A-to-C', 'A'), ('C-to-D', 'C')]]

        self.assertIn(lsp_a_d_1_path_info, path_list)

    # def test_get_feasible_paths(self):
    #     pdb.set_trace()
    #     self.assertIn(self.int_a_d, self.lsp_a_d_1.path['interfaces'])
