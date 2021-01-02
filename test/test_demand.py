import unittest

from pyNTM import Node
from pyNTM import Demand
from pyNTM import FlexModel
from pyNTM import PerformanceModel
from pyNTM import Interface
from pyNTM import RSVP_LSP


class TestDemand(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.maxDiff = None
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=self.node_a, remote_node_object=self.node_b, circuit_id=1)
        self.interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=self.node_b, remote_node_object=self.node_a, circuit_id=1)
        self.rsvp_lsp_a = RSVP_LSP(source_node_object=self.node_a, dest_node_object=self.node_b, lsp_name='A-to-B')
        self.model = PerformanceModel(interface_objects=set([self.interface_a, self.interface_b]),
                                      node_objects=set([self.node_a, self.node_b]), demand_objects=set([]),
                                      rsvp_lsp_objects=set([self.rsvp_lsp_a]))
        self.demand = Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=10, name='A-to-B')

    def test_init_fail_neg_traffic(self):
        with self.assertRaises(ValueError):
            Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=-1, name='A-to-B')

    def test_repr(self):
        self.assertEqual(repr(self.demand), "Demand(source = nodeA, dest = nodeB, traffic = 10, name = 'A-to-B')")

    def test_key(self):
        self.assertEqual(self.demand._key, (Node('nodeA').name, Node('nodeB').name, 'A-to-B'))

    def test_demand_behavior(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        model.update_simulation()

        dmd_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')

        # Demand routes initially
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

        # Demand should not route if source node is down
        model.fail_node('A')
        model.update_simulation()
        self.assertEqual(dmd_a_f.path, 'Unrouted')

        # Demand should route when source node unfails
        model.unfail_node('A')
        model.update_simulation()
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

        # Demand should not route when dest node fails
        model.fail_node('F')
        model.update_simulation()
        self.assertEqual(dmd_a_f.path, 'Unrouted')

        # Demand should route when dest node unfails
        model.unfail_node('F')
        model.update_simulation()
        self.assertNotEqual(dmd_a_f.path, 'Unrouted')

    def test_unroutable_demand(self):
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        node_d = Node(name='nodeD')
        interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object=node_a, remote_node_object=node_b, circuit_id=1)
        interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                     node_object=node_b, remote_node_object=node_a, circuit_id=1)
        dmd_a_d = Demand(node_a, node_d, traffic=10)
        model = PerformanceModel(interface_objects=set([interface_a, interface_b]),
                                 node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_d]),
                                 rsvp_lsp_objects=set([]))
        model.update_simulation()

        self.assertEqual(dmd_a_d.path, 'Unrouted')

    def test_demand_on_lsp(self):
        """
        Ensure the demand takes an available LSP
        :return:
        """
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        node_d = Node(name='nodeD')
        interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                node_object=node_a, remote_node_object=node_b, circuit_id=1)
        interface_b = Interface(name='inerfaceB-to-A', cost=4, capacity=100,
                                node_object=node_b, remote_node_object=node_a, circuit_id=1)
        dmd_a_b = Demand(node_a, node_b, traffic=10)

        lsp_a_b = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b')

        model = PerformanceModel(interface_objects=set([interface_a, interface_b]),
                                 node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_b]),
                                 rsvp_lsp_objects=set([lsp_a_b]))

        model.update_simulation()

        self.assertEqual(str(dmd_a_b.path), "[[RSVP_LSP(source = nodeA, dest = nodeB, lsp_name = 'lsp_a_b')]]")

    def test_path_detail_perf_model_igp_routed(self):
        model = PerformanceModel.load_model_file('test/igp_routing_topology.csv')

        model.update_simulation()

        dmd_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')

        int_a_d = model.get_interface_object('A-to-D', 'A')
        int_d_f = model.get_interface_object('D-to-F', 'D')
        int_b_d = model.get_interface_object('B-to-D', 'B')
        int_a_b = model.get_interface_object('A-to-B', 'A')
        int_b_g = model.get_interface_object('B-to-G', 'B')
        int_g_d = model.get_interface_object('G-to-D', 'G')

        dmd_path_detail = {
            'path_0': {'interfaces': [int_a_d, int_d_f],
                       'path_traffic': 20.0,
                       'splits': {int_a_d: 2, int_d_f: 2}},
            'path_1': {'interfaces': [int_a_b, int_b_d, int_d_f],
                       'path_traffic': 10.0,
                       'splits': {int_b_d: 4, int_a_b: 2, int_d_f: 4}},
            'path_2': {'interfaces': [int_a_b, int_b_g, int_g_d, int_d_f],
                       'path_traffic': 10.0,
                       'splits': {int_a_b: 2, int_b_g: 4, int_g_d: 4, int_d_f: 4}}
        }

        self.assertEqual(dmd_a_f.path_detail, dmd_path_detail)

    def test_lsp_demand_path_detail_perf_model_lsp_routed(self):
        """
        Test demand path info for demand that takes LSPs
        :return:
        """
        model = PerformanceModel.load_model_file('test/traffic_eng_test_model.csv')

        model.update_simulation()

        dmd_a_e_1 = model.get_demand_object('A', 'E', 'dmd_a_e_1')

        lsp_a_e_1 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
        lsp_a_e_2 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
        lsp_a_e_3 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')

        # This is the expected path_detail for the demand, although the LSP component of
        # each path may vary
        # {'path_0': {'items': [RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_1')],
        #             'path_traffic': 26.6667,
        #             'splits': {RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_1'): 3}},
        #  'path_1': {'items': [RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_3')],
        #             'path_traffic': 26.6667,
        #             'splits': {RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_3'): 3}},
        #  'path_2': {'items': [RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_2')],
        #             'path_traffic': 26.6667,
        #             'splits': {RSVP_LSP(source=A, dest=E, lsp_name='lsp_a_e_2'): 3}}}

        # Confirm that the items are in the expected group of LSPs
        self.assertIn(dmd_a_e_1.path_detail['path_0']['items'], [[lsp_a_e_1], [lsp_a_e_2], [lsp_a_e_3]])
        self.assertIn(dmd_a_e_1.path_detail['path_1']['items'], [[lsp_a_e_1], [lsp_a_e_2], [lsp_a_e_3]])
        self.assertIn(dmd_a_e_1.path_detail['path_2']['items'], [[lsp_a_e_1], [lsp_a_e_2], [lsp_a_e_3]])

        # Confirm the items length is a single LSP
        self.assertEqual(len(dmd_a_e_1.path_detail['path_0']['items']), 1)
        self.assertEqual(len(dmd_a_e_1.path_detail['path_1']['items']), 1)
        self.assertEqual(len(dmd_a_e_1.path_detail['path_2']['items']), 1)

        # Confirm that the items in each path are unique to that path
        self.assertNotEqual(dmd_a_e_1.path_detail['path_0']['items'], dmd_a_e_1.path_detail['path_1']['items'])
        self.assertNotEqual(dmd_a_e_1.path_detail['path_1']['items'], dmd_a_e_1.path_detail['path_2']['items'])
        self.assertNotEqual(dmd_a_e_1.path_detail['path_2']['items'], dmd_a_e_1.path_detail['path_0']['items'])

        # Confirm path_traffic
        self.assertEqual([dmd_a_e_1.path_detail['path_0']['path_traffic'],
                          dmd_a_e_1.path_detail['path_1']['path_traffic'],
                          dmd_a_e_1.path_detail['path_2']['path_traffic']],
                         [26.6667, 26.6667, 26.6667])

        # Confirm the splits
        self.assertIn(3, dmd_a_e_1.path_detail['path_0']['splits'].values())
        self.assertIn(3, dmd_a_e_1.path_detail['path_1']['splits'].values())
        self.assertIn(3, dmd_a_e_1.path_detail['path_2']['splits'].values())

        # Confirm the 'items' in each path are the key in the 'splits' for the path
        self.assertTrue(dmd_a_e_1.path_detail['path_0']['items'][0] in dmd_a_e_1.path_detail['path_0']['splits'].keys())
        self.assertTrue(dmd_a_e_1.path_detail['path_1']['items'][0] in dmd_a_e_1.path_detail['path_1']['splits'].keys())
        self.assertTrue(dmd_a_e_1.path_detail['path_2']['items'][0] in dmd_a_e_1.path_detail['path_2']['splits'].keys())

    def test_lsp_demand_path_detail_flex_model_lsp_routed(self):
        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')
        model.update_simulation()

        dmd_d_f_1 = model.get_demand_object('D', 'F', 'dmd_d_f_1')
        lsp_d_f_1 = model.get_rsvp_lsp('D', 'F', 'lsp_d_f_1')

        expected_path = {'path_0': {'items': [lsp_d_f_1], 'path_traffic': 8.0}}

        self.assertEqual(dmd_d_f_1.path_detail, expected_path)

    def test_lsp_demand_path_detail_flex_model_lsp_and_igp_routed(self):
        model = FlexModel.load_model_file('test/igp_shortcuts_model_mult_lsps_in_path.csv')
        model.update_simulation()
        dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')

        int_a_g = model.get_interface_object('A-G', 'A')
        int_g_f = model.get_interface_object('G-F', 'G')
        int_a_b = model.get_interface_object('A-B', 'A')
        lsp_b_d_1 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_1')
        lsp_b_d_2 = model.get_rsvp_lsp('B', 'D', 'lsp_b_d_2')
        lsp_d_f_1 = model.get_rsvp_lsp('D', 'F', 'lsp_d_f_1')

        # dmd_a_f_1.path_detail should look something like this:
        # {'path_0': {'items': [
        #     Interface(name='A-G', cost=25, capacity=100, node_object=Node('A'), remote_node_object=Node('G'),
        #               circuit_id='6'),
        #     Interface(name='G-F', cost=25, capacity=100, node_object=Node('G'), remote_node_object=Node('F'),
        #               circuit_id='7')],
        #             'path_traffic': 5.0,
        #             'splits': {Interface(name='A-G', cost=25, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('G'), circuit_id='6'): 2,
        #                        Interface(name='G-F', cost=25, capacity=100, node_object=Node('G'),
        #                                  remote_node_object=Node('F'), circuit_id='7'): 2}},
        #  'path_1': {'items': [
        #      Interface(name='A-B', cost=10, capacity=100, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='1'),
        #      RSVP_LSP(source=B, dest=D, lsp_name='lsp_b_d_2'),
        #      RSVP_LSP(source=D, dest=F, lsp_name='lsp_d_f_1')],
        #             'path_traffic': 2.5,
        #             'splits': {Interface(name='A-B', cost=10, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='1'): 2,
        #                        RSVP_LSP(source=D, dest=F, lsp_name='lsp_d_f_1'): 4,
        #                        RSVP_LSP(source=B, dest=D, lsp_name='lsp_b_d_2'): 4}},
        #  'path_2': {'items': [
        #      Interface(name='A-B', cost=10, capacity=100, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='1'),
        #      RSVP_LSP(source=B, dest=D, lsp_name='lsp_b_d_1'),
        #      RSVP_LSP(source=D, dest=F, lsp_name='lsp_d_f_1')],
        #             'path_traffic': 2.5,
        #             'splits': {Interface(name='A-B', cost=10, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='1'): 2,
        #                        RSVP_LSP(source=B, dest=D, lsp_name='lsp_b_d_1'): 4,
        #                        RSVP_LSP(source=D, dest=F, lsp_name='lsp_d_f_1'): 4}}}

        dmd_pd = dmd_a_f_1.path_detail

        # Confirm 3 paths exist
        self.assertEqual(len(dmd_pd), 3)

        list_of_paths_items = [dmd_pd['path_0']['items'], dmd_pd['path_1']['items'], dmd_pd['path_2']['items']]

        # Confirm the path with the 2 interfaces
        self.assertIn([int_a_g, int_g_f], list_of_paths_items)

        # Confirm the 2 paths that differ only be lsp_b_d_1/lsp_b_d_2
        self.assertIn([int_a_b, lsp_b_d_1, lsp_d_f_1], list_of_paths_items)
        self.assertIn([int_a_b, lsp_b_d_2, lsp_d_f_1], list_of_paths_items)

        # Confirm the path A-G-F Interfaces only has 5 units of traffic
        five_traff_path = [path for path in dmd_a_f_1.path_detail if
                           dmd_a_f_1.path_detail[path]['items'] == [int_a_g, int_g_f]][0]

        self.assertEqual(dmd_pd[five_traff_path]['path_traffic'], 5.0)

        # Confirm the path [A-B, lsp_b_d_1, lsp_d_f_1] and [A-B, lsp_b_d_2, lsp_d_f_1] have 2.5 traffic units each
        lsp_path_1 = [path for path in dmd_a_f_1.path_detail if
                      dmd_a_f_1.path_detail[path]['items'] == [int_a_b, lsp_b_d_1, lsp_d_f_1]][0]
        lsp_path_2 = [path for path in dmd_a_f_1.path_detail if
                      dmd_a_f_1.path_detail[path]['items'] == [int_a_b, lsp_b_d_2, lsp_d_f_1]][0]

        self.assertEqual(dmd_pd[lsp_path_1]['path_traffic'], 2.5)
        self.assertEqual(dmd_pd[lsp_path_2]['path_traffic'], 2.5)

        # Confirm the split values of each path
        self.assertIn(2, set(dmd_pd[five_traff_path]['splits'].values()))
        self.assertEqual(1, len(set(dmd_pd[five_traff_path]['splits'].values())))

        self.assertEqual({2, 4}, set(dmd_pd[lsp_path_1]['splits'].values()))
        self.assertEqual({2, 4}, set(dmd_pd[lsp_path_2]['splits'].values()))
