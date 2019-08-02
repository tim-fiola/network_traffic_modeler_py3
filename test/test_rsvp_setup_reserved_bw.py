import sys  # noqa - these lines are a hack to get testing working
sys.path.append('..')  # noqa
sys.path.append('.')   # noqa

sys.path.append('test')  # noqa -


import unittest

from pyNTM import Model


class TestRSVPLSPSetupBWFail(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.model = Model.load_model_file('model_test_topology.csv')
        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.model.update_simulation()

        # Add additional traffic from A to D
        self.model.add_demand('A', 'D', 100, 'demand_a_d_3')

        self.model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        self.lsp_a_d_3 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        self.model.update_simulation()

    def test_setup_bw_fail(self):
        # One of the 3 LSPs will not set up
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)

    def test_lsp_res_bw(self):
        # The 2 LSPs that do set up will have setup_bandwidth of 125
        self.assertEqual([self.lsp_a_d_1.reserved_bandwidth,
                          self.lsp_a_d_2.reserved_bandwidth,
                          self.lsp_a_d_3.reserved_bandwidth].count(125.0), 2)

    # def test_setup_bw_fail(self):
    #     model = Model.load_model_file('model_test_topology.csv')
    #     lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
    #     lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
    #     lsp_f_e_1 = model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
    #     int_a_b = model.get_interface_object('A-to-B', 'A')
    #     int_a_c = model.get_interface_object('A-to-C', 'A')
    #     # model.update_simulation()
    #
    #
    #     # Add additional traffic from A to D
    #     model.add_demand('A', 'D', 100, 'demand_a_d_3')
    #     # model.update_simulation()
    #
    #     # Add 3rd lsp from Node('A') to Node('D'); this LSP
    #     # will be the 3rd LSP signaled over two possible paths;
    #     # this LSP should cause one of the 3 to not signal
    #     model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
    #     model.update_simulation()
    #     lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
    #
    #     # One of the 3 LSPs will not set up
    #     self.assertEqual([lsp_a_d_1.reserved_bandwidth,
    #                      lsp_a_d_2.reserved_bandwidth,
    #                      lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)
    #
    #     # The 2 LSPs that do set up will have setup_bandwidth of 125
    #     self.assertEqual([lsp_a_d_1.reserved_bandwidth,
    #                      lsp_a_d_2.reserved_bandwidth,
    #                      lsp_a_d_3.reserved_bandwidth].count(125.0), 2)


# class TestRSVPLSPSetupBWAdjust(unittest.TestCase):
#     def test_reserved_bw(self):
#         model2 = Model.load_model_file('model_test_topology.csv')
#         lsp_a_d_1 = model2.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
#         lsp_a_d_2 = model2.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
#         lsp_f_e_1 = model2.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
#         int_a_b = model2.get_interface_object('A-to-B', 'A')
#         int_a_c = model2.get_interface_object('A-to-C', 'A')
#         # model2.update_simulation()
#
#         # Add additional traffic from A to D
#         model2.add_demand('A', 'D', 100, 'demand_a_d_3')
#         # model2.update_simulation()
#
#         # Add 3rd lsp from Node('A') to Node('D'); this LSP
#         # will be the 3rd LSP signaled over two possible paths;
#         # this LSP should cause one of the 3 to not signal
#         model2.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
#         model2.update_simulation()
#         lsp_a_d_3 = model2.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
#
#         # One of the 3 LSPs will not set up
#         self.assertEqual([lsp_a_d_1.reserved_bandwidth,
#                          lsp_a_d_2.reserved_bandwidth,
#                          lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)
#
#         # The 2 LSPs that do set up will have setup_bandwidth of 125
#         self.assertEqual([lsp_a_d_1.reserved_bandwidth,
#                           lsp_a_d_2.reserved_bandwidth,
#                           lsp_a_d_3.reserved_bandwidth].count(125.0), 2)
