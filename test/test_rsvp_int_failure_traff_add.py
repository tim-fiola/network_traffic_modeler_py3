import unittest

from pyNTM import Model


class TestRSVPLSPTraffAdd(unittest.TestCase):

    # @classmethod
    # def setUpClass(self):
    #     self.maxDiff = None
    #     self.model = Model.load_model_file('test/model_test_topology.csv')
    #     self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
    #     self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
    #     self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
    #     self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
    #     self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
    #     self.model.update_simulation()
    #
    #     # Fail an interface
    #     self.model.fail_interface('A-to-B', 'A')
    #     self.model.update_simulation()
    #
    #     # Add additional traffic from A to D
    #     self.model.add_demand('A', 'D', 100, 'demand_a_d_3')
    #     self.model.update_simulation()

    # Validate the reserved and setup bandwidths of lsp_a_d_1, lsp_a_d_2
    # One of the lsp_a_d_1 or lsp_a_d_2 LSPs will not be able to signal
    # with int_a_b failed; the one that does signal will reserved will
    # attempt to reserve 250/2 = 125 units of bandwidth
    def test_reserved_bandwidth(self):
        model = Model()
        model.rsvp_lsp_objects = set([])
        model.demand_objects = set([])

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

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        print("lsp_a_d_1.reserved_bandwidth = {}".format(lsp_a_d_1.reserved_bandwidth))
        print('int_a_c reservable_bandwidth = {}'.format(model.get_interface_object('A-to-C', 'A').reservable_bandwidth))
        self.assertIn(lsp_a_d_1.reserved_bandwidth, ['Unrouted - setup_bandwidth', 125.0])
        self.assertIn(lsp_a_d_2.reserved_bandwidth, ['Unrouted - setup_bandwidth', 125.0])
        self.assertNotEqual(lsp_a_d_1.reserved_bandwidth, lsp_a_d_2.reserved_bandwidth)

    # lsp_a_d_1/2 will each try to set up at 125.0 traffic units
    def test_setup_bandwidth(self):
        model = Model()
        model.rsvp_lsp_objects = set([])
        model.demand_objects = set([])

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

        model.update_simulation()

        self.assertEqual(lsp_a_d_1.setup_bandwidth, 125.0)
        self.assertEqual(lsp_a_d_2.setup_bandwidth, 125.0)

    # Validate the reserved and reservable bandwidth on int_a_c.
    # int_a_c has 150 capacity; one lsp_a_d_1/2 will take 125 of
    # that reserved_bandwidth; there will be a 25 unit remainder
    def test_int_bw(self):

        model = Model()
        model.rsvp_lsp_objects = set([])
        model.demand_objects = set([])

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

        demands = [{'source': 'A', 'dest': 'D', 'traffic': 100, 'name': 'dmd_a_d_3'},
                   {'source': 'A', 'dest': 'D', 'traffic': 70, 'name': 'dmd_a_d_2'},
                   {'source': 'A', 'dest': 'D', 'traffic': 80, 'name': 'dmd_a_d_1'},
                   {'source': 'F', 'dest': 'E', 'traffic': 400, 'name': 'dmd_f_e_1'},
                   {'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'},
                   ]

        for demand in demands:
            model.add_demand(demand['source'], demand['dest'],
                             demand['traffic'], demand['name'])

        int_a_c = model.get_interface_object('A-to-C', 'A')

        model.update_simulation()

        print("int_a_c reserved and reservable bw = {} and {}".format(int_a_c.reserved_bandwidth,
                                                                      int_a_c.reservable_bandwidth))
        self.assertEqual(int_a_c.reserved_bandwidth, 125.0)
        self.assertEqual(int_a_c.reservable_bandwidth, 25.0)
