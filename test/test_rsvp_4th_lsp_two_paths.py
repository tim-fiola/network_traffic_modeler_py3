import unittest

from pyNTM import Model

class TestRSVPLSPAddLSP4LSPs(unittest.TestCase):

    # @classmethod
    # def setUpClass(self):
    #     self.maxDiff = None
    #     self.model1 = Model.load_model_file('test/model_test_topology_2.csv')
    #     self.lsp_a_d_1 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
    #     self.lsp_a_d_2 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
    #     self.lsp_f_e_1 = self.model1.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
    #     self.int_a_b = self.model1.get_interface_object('A-to-B', 'A')
    #     self.int_a_c = self.model1.get_interface_object('A-to-C', 'A')
    #     self.model1.update_simulation()
    #
    #     # Fail an interface
    #     self.model1.fail_interface('A-to-B', 'A')
    #     self.model1.update_simulation()
    #
    #     # Add additional traffic from A to D
    #     self.model1.add_demand('A', 'D', 100, 'demand_a_d_3')
    #     self.model1.update_simulation()
    #
    #     # Unfail interface int_a_b
    #     self.model1.unfail_interface('A-to-B', 'A')
    #     self.model1.update_simulation()
    #
    #     # Add 3rd and 4th LSPs from Node('A') to Node('D')
    #
    #     self.model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
    #     self.model1.update_simulation()
    #     self.lsp_a_d_3 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
    #
    #
    #     self.model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_4')
    #     self.model1.update_simulation()
    #     self.lsp_a_d_4 = self.model1.get_rsvp_lsp('A', 'D', 'lsp_a_d_4')


    def test_validate_lsp_routing(self):
        """
        Test that all 4 LSPs between A and D route
        """

        model = Model.load_model_file('test/model_test_topology.csv')
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_f_e_1 = model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_a_c = model.get_interface_object('A-to-C', 'A')

        # Fail an interface
        model.fail_interface('A-to-B', 'A')

        # Add additional traffic from A to D
        model.add_demand('A', 'D', 100, 'demand_a_d_3')

        # Unfail interface int_a_b
        model.unfail_interface('A-to-B', 'A')


        # Add 3rd lsp from Node('A') to Node('D'); this LSP
        # will be the 3rd LSP signaled over two possible paths;
        # this LSP should cause one of the 3 to not signal
        model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        model.update_simulation()
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        model.add_rsvp_lsp('A', 'D', 'lsp_a_d_4')
        model.update_simulation()
        lsp_a_d_4 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_4')


        # All the paths for each LSP from Node('A') to Node('D')
        paths = [lsp.path for lsp in model.rsvp_lsp_objects if lsp.source_node_object.name == 'A' and
                 lsp.dest_node_object.name == 'D']

        # Ensure all LSPs route
        self.assertNotIn("Unrouted", paths)
