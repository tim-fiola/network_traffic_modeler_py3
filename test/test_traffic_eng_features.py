"""
Test suite for traffic engineering features: rsvp_enabled and
percent_reservable_bandwidth Interface attributes
"""

import unittest

from pyNTM import PerformanceModel
from pyNTM import FlexModel


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = PerformanceModel.load_model_file('test/traffic_eng_test_model.csv')
        self.model.update_simulation()

        self.int_a_b = self.model.get_interface_object('A-to-B', 'A')
        self.int_a_c = self.model.get_interface_object('A-to-C', 'A')
        self.int_a_d = self.model.get_interface_object('A-to-D', 'A')

        self.lsp_a_e_1 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
        self.lsp_a_e_2 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
        self.lsp_a_e_3 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')

        self.dmd_a_e_1 = self.model.get_demand_object('A', 'E', 'dmd_a_e_1')
        self.dmd_a_e_2 = self.model.get_demand_object('A', 'E', 'dmd_a_e_2')

    def test_rsvp_enabled(self):
        """
        Interface that is not rsvp_enabled will have no LSPs
        """
        self.assertFalse(self.int_a_d.rsvp_enabled)
        self.assertEqual(len(self.int_a_d.lsps(self.model)), 0)

    def test_percent_reservable_bandwidth(self):
        """
        Interface with percent_reservable_bandwidth only allows
        for 50% of capacity to be used by LSPs
        """

        self.assertEqual(self.int_a_b.percent_reservable_bandwidth, 50)

        reserved_bw = self.int_a_b.reserved_bandwidth
        reservable_bw = self.int_a_b.reservable_bandwidth
        capacity = self.int_a_b.capacity

        self.assertEqual((reservable_bw + reserved_bw), capacity/2)


class TestParallelLinkModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.model = FlexModel.load_model_file('test/traffic_eng_test_parallel_link_model.csv')
        self.model.update_simulation()

        self.int_a_b_1 = self.model.get_interface_object('A-to-B_1', 'A')
        self.int_a_b_2 = self.model.get_interface_object('A-to-B_2', 'A')
        self.int_a_b_3 = self.model.get_interface_object('A-to-B_3', 'A')

        self.lsp_a_e_1 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
        self.lsp_a_e_2 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
        self.lsp_a_e_3 = self.model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')

        self.dmd_a_e_1 = self.model.get_demand_object('A', 'E', 'dmd_a_e_1')
        self.dmd_a_e_2 = self.model.get_demand_object('A', 'E', 'dmd_a_e_2')

    def test_rsvp_enabled(self):
        """
        Interface that is not rsvp_enabled will have no LSPs
        """
        self.assertFalse(self.int_a_b_3.rsvp_enabled)
        self.assertEqual(len(self.int_a_b_3.lsps(self.model)), 0)

    def test_percent_reservable_bandwidth(self):
        """
        Interface with percent_reservable_bandwidth only allows
        for 50% of capacity to be used by LSPs
        """

        self.assertEqual(self.int_a_b_1.percent_reservable_bandwidth, 50)

        reserved_bw = self.int_a_b_1.reserved_bandwidth
        reservable_bw = self.int_a_b_1.reservable_bandwidth
        capacity = self.int_a_b_1.capacity

        self.assertEqual((reservable_bw + reserved_bw), capacity/2)
