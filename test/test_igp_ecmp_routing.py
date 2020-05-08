import unittest

from pyNTM import PerformanceModel


class TestIGPRouting(unittest.TestCase):
    def test_ecmp(self):

        model8 = PerformanceModel()
        model8.rsvp_lsp_objects = set([])
        model8.demand_objects = set([])

        int_list = [{'name': 'E-to-A', 'cost': 10, 'capacity': 300, 'node': 'E', 'remote_node': 'A', 'circuit_id': 1,
                     'failed': False},
                    {'name': 'C-to-D', 'cost': 30, 'capacity': 150, 'node': 'C', 'remote_node': 'D', 'circuit_id': 5,
                     'failed': False},
                    {'name': 'D-to-C', 'cost': 30, 'capacity': 150, 'node': 'D', 'remote_node': 'C', 'circuit_id': 5,
                     'failed': False},
                    {'name': 'A-to-E', 'cost': 10, 'capacity': 300, 'node': 'A', 'remote_node': 'E', 'circuit_id': 1,
                     'failed': False},
                    {'name': 'A-to-D', 'cost': 40, 'capacity': 20, 'node': 'A', 'remote_node': 'D', 'circuit_id': 2,
                     'failed': False},
                    {'name': 'D-to-A', 'cost': 40, 'capacity': 20, 'node': 'D', 'remote_node': 'A', 'circuit_id': 2,
                     'failed': False},
                    {'name': 'G-to-D', 'cost': 10, 'capacity': 100, 'node': 'G', 'remote_node': 'D', 'circuit_id': 7,
                     'failed': False},
                    {'name': 'C-to-A', 'cost': 30, 'capacity': 150, 'node': 'C', 'remote_node': 'A', 'circuit_id': 3,
                     'failed': False},
                    {'name': 'D-to-F', 'cost': 10, 'capacity': 300, 'node': 'D', 'remote_node': 'F', 'circuit_id': 6,
                     'failed': False},
                    {'name': 'F-to-D', 'cost': 10, 'capacity': 300, 'node': 'F', 'remote_node': 'D', 'circuit_id': 6,
                     'failed': False},
                    {'name': 'D-to-G', 'cost': 10, 'capacity': 100, 'node': 'D', 'remote_node': 'G', 'circuit_id': 7,
                     'failed': False},
                    {'name': 'B-to-A', 'cost': 20, 'capacity': 125, 'node': 'B', 'remote_node': 'A', 'circuit_id': 4,
                     'failed': False},
                    {'name': 'D-to-B', 'cost': 20, 'capacity': 125, 'node': 'D', 'remote_node': 'B', 'circuit_id': 8,
                     'failed': False},
                    {'name': 'B-to-G', 'cost': 10, 'capacity': 100, 'node': 'B', 'remote_node': 'G', 'circuit_id': 9,
                     'failed': False},
                    {'name': 'A-to-C', 'cost': 30, 'capacity': 150, 'node': 'A', 'remote_node': 'C', 'circuit_id': 3,
                     'failed': False},
                    {'name': 'B-to-D', 'cost': 20, 'capacity': 125, 'node': 'B', 'remote_node': 'D', 'circuit_id': 8,
                     'failed': False},
                    {'name': 'G-to-B', 'cost': 10, 'capacity': 100, 'node': 'G', 'remote_node': 'B', 'circuit_id': 9,
                     'failed': False},
                    {'name': 'A-to-B', 'cost': 20, 'capacity': 125, 'node': 'A', 'remote_node': 'B', 'circuit_id': 4,
                     'failed': False}]

        model8.add_network_interfaces_from_list(int_list)

        demands = [{'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'}, ]

        for demand in demands:
            model8.add_demand(demand['source'], demand['dest'],
                              demand['traffic'], demand['name'])

        int_a_b = model8.get_interface_object('A-to-B', 'A')
        int_b_d = model8.get_interface_object('B-to-D', 'B')
        int_b_g = model8.get_interface_object('B-to-G', 'B')
        int_g_d = model8.get_interface_object('G-to-D', 'G')
        int_d_f = model8.get_interface_object('D-to-F', 'D')
        int_a_c = model8.get_interface_object('A-to-C', 'A')
        int_c_d = model8.get_interface_object('C-to-D', 'C')
        int_a_d = model8.get_interface_object('A-to-D', 'A')

        model8.update_simulation()

        self.assertEqual(int_a_b.traffic, 20)
        self.assertEqual(int_b_d.traffic, 10)
        self.assertEqual(int_d_f.traffic, 40)
        self.assertEqual(int_b_g.traffic, 10)
        self.assertEqual(int_g_d.traffic, 10)
        self.assertEqual(int_a_c.traffic, 0)
        self.assertEqual(int_c_d.traffic, 0)
        self.assertEqual(int_a_d.traffic, 20)
