import unittest

from pyNTM import Model


class TestRSVPLSPAddLSP3LSPs(unittest.TestCase):

    def test_reserved_bandwidth(self):
        """
        The 3rd LSP from Node('A') to Node('D') should cause one of
        the lsp_a_d_[1-3] to not signal.
        This LSP will be the 3rd LSP signaled over two possible paths,
        with the 2 existing LSPs each taking up the majority of
        reservable bandwidth on each path.
        """

        model = Model()
        model.rsvp_lsp_objects = set([])

        int_list = [{'name': 'E-to-A', 'cost': 10, 'capacity': 300, 'node': 'E', 'remote_node': 'A', 'address': 1,
                     'failed': False},
                    {'name': 'C-to-D', 'cost': 30, 'capacity': 150, 'node': 'C', 'remote_node': 'D', 'address': 5,
                     'failed': False},
                    {'name': 'D-to-C', 'cost': 30, 'capacity': 150, 'node': 'D', 'remote_node': 'C', 'address': 5,
                     'failed': False},
                    {'name': 'A-to-E', 'cost': 10, 'capacity': 300, 'node': 'A', 'remote_node': 'E', 'address': 1,
                     'failed': False},
                    {'name': 'A-to-D', 'cost': 40, 'capacity': 20, 'node': 'A', 'remote_node': 'D', 'address': 2,
                     'failed': False},
                    {'name': 'D-to-A', 'cost': 40, 'capacity': 20, 'node': 'D', 'remote_node': 'A', 'address': 2,
                     'failed': False},
                    {'name': 'G-to-D', 'cost': 10, 'capacity': 100, 'node': 'G', 'remote_node': 'D', 'address': 7,
                     'failed': False},
                    {'name': 'C-to-A', 'cost': 30, 'capacity': 150, 'node': 'C', 'remote_node': 'A', 'address': 3,
                     'failed': False},
                    {'name': 'D-to-F', 'cost': 10, 'capacity': 300, 'node': 'D', 'remote_node': 'F', 'address': 6,
                     'failed': False},
                    {'name': 'F-to-D', 'cost': 10, 'capacity': 300, 'node': 'F', 'remote_node': 'D', 'address': 6,
                     'failed': False},
                    {'name': 'D-to-G', 'cost': 10, 'capacity': 100, 'node': 'D', 'remote_node': 'G', 'address': 7,
                     'failed': False},
                    {'name': 'B-to-A', 'cost': 20, 'capacity': 125, 'node': 'B', 'remote_node': 'A', 'address': 4,
                     'failed': False},
                    {'name': 'D-to-B', 'cost': 20, 'capacity': 125, 'node': 'D', 'remote_node': 'B', 'address': 8,
                     'failed': False},
                    {'name': 'B-to-G', 'cost': 10, 'capacity': 100, 'node': 'B', 'remote_node': 'G', 'address': 9,
                     'failed': False},
                    {'name': 'A-to-C', 'cost': 30, 'capacity': 150, 'node': 'A', 'remote_node': 'C', 'address': 3,
                     'failed': False},
                    {'name': 'B-to-D', 'cost': 20, 'capacity': 125, 'node': 'B', 'remote_node': 'D', 'address': 8,
                     'failed': False},
                    {'name': 'G-to-B', 'cost': 10, 'capacity': 100, 'node': 'G', 'remote_node': 'B', 'address': 9,
                     'failed': False},
                    {'name': 'A-to-B', 'cost': 20, 'capacity': 125, 'node': 'A', 'remote_node': 'B', 'address': 4,
                     'failed': False}]

        model.add_network_interfaces_from_list(int_list)
        model.add_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        model.add_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        demands = [{'source': 'A', 'dest': 'D', 'traffic': 100, 'name': 'dmd_a_d_3'},
                   {'source': 'A', 'dest': 'D', 'traffic': 70, 'name': 'dmd_a_d_2'},
                   {'source': 'A', 'dest': 'D', 'traffic': 80, 'name': 'dmd_a_d_1'},
                   {'source': 'F', 'dest': 'E', 'traffic': 400, 'name': 'dmd_f_e_1'},
                   {'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'},
                   ]

        for demand in demands:
            model.add_demand(demand['source'], demand['dest'],
                             demand['traffic'], demand['name'])

        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        # lsp_f_e_1 = model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        # int_a_b = model.get_interface_object('A-to-B', 'A')
        # int_a_c = model.get_interface_object('A-to-C', 'A')

        model.update_simulation()

        # One of the 3 LSPs will not set up
        self.assertEqual([lsp_a_d_1.reserved_bandwidth,
                          lsp_a_d_2.reserved_bandwidth,
                          lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)

        # The 2 LSPs that do set up will have setup_bandwidth of 125
        self.assertEqual([lsp_a_d_1.reserved_bandwidth,
                          lsp_a_d_2.reserved_bandwidth,
                          lsp_a_d_3.reserved_bandwidth].count(125.0), 2)

    # def test_reserved_bandwidth(self):
    #     """
    #     The 3rd LSP from Node('A') to Node('D') should cause one of
    #     the lsp_a_d_[1-3] to not signal.
    #     This LSP will be the 3rd LSP signaled over two possible paths,
    #     with the 2 existing LSPs each taking up the majority of
    #     reservable bandwidth on each path.
    #     """
    #
    #     model = Model.load_model_file('test/model_test_topology.csv')
    #     lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
    #     lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
    #     lsp_f_e_1 = model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
    #     int_a_b = model.get_interface_object('A-to-B', 'A')
    #     int_a_c = model.get_interface_object('A-to-C', 'A')
    #
    #     # Fail an interface
    #     model.fail_interface('A-to-B', 'A')
    #
    #     # Add additional traffic from A to D
    #     model.add_demand('A', 'D', 100, 'demand_a_d_3')
    #
    #     # Unfail interface int_a_b
    #     model.unfail_interface('A-to-B', 'A')
    #
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
    #                       lsp_a_d_2.reserved_bandwidth,
    #                       lsp_a_d_3.reserved_bandwidth].count('Unrouted - setup_bandwidth'), 1)
    #
    #     # The 2 LSPs that do set up will have setup_bandwidth of 125
    #     self.assertEqual([lsp_a_d_1.reserved_bandwidth,
    #                       lsp_a_d_2.reserved_bandwidth,
    #                       lsp_a_d_3.reserved_bandwidth].count(125.0), 2)

    # def test_setup_bandwidth(self):
    #     """
    #     Each of the 3 LSPs from A to D will try to signal
    #     for (traffic/num_lsps) = 250/3 = 83.3.  The first two to signal will
    #     succeed.  The last one will fail due to lack of available bandwidth.
    #     When this happens, the traffic will then be split across 2 LSPs.
    #     So each LSP will try to resignal to carry more traffic (125 units).
    #     The LSP taking the A-to-B, B-to-D path
    #     """
