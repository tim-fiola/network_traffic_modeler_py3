import unittest

from pyNTM import RSVP_LSP
from pyNTM import Model


class TestRSVPLSPInitial(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.model = Model()
        self.model.rsvp_lsp_objects = set()
        self.model.demand_objects = set()

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

        self.model.add_network_interfaces_from_list(int_list)
        self.model.add_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.model.add_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.model.add_rsvp_lsp('F', 'E', 'lsp_f_e_1')

        demands = [{'source': 'A', 'dest': 'D', 'traffic': 70, 'name': 'dmd_a_d_2'},
                   {'source': 'A', 'dest': 'D', 'traffic': 80, 'name': 'dmd_a_d_1'},
                   {'source': 'F', 'dest': 'E', 'traffic': 400, 'name': 'dmd_f_e_1'},
                   {'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'},
                   ]

        for demand in demands:
            self.model.add_demand(demand['source'], demand['dest'],
                                  demand['traffic'], demand['name'])

        self.model.update_simulation()

        self.lsp_a_d_1 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        self.lsp_a_d_2 = self.model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        self.lsp_f_e_1 = self.model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1')
        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.model.update_simulation()

    def test_lsp_instance(self):
        self.assertIsInstance(self.lsp_a_d_1, RSVP_LSP)

    def test_lsp_path_instance(self):
        self.assertIsInstance(self.lsp_a_d_1.path, dict)

    def test_lsp_effective_metric_value(self):
        self.assertEqual(40.0, self.lsp_a_d_1.effective_metric(self.model))

    def test_lsp_repr(self):
        self.assertEqual(repr(self.lsp_a_d_1), "RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_1')")

    def test_lsp_reserved_bw(self):
        self.assertEqual(self.lsp_a_d_1.reserved_bandwidth, 75.0)

    # lsp_a_d_1 and lsp_a_d_2 take different paths, so actual_metric values
    # should not be equal; one path actual_metric is 40, the other path's
    # actual metric is 60
    def test_lsp_actual_metrics(self):
        self.assertNotEqual(self.lsp_a_d_1.actual_metric(self.model),
                            self.lsp_a_d_2.actual_metric(self.model))
        self.assertIn(self.lsp_a_d_1.actual_metric(self.model), [40, 60])
        self.assertIn(self.lsp_a_d_2.actual_metric(self.model), [40, 60])

    # lsp_f_e_1 should not be routed because
    # 1. It is trying to initially signal
    # 2. It has a setup_bandwidth of 400
    # 3. There are no available paths to support that setup_bandwidth
    def test_lsp_setup_bandwidth_failure(self):
        self.assertEqual(self.lsp_f_e_1.path, 'Unrouted - setup_bandwidth')
        self.assertEqual(self.lsp_f_e_1.setup_bandwidth, 400.0)

    # Validate reserved and reservable bandwidth on int_a_b, int_a_c
    def test_reserved_bandwidth(self):
        self.assertEqual(self.int_a_b.reserved_bandwidth, 75.0)
        self.assertEqual(self.int_a_b.reservable_bandwidth, 50.0)

        self.assertEqual(self.int_a_c.reserved_bandwidth, 75.0)
        self.assertEqual(self.int_a_c.reservable_bandwidth, 75.0)
