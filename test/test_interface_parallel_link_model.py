"""
Confirming behavior of Interface object in Parallel_Link_Model
"""

import unittest

from pyNTM import FlexModel
from pyNTM import ModelException


class TestInterface(unittest.TestCase):

    def test_demands_non_failed_int(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_b_e = model.get_interface_object('B-to-E', 'B')

        self.assertTrue(int_b_e.demands(model) != [])

    def test_traffic_non_failed_int(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_b_e = model.get_interface_object('B-to-E', 'B')

        self.assertTrue(int_b_e.traffic, 10)

    def test_demands_non_failed(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_b_e = model.get_interface_object('B-to-E', 'B')
        dmd_a_e_1 = model.get_demand_object('A', 'E', 'dmd_a_e_1')

        self.assertEqual(int_b_e.demands(model), [dmd_a_e_1])

    def test_traffic_failed_int(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertEqual(int_a_b.traffic, 'Down')

    def test_dmd_failed_int(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertTrue(len(int_a_b.demands(model)) != 0)

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        self.assertEqual(int_a_b.demands(model), [])

    def test_failed_node(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        model.fail_node('A')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)

    def test_remote_int_failed(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_b_a = model.get_interface_object('B-to-A', 'B')

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        self.assertTrue(int_b_a.failed)

    def test_unfail_int_failed_node(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        model.fail_node('A')
        model.update_simulation()

        err_msg = 'Local and/or remote node are failed; cannot have unfailed interface on failed node'

        with self.assertRaises(ModelException) as context:
            int_a_b.unfail_interface(model)

        self.assertTrue(err_msg in context.exception.args[0])

    def test_get_ckt(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')

        ckt1 = model.get_circuit_object_from_interface('A-to-B', 'A')
        ckt2 = int_a_b.get_circuit_object(model)

        self.assertEqual(ckt1, ckt2)

    def test_utilization(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        int_b_e = model.get_interface_object('B-to-E', 'B')

        util = (30/3/200)*100

        self.assertEqual(int_b_e.utilization, util)

        model.fail_interface('B-to-E', 'B')
        model.update_simulation()
        self.assertEqual(int_b_e.utilization, 'Int is down')

    # Test failed interface makes circuit.failed=True
    def test_ckt_failure(self):
        model = FlexModel.load_model_file('test/parallel_link_model_w_lsps.csv')
        model.update_simulation()

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')

        self.assertTrue(ckt_1.failed(model))

    def test_ckt_non_failure(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()

        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')

        self.assertFalse(ckt_1.failed(model))

    def test_equality(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()
        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')
        int_a, int_b = ckt_1.get_circuit_interfaces(model)

        self.assertNotEqual(int_a, int_b)

    def test_reserved_bw_failed(self):
        model = FlexModel.load_model_file('test/parallel_link_model_w_lsps.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertNotEqual(int_a_b.reserved_bandwidth, 0)

        model.fail_node('A')
        model.update_simulation()

        int_a_b.failed = False
        self.assertTrue(int_a_b.failed)
        self.assertEqual(int_a_b.reserved_bandwidth, 0)

    def test_unfail_interface(self):
        model = FlexModel.load_model_file('test/parallel_link_model_test_topology_igp_only.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        self.assertTrue(int_b_a.failed)
        self.assertTrue(int_a_b.failed)

        int_a_b.unfail_interface(model)
        model.update_simulation()
        self.assertFalse(int_a_b.failed)

    def test_demands_on_interface_via_lsps(self):
        model = FlexModel.load_model_file('test/parallel_link_model_w_lsps.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        dmd_a_b_1 = model.get_demand_object('A', 'B', 'dmd_a_b_1')  # Rides an LSP
        dmd_c_e_1 = model.get_demand_object('C', 'E', 'dmd_c_e_1')  # IGP routed
        dmd_a_e_1 = model.get_demand_object('A', 'E', 'dmd_a_e_1')  # IGP routed

        self.assertEqual(len(int_a_b.demands(model)), 3)
        self.assertTrue(dmd_a_b_1 in int_a_b.demands(model))
        self.assertTrue(dmd_c_e_1 in int_a_b.demands(model))
        self.assertTrue(dmd_a_e_1 in int_a_b.demands(model))
