import unittest

from pyNTM import Interface
from pyNTM import Model
from pyNTM import Node


class TestRSVPLSPAddLSP(unittest.TestCase):

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

        # Fail an interface
        self.model.fail_interface('A-to-B', 'A')
        self.model.update_simulation()

        # Add additional traffic from A to D
        self.model.add_demand('A', 'D', 100, 'demand_a_d_3')
        self.model.update_simulation()

        # Unfail interface int_a_b
        self.model.unfail_interface('A-to-B', 'A')
        self.model.update_simulation()

    # Validate lsp_a_d_1 and lsp_a_d_2 reserve needed setup bandwidth
    # now that each has a path that allows it
    def test_lsp_bandwidth(self):
        self.assertEqual(self.lsp_a_d_1.reserved_bandwidth, 125.0)
        self.assertEqual(self.lsp_a_d_1.setup_bandwidth, 125.0)

        self.assertEqual(self.lsp_a_d_2.reserved_bandwidth, 125.0)
        self.assertEqual(self.lsp_a_d_2.setup_bandwidth, 125.0)

    # Test lsp_a_d_1 and lsp_a_d_2 are on separate paths
    def test_lsp_paths(self):
        # These 2 lists represent the ordered path lsp_a_d_1 and lsp_a_d_2
        # could take through the network
        possible_paths = [[Interface(name='A-to-B', cost=20, capacity=125, node_object=Node('A'),
                                     remote_node_object=Node('B'), address=2),
                           Interface(name='B-to-D', cost=20, capacity=125, node_object=Node('B'),
                                     remote_node_object=Node('D'), address=7)],
                          [Interface(name='A-to-C', cost=30, capacity=150, node_object=Node('A'),
                                     remote_node_object=Node('C'), address=3),
                           Interface(name='C-to-D', cost=30, capacity=150, node_object=Node('C'),
                                     remote_node_object=Node('D'), address=6)], ]

        possible_paths = [['A-to-B', 'B-to-D'],
                          ['A-to-C', 'C-to-D'],]
        # Validate lsp_a_d_1 and lsp_a_d_2 path interfaces
        # are in possible_paths
        self.assertIn([interface.name for interface in self.lsp_a_d_1.path['interfaces']], possible_paths)
        self.assertIn([interface.name for interface in self.lsp_a_d_2.path['interfaces']], possible_paths)
        # Validate lsp_a_d_1 and lsp_a_d_2 path interfaces are not the same
        self.assertNotEqual(self.lsp_a_d_1.path['interfaces'], self.lsp_a_d_2.path['interfaces'])

    # Test the reserved and reservable bandwidth on int_a_b, int_a_c
    def test_interface_bandwidth(self):
        self.assertEqual(self.int_a_b.reserved_bandwidth, 125.0)
        self.assertEqual(self.int_a_b.reservable_bandwidth, 0.0)
        self.assertEqual(self.int_a_c.reserved_bandwidth, 125.0)
        self.assertEqual(self.int_a_c.reservable_bandwidth, 25.0)
