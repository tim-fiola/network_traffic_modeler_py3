import unittest

from pyNTM import Model


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = Model.load_model_file('test/model_test_topology.csv')

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.dmd_a_d_1 = self.model.get_demand_object('A', 'D', 'dmd_a_d_1')
        self.dmd_a_d_2 = self.model.get_demand_object('A', 'D', 'dmd_a_d_2')
        self.dmd_a_f_1 = self.model.get_demand_object('A', 'F', 'dmd_a_f_1')
        self.model.update_simulation()

    def test_demand_add(self):
        self.model.add_demand('A', 'B', 40, 'dmd_a_b')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 3)')

    def test_rsvp_lsp_add(self):
        self.model.add_rsvp_lsp('A', 'B', 'lsp_a_b_1')
        self.model.update_simulation()
        self.assertEqual(self.model.__repr__(), 'Model(Interfaces: 18, Nodes: 7, Demands: 5, RSVP_LSPs: 4)')

    def test_node_source_demands(self):
        dmd_a_b = self.model.get_demand_object('A', 'B', 'dmd_a_b')
        self.assertTrue(dmd_a_b in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_d_1 in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_d_2 in self.model.get_demand_objects_source_node('A'))
        self.assertTrue(self.dmd_a_f_1 in self.model.get_demand_objects_source_node('A'))

    def test_node_dest_demands(self):
        dmd_a_b = self.model.get_demand_object('A', 'B', 'dmd_a_b')
        self.assertEqual(self.model.get_demand_objects_dest_node('B'), [dmd_a_b])

    # TODO - get get_failed_interface_objects before int fail

    # TODO - test fail interface

    # TODO - test get_unfailed_interface_objects

    # TODO - get get_failed_interface_objects after int fail

    # TODO - test unfail interface when one of the Nodes is failed
