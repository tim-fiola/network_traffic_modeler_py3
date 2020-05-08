import unittest

from pyNTM import Node
from pyNTM import Interface
from pyNTM import PerformanceModel
from pyNTM import ModelException


class TestInterface(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, circuit_id=1)

    # def test_repr(self):
    #     self.assertEqual(repr(self.interface_a), "Interface(name = 'inerfaceA-to-B', cost = 4, capacity = 100, node_object = Node('nodeA'), remote_node_object = Node('nodeB'), circuit_id = 1)")  # noqa E501

    def test_bad_int_cost(self):
        with self.assertRaises(ModelException) as context:
            (Interface('test_int', -5, 40, self.node_a, self.node_b, 50))
        self.assertTrue('Interface cost cannot be less than 1' in context.exception.args[0])

    def test_key(self):
        self.assertEqual(self.interface_a._key, ('inerfaceA-to-B', 'nodeA'))

    def test_eq(self):
        if self.interface_a == self.interface_a:
            self.assertTrue(True)

    def test_init_fail_neg_cost(self):
        with self.assertRaises(ModelException):
            Interface(name='inerfaceA-to-B', cost=-1, capacity=100,
                      node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)

    def test_init_fail_neg_capacity(self):
        with self.assertRaises(ModelException):
            Interface(name='inerfaceA-to-B', cost=4, capacity=-1,
                      node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)

    def test_reservable_bandwidth(self):
        self.assertEqual(100, self.interface_a.reservable_bandwidth)

    def test_int_fail(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')

        self.assertFalse(int_a_b.failed)

        int_a_b.fail_interface(model)
        model.update_simulation()

        self.assertEqual(int_a_b.get_remote_interface(model), int_b_a)
        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)

    def test_int_fail_2(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_a = model.get_interface_object('B-to-A', 'B')

        self.assertFalse(int_a_b.failed)
        self.assertFalse(int_b_a.failed)

        model.fail_node('A')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)
        self.assertTrue(int_b_a.failed)

    def test_demands_non_failed_int(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertTrue(int_a_b.demands(model) != [])

    def test_traffic_non_failed_int(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertTrue(int_a_b.traffic, 20)

    def test_demands_non_failed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')

        self.assertEqual(int_a_b.demands(model), [dmd_a_f_1])

    def test_traffic_failed_int(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertEqual(int_a_b.traffic, 'Down')

    def test_dmd_failed_int(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        self.assertEqual(int_a_b.demands(model), [])

    def test_bad_failed_status(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        with self.assertRaises(ModelException) as context:
            int_a_b.failed = 'hi'

        self.assertTrue('must be boolean value' in context.exception.args[0])

    def test_failed_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        model.fail_node('A')
        model.update_simulation()

        self.assertTrue(int_a_b.failed)

    def test_remote_int_failed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_b_a = model.get_interface_object('B-to-A', 'B')

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        self.assertTrue(int_b_a.failed)

    def test_unfail_int_failed_node(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        model.fail_node('A')
        model.update_simulation()

        err_msg = 'Local and/or remote node are failed; cannot have unfailed interface on failed node'

        with self.assertRaises(ModelException) as context:
            int_a_b.unfail_interface(model)

        self.assertTrue(err_msg in context.exception.args[0])

    # Test __ne__ method against Nodes with same names as nodes in the Model
    def test_not_equal(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')
        circuit_id = int_a_b.circuit_id

        node_a_prime = Node('A')
        node_b_prime = Node('B')

        int_a_b_prime = Interface('A-to-B', 20, 125, node_a_prime, node_b_prime, circuit_id)

        self.assertFalse(int_a_b == int_a_b_prime)

    def test_get_ckt(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')

        ckt1 = model.get_circuit_object_from_interface('A-to-B', 'A')
        ckt2 = int_a_b.get_circuit_object(model)

        self.assertEqual(ckt1, ckt2)

    def test_utilization(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')

        util = (20/125)*100

        self.assertEqual(int_a_b.utilization, util)

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()
        self.assertEqual(int_a_b.utilization, 'Int is down')

    def test_int_cost_not_integer(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        int_a_b = model.get_interface_object('A-to-B', 'A')

        err_msg = 'Interface cost must be integer'

        with self.assertRaises(ModelException) as context:
            int_a_b.cost = 14.1
        self.assertTrue(err_msg in context.exception.args[0])

    # Test failed interface makes circuit.failed=True
    def test_ckt_failure(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        model.fail_interface('A-to-B', 'A')
        model.update_simulation()

        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')

        self.assertTrue(ckt_1.failed(model))

    def test_ckt_non_failure(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()

        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')

        self.assertFalse(ckt_1.failed(model))

    def test_equality(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        ckt_1 = model.get_circuit_object_from_interface('A-to-B', 'A')
        int_a, int_b = ckt_1.get_circuit_interfaces(model)

        self.assertNotEqual(int_a, int_b)

    def test_reserved_bw_failed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')

        model.fail_node('A')
        model.update_simulation()

        int_a_b.failed = False
        self.assertTrue(int_a_b.failed)
        self.assertEqual(int_a_b.reserved_bandwidth, 0)

    def test_unfail_interface(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')
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
        model = PerformanceModel.load_model_file('test/model_test_topology.csv')
        model.update_simulation()
        int_a_b = model.get_interface_object('A-to-B', 'A')
        dmd_a_d_2 = model.get_demand_object('A', 'D', 'dmd_a_d_2')  # Rides an LSP
        dmd_a_d_1 = model.get_demand_object('A', 'D', 'dmd_a_d_1')  # Rides an LSP
        dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')  # IGP routed

        self.assertEqual(len(int_a_b.demands(model)), 3)
        self.assertTrue(dmd_a_d_1 in int_a_b.demands(model))
        self.assertTrue(dmd_a_d_2 in int_a_b.demands(model))
        self.assertTrue(dmd_a_f_1 in int_a_b.demands(model))
