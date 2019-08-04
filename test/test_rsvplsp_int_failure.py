import unittest
from pyNTM import Model


class TestRSVPLSPIntFailure(unittest.TestCase):

    # This next section will see if the LSPs behave as expected
    # to the failed interface int_a_c
    # def test_fail_interface(self):
    #     self.assertTrue(self.int_a_b.failed)

    # Update the simulation and make sure both LSPs are on
    # interface int_a_c
    def test_lsp_failover(self):
        model1 = Model()
        model1.rsvp_lsp_objects = set()
        model1.demand_objects = set()

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

        model1.add_network_interfaces_from_list(int_list)
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        model1.fail_interface('A-to-B', 'A')
        int_a_b = model1.get_interface_object('A-to-B', 'A')
        int_a_c = model1.get_interface_object('A-to-C', 'A')

        demands = [{'source': 'A', 'dest': 'D', 'traffic': 70, 'name': 'dmd_a_d_2'},
                   {'source': 'A', 'dest': 'D', 'traffic': 80, 'name': 'dmd_a_d_1'},
                   {'source': 'F', 'dest': 'E', 'traffic': 400, 'name': 'dmd_f_e_1'},
                   {'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'},
                   ]

        for demand in demands:
            model1.add_demand(demand['source'], demand['dest'],
                              demand['traffic'], demand['name'])

        model1.update_simulation()

        self.assertTrue(int_a_b.failed)

        # int_a_b should not have any LSPs
        lsps_on_int_a_b = [lsp for lsp in int_a_b.lsps(model1)]
        self.assertTrue(len(lsps_on_int_a_b) == 0)

        # int_a_c should have lsp_a_d_1 and lsp_a_d_2
        lsp_names_on_int_a_c = [lsp.lsp_name for lsp in int_a_c.lsps(model1)]
        self.assertIn('lsp_a_d_1', lsp_names_on_int_a_c)
        self.assertIn('lsp_a_d_2', lsp_names_on_int_a_c)

        # reservable_bandwidth on int_a_c
        self.assertEqual(int_a_c.reserved_bandwidth, 150.0)
        self.assertEqual(int_a_c.reservable_bandwidth, 0.0)
