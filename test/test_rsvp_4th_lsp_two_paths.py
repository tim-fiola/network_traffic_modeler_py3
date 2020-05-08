import unittest

from pyNTM import PerformanceModel

class TestRSVPLSPAddLSP4LSPs(unittest.TestCase):

    def test_validate_lsp_routing(self):
        """
        Test that all 4 LSPs between A and D route
        """

        model1 = PerformanceModel()
        model1.rsvp_lsp_objects = set([])
        model1.demand_objects = set([])

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

        model1.add_network_interfaces_from_list(int_list)
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
        model1.add_rsvp_lsp('A', 'D', 'lsp_a_d_4')

        demands = [{'source': 'A', 'dest': 'D', 'traffic': 100, 'name': 'dmd_a_d_3'},
                   {'source': 'A', 'dest': 'D', 'traffic': 70, 'name': 'dmd_a_d_2'},
                   {'source': 'A', 'dest': 'D', 'traffic': 80, 'name': 'dmd_a_d_1'},
                   {'source': 'F', 'dest': 'E', 'traffic': 400, 'name': 'dmd_f_e_1'},
                   {'source': 'A', 'dest': 'F', 'traffic': 40, 'name': 'dmd_a_f_1'},
                   ]

        for demand in demands:
            model1.add_demand(demand['source'], demand['dest'],
                              demand['traffic'], demand['name'])

        model1.update_simulation()

        # All the paths for each LSP from Node('A') to Node('D')
        paths = [lsp.path for lsp in model1.rsvp_lsp_objects if lsp.source_node_object.name == 'A' and
                 lsp.dest_node_object.name == 'D']

        # Ensure all LSPs route
        self.assertNotIn("Unrouted", paths)
