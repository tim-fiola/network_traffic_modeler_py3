import unittest

from pyNTM import PerformanceModel


class TestRSVPLSPConfigSetupBW(unittest.TestCase):

    def test_config_setup_bw_model_load(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        self.assertEqual(model.__repr__(), 'PerformanceModel(Interfaces: 18, Nodes: 7, Demands: 4, RSVP_LSPs: 4)')

    def test_lsp_setup_bw(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        self.assertEqual(lsp_a_d_1.setup_bandwidth, 50)
        self.assertEqual(lsp_a_d_1.setup_bandwidth, lsp_a_d_2.setup_bandwidth)
        self.assertEqual(lsp_a_d_3.setup_bandwidth, 1)

    def test_lsp_traffic(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        self.assertEqual(lsp_a_d_1.traffic_on_lsp(model), 50)
        self.assertEqual(lsp_a_d_2.traffic_on_lsp(model), 50)
        self.assertEqual(lsp_a_d_3.traffic_on_lsp(model), 50)

    def test_lsp_res_bw(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        self.assertEqual(lsp_a_d_1.reserved_bandwidth, 50)
        self.assertEqual(lsp_a_d_2.reserved_bandwidth, 50)
        self.assertEqual(lsp_a_d_3.reserved_bandwidth, 1)

    def test_lsp_dmds(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
        lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        dmd_a_d_1 = model.get_demand_object('A', 'D', 'dmd_a_d_1')
        dmd_a_d_2 = model.get_demand_object('A', 'D', 'dmd_a_d_2')

        self.assertEqual(set(lsp_a_d_1.demands_on_lsp(model)), set([dmd_a_d_1, dmd_a_d_2]))
        self.assertEqual(set(lsp_a_d_2.demands_on_lsp(model)), set([dmd_a_d_1, dmd_a_d_2]))
        self.assertEqual(set(lsp_a_d_3.demands_on_lsp(model)), set([dmd_a_d_1, dmd_a_d_2]))

    # lsp_a_d_3 should always take the single hop path of Interface('A-to-D', 'A') since
    # it only has a setup_bw of 1.  That interface has a capacity of 40 so lsp_a_d_1/2
    # can't take it since they have a setup_bw of 50
    def test_shortest_path(self):
        model = PerformanceModel.load_model_file('test/lsp_configured_setup_bw_model.csv')
        model.update_simulation()
        lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

        self.assertEqual(len(lsp_a_d_3.path['interfaces']), 1)
        self.assertEqual(lsp_a_d_3.path['interfaces'][0]._key, ('A-to-D', 'A'))
