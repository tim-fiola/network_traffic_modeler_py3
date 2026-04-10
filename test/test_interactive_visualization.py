import unittest

from pyNTM import Model
from pyNTM.interactive_visualization import InteractiveVisualization


class TestVisualizationNoLSPs(unittest.TestCase):
    """Test visualization data builders with a model that has no LSPs."""

    @classmethod
    def setUpClass(cls):
        cls.model = Model.load_model_file("examples/sample_network_model_file.csv")
        cls.model.update_simulation()
        cls.vis = InteractiveVisualization(cls.model)

    def test_build_nodes(self):
        nodes = self.vis._build_nodes()
        node_ids = {n["id"] for n in nodes}
        self.assertEqual(len(nodes), len(self.model.node_objects))
        for node in self.model.node_objects:
            self.assertIn(node.name, node_ids)

    def test_build_edges(self):
        edges = self.vis._build_edges()
        # Two edges per circuit (one per direction)
        self.assertEqual(len(edges), len(self.model.circuit_objects) * 2)
        for edge in edges:
            self.assertIn("id", edge)
            self.assertIn("from", edge)
            self.assertIn("to", edge)
            self.assertIn("util_range", edge)
            self.assertIn("color", edge)

    def test_build_demands_data(self):
        demands = self.vis._build_demands_data()
        self.assertEqual(len(demands), len(self.model.demand_objects))
        for d in demands:
            self.assertIn("label", d)
            self.assertIn("traffic", d)
            self.assertIn("edge_ids", d)
            self.assertIn("node_ids", d)
            self.assertIn("interfaces", d)
            self.assertIn("lsps", d)

    def test_routed_demand_has_edges(self):
        demands = self.vis._build_demands_data()
        routed = [d for d in demands if d["edge_ids"]]
        self.assertTrue(len(routed) > 0)
        for d in routed:
            self.assertTrue(len(d["interfaces"]) > 0)
            for intf in d["interfaces"]:
                self.assertIn("label", intf)
                self.assertIn("node", intf)
                self.assertIn("edge_id", intf)

    def test_no_lsps(self):
        lsps = self.vis._build_lsps_data()
        self.assertEqual(len(lsps), 0)

    def test_build_interfaces_by_node(self):
        ibn = self.vis._build_interfaces_by_node()
        self.assertEqual(len(ibn), len(self.model.node_objects))
        for node_name, intfs in ibn.items():
            self.assertTrue(len(intfs) > 0)
            for intf in intfs:
                self.assertIn("name", intf)
                self.assertIn("remote", intf)
                self.assertIn("capacity", intf)
                self.assertIn("utilization", intf)
                self.assertIn("edge_id", intf)
                self.assertIn("demands", intf)
                self.assertIn("lsps", intf)

    def test_generate_html(self):
        html = self.vis._generate_html()
        self.assertIn("vis.Network", html)
        self.assertIn("vis.DataSet", html)
        self.assertIn("demand-select", html)
        self.assertIn("lsp-select", html)
        self.assertIn("node-select", html)


class TestVisualizationWithLSPs(unittest.TestCase):
    """Test visualization data builders with a model that has LSPs."""

    @classmethod
    def setUpClass(cls):
        cls.model = Model.load_model_file("examples/lsp_model_test_file.csv")
        cls.model.update_simulation()
        cls.vis = InteractiveVisualization(cls.model)

    def test_build_lsps_data(self):
        lsps = self.vis._build_lsps_data()
        self.assertEqual(len(lsps), len(self.model.rsvp_lsp_objects))
        for l in lsps:
            self.assertIn("label", l)
            self.assertIn("traffic", l)
            self.assertIn("reserved_bw", l)
            self.assertIn("edge_ids", l)
            self.assertIn("interfaces", l)
            self.assertIn("demands", l)

    def test_routed_lsp_has_data(self):
        lsps = self.vis._build_lsps_data()
        routed = [l for l in lsps if l["edge_ids"]]
        self.assertTrue(len(routed) > 0)
        for l in routed:
            self.assertTrue(l["traffic"] > 0)
            self.assertTrue(l["reserved_bw"] > 0)
            self.assertTrue(len(l["interfaces"]) > 0)
            for intf in l["interfaces"]:
                self.assertIn("label", intf)
                self.assertIn("node", intf)
                self.assertIn("edge_id", intf)

    def test_unrouted_lsp(self):
        lsps = self.vis._build_lsps_data()
        unrouted = [l for l in lsps if not l["edge_ids"]]
        self.assertTrue(len(unrouted) > 0)
        for l in unrouted:
            self.assertIn("Unrouted", l["label"])
            self.assertEqual(l["traffic"], 0)

    def test_demand_has_lsp_references(self):
        demands = self.vis._build_demands_data()
        demands_with_lsps = [d for d in demands if d["lsps"]]
        self.assertTrue(len(demands_with_lsps) > 0)
        for d in demands_with_lsps:
            for lsp_ref in d["lsps"]:
                self.assertIn("label", lsp_ref)
                self.assertIn("index", lsp_ref)
                self.assertGreaterEqual(lsp_ref["index"], 0)

    def test_lsp_has_demand_references(self):
        lsps = self.vis._build_lsps_data()
        lsps_with_demands = [l for l in lsps if l["demands"]]
        self.assertTrue(len(lsps_with_demands) > 0)
        for l in lsps_with_demands:
            for dmd_ref in l["demands"]:
                self.assertIn("label", dmd_ref)
                self.assertIn("index", dmd_ref)
                self.assertGreaterEqual(dmd_ref["index"], 0)

    def test_interfaces_by_node_has_lsps(self):
        ibn = self.vis._build_interfaces_by_node()
        found_lsp = False
        for node_name, intfs in ibn.items():
            for intf in intfs:
                if intf["lsps"]:
                    found_lsp = True
                    for lsp_ref in intf["lsps"]:
                        self.assertIn("label", lsp_ref)
                        self.assertIn("index", lsp_ref)
        self.assertTrue(found_lsp)

    def test_edge_ids_are_stable(self):
        """Edge IDs should match between edges and demand/LSP references."""
        edges = self.vis._build_edges()
        edge_id_set = {e["id"] for e in edges}
        demands = self.vis._build_demands_data()
        for d in demands:
            for eid in d["edge_ids"]:
                self.assertIn(eid, edge_id_set)
        lsps = self.vis._build_lsps_data()
        for l in lsps:
            for eid in l["edge_ids"]:
                self.assertIn(eid, edge_id_set)
