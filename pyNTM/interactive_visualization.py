"""
Interactive network visualization for pyNTM models.

Generates a self-contained HTML file using vis.js Network that allows
users to drag nodes, see per-direction utilization coloring on each
interface, and inspect interface details via tooltips.
"""

import json
import os
import webbrowser
import tempfile

from .rsvp import RSVP_LSP


class InteractiveVisualization(object):
    """
    Creates an interactive, browser-based visualization of a pyNTM Model.

    Each circuit is rendered as two directed edges (one per interface direction),
    color-coded by utilization. Nodes are draggable so the user can rearrange
    the topology for clarity.

    Basic usage::

        from pyNTM import Model

        model = Model.load_model_file('model.csv')
        model.update_simulation()
        model.visualize()          # opens in browser
        model.visualize('my_network.html')  # saves to file
    """

    def __init__(self, model):
        self.model = model

        # Spacing multiplier for lat/lon coordinates
        self.spacing_factor = 5

        # Utilization color thresholds: list of (upper_bound, color, label)
        # Checked in order; first match wins. None upper_bound = catch-all for 100%+
        self.util_ranges = [
            (25, "#4169E1", "0-24%"),     # Royal Blue
            (50, "#228B22", "25-49%"),     # Forest Green
            (75, "#FFD700", "50-74%"),     # Gold
            (90, "#FF4500", "75-89%"),     # Orange Red
            (100, "#8B0000", "90-99%"),    # Dark Red
            (None, "#9400D3", "100%+"),    # Dark Violet
        ]
        self.failed_color = "#696969"      # Dim Grey
        self.failed_label = "Failed"

        # Node styling
        self.node_color = "#90EE90"        # Light green
        self.node_failed_color = "#FF0000" # Red
        self.node_border_color = "#696969"
        self.node_size = 25
        self.node_font_size = 14

        # Edge styling
        self.edge_width = 3
        self.edge_arrow_scale = 0.8

        # Path highlight colors
        self.demand_highlight_color = "#FF69B4"  # Hot pink
        self.lsp_highlight_color = "#00FFFF"     # Cyan

    def _get_utilization_color(self, utilization):
        """Return the color for a given utilization percentage."""
        if utilization == "Int is down":
            return self.failed_color

        for upper, color, _ in self.util_ranges:
            if upper is None:
                return color
            if utilization < upper:
                return color

        # Fallback (shouldn't reach here)
        return self.util_ranges[-1][1]

    def _get_utilization_label(self, utilization):
        """Return the legend label for a given utilization percentage."""
        if utilization == "Int is down":
            return self.failed_label

        for upper, _, label in self.util_ranges:
            if upper is None:
                return label
            if utilization < upper:
                return label

        return self.util_ranges[-1][2]

    def _build_nodes(self):
        """Build vis.js node data from model nodes."""
        nodes = []
        seen = set()
        for node in self.model.node_objects:
            if node.name in seen:
                continue
            seen.add(node.name)

            x = node.lon * self.spacing_factor
            y = -node.lat * self.spacing_factor  # Invert y-axis like WeatherMap

            bg_color = self.node_failed_color if node.failed else self.node_color
            border_color = "#B73239" if node.failed else self.node_border_color
            shape = "diamond" if node.failed else "dot"

            nodes.append({
                "id": node.name,
                "label": node.name,
                "x": x,
                "y": y,
                "color": {
                    "background": bg_color,
                    "border": border_color,
                    "highlight": {
                        "background": bg_color,
                        "border": "#333333",
                    },
                },
                "shape": shape,
                "size": self.node_size,
                "font": {
                    "size": self.node_font_size,
                    "face": "arial",
                    "color": "#222222",
                    "vadjust": self.node_size + 8,
                },
                "borderWidth": 2,
                "title": self._node_tooltip(node),
            })
        return nodes

    def _node_tooltip(self, node):
        """Build plain-text tooltip for a node."""
        status = "FAILED" if node.failed else "Active"
        interfaces = node.interfaces(self.model)
        lines = ["{} ({})".format(node.name, status), ""]
        for intf in sorted(interfaces, key=lambda i: i.name):
            util = intf.utilization
            if util == "Int is down":
                util_str = "Down"
            else:
                util_str = "{:.1f}%".format(util)
            lines.append("  {} -> {}  cap: {}  util: {}".format(
                intf.name, intf.remote_node_object.name,
                intf.capacity, util_str,
            ))
        return "\n".join(lines)

    @staticmethod
    def _edge_id(interface):
        """Stable edge ID for an interface: 'intName__nodeName'."""
        return "{}__{}".format(interface.name, interface.node_object.name)

    def _build_edges(self):
        """
        Build vis.js edge data. Each circuit produces two directed edges,
        one per interface direction, each color-coded by its own utilization.
        """
        edges = []
        seen_circuits = set()

        for ckt in self.model.circuit_objects:
            int_a = ckt.interface_a
            int_b = ckt.interface_b
            node_a = int_a.node_object.name
            node_b = int_b.node_object.name

            # Avoid duplicate circuits
            ckt_key = frozenset([
                (int_a.name, node_a),
                (int_b.name, node_b),
            ])
            if ckt_key in seen_circuits:
                continue
            seen_circuits.add(ckt_key)

            # Edge for int_a direction: node_a -> node_b
            color_a = self._get_utilization_color(int_a.utilization)
            edges.append({
                "id": self._edge_id(int_a),
                "from": node_a,
                "to": node_b,
                "color": {"color": color_a, "highlight": color_a},
                "title": self._edge_tooltip(int_a),
                "width": self.edge_width,
                "arrows": {
                    "to": {"enabled": True, "scaleFactor": self.edge_arrow_scale}
                },
                "smooth": {"type": "curvedCW", "roundness": 0.2},
                "dashes": int_a.utilization == "Int is down",
                "util_range": self._get_utilization_label(int_a.utilization),
            })

            # Edge for int_b direction: node_b -> node_a
            color_b = self._get_utilization_color(int_b.utilization)
            edges.append({
                "id": self._edge_id(int_b),
                "from": node_b,
                "to": node_a,
                "color": {"color": color_b, "highlight": color_b},
                "title": self._edge_tooltip(int_b),
                "width": self.edge_width,
                "arrows": {
                    "to": {"enabled": True, "scaleFactor": self.edge_arrow_scale}
                },
                "smooth": {"type": "curvedCW", "roundness": 0.2},
                "dashes": int_b.utilization == "Int is down",
                "util_range": self._get_utilization_label(int_b.utilization),
            })

        return edges

    def _build_demands_data(self):
        """Build a list of demands with their path edge IDs and interface details."""
        demands = []
        for dmd in sorted(self.model.demand_objects,
                          key=lambda d: (d.source_node_object.name,
                                         d.dest_node_object.name, d.name)):
            if dmd.path == "Unrouted":
                demands.append({
                    "label": "{} -> {} ({}) [Unrouted]".format(
                        dmd.source_node_object.name,
                        dmd.dest_node_object.name, dmd.name),
                    "traffic": dmd.traffic,
                    "edge_ids": [],
                    "node_ids": [],
                    "interfaces": [],
                    "lsps": [],
                })
                continue

            edge_ids = set()
            node_ids = set()
            intf_details = []
            lsp_set = set()
            for path in dmd.path:
                for hop in path:
                    if isinstance(hop, RSVP_LSP):
                        lsp_set.add(hop)
                        if hop.path != "Unrouted":
                            for intf in hop.path["interfaces"]:
                                eid = self._edge_id(intf)
                                if eid not in edge_ids:
                                    intf_details.append({
                                        "label": "{} ({} -> {})".format(
                                            intf.name, intf.node_object.name,
                                            intf.remote_node_object.name),
                                        "node": intf.node_object.name,
                                        "edge_id": eid,
                                    })
                                edge_ids.add(eid)
                                node_ids.add(intf.node_object.name)
                                node_ids.add(intf.remote_node_object.name)
                    else:
                        eid = self._edge_id(hop)
                        if eid not in edge_ids:
                            intf_details.append({
                                "label": "{} ({} -> {})".format(
                                    hop.name, hop.node_object.name,
                                    hop.remote_node_object.name),
                                "node": hop.node_object.name,
                                "edge_id": eid,
                            })
                        edge_ids.add(eid)
                        node_ids.add(hop.node_object.name)
                        node_ids.add(hop.remote_node_object.name)

            lsp_details = []
            for lsp in sorted(lsp_set,
                              key=lambda l: (l.source_node_object.name,
                                             l.dest_node_object.name, l.lsp_name)):
                lsp_details.append({
                    "label": "{} -> {} ({})".format(
                        lsp.source_node_object.name,
                        lsp.dest_node_object.name, lsp.lsp_name),
                    "index": self._lsp_index(lsp),
                })

            demands.append({
                "label": "{} -> {} ({}, traffic={})".format(
                    dmd.source_node_object.name,
                    dmd.dest_node_object.name, dmd.name, dmd.traffic),
                "traffic": dmd.traffic,
                "edge_ids": sorted(edge_ids),
                "node_ids": sorted(node_ids),
                "interfaces": intf_details,
                "lsps": lsp_details,
            })
        return demands

    def _build_lsps_data(self):
        """Build a list of LSPs with their path edge IDs and details."""
        lsps = []
        for lsp in sorted(self.model.rsvp_lsp_objects,
                          key=lambda l: (l.source_node_object.name,
                                         l.dest_node_object.name, l.lsp_name)):
            if "Unrouted" in str(lsp.path):
                lsps.append({
                    "label": "{} -> {} ({}) [Unrouted]".format(
                        lsp.source_node_object.name,
                        lsp.dest_node_object.name, lsp.lsp_name),
                    "traffic": 0,
                    "reserved_bw": 0,
                    "edge_ids": [],
                    "node_ids": [],
                    "interfaces": [],
                    "demands": [],
                })
                continue

            edge_ids = []
            node_ids = set()
            intf_details = []
            for intf in lsp.path["interfaces"]:
                eid = self._edge_id(intf)
                edge_ids.append(eid)
                node_ids.add(intf.node_object.name)
                node_ids.add(intf.remote_node_object.name)
                intf_details.append({
                    "label": "{} ({} -> {})".format(
                        intf.name, intf.node_object.name,
                        intf.remote_node_object.name),
                    "node": intf.node_object.name,
                    "edge_id": eid,
                })

            traffic = lsp.traffic_on_lsp(self.model)
            res_bw = lsp.reserved_bandwidth
            if not isinstance(res_bw, (int, float)):
                res_bw = 0

            dmd_details = []
            for dmd in sorted(lsp.demands_on_lsp(self.model),
                              key=lambda d: (d.source_node_object.name,
                                             d.dest_node_object.name, d.name)):
                dmd_details.append({
                    "label": "{} -> {} ({})".format(
                        dmd.source_node_object.name,
                        dmd.dest_node_object.name, dmd.name),
                    "index": self._demand_index(dmd),
                })

            lsps.append({
                "label": "{} -> {} ({})".format(
                    lsp.source_node_object.name,
                    lsp.dest_node_object.name, lsp.lsp_name),
                "traffic": round(traffic, 2) if isinstance(traffic, float) else traffic,
                "reserved_bw": round(res_bw, 2) if isinstance(res_bw, float) else res_bw,
                "edge_ids": edge_ids,
                "node_ids": sorted(node_ids),
                "interfaces": intf_details,
                "demands": dmd_details,
            })
        return lsps

    def _build_interfaces_by_node(self):
        """Build node -> interfaces mapping with demand/LSP lists per interface."""
        nodes_dict = {}
        for node in sorted(self.model.node_objects, key=lambda n: n.name):
            intfs = []
            for intf in sorted(node.interfaces(self.model), key=lambda i: i.name):
                util = intf.utilization
                if util == "Int is down":
                    util_str = "Down"
                else:
                    util_str = "{:.1f}%".format(util)

                # Demands on this interface
                dmd_labels = []
                for dmd in intf.demands(self.model):
                    dmd_labels.append({
                        "label": "{} -> {} ({})".format(
                            dmd.source_node_object.name,
                            dmd.dest_node_object.name, dmd.name),
                        "type": "demand",
                        "index": self._demand_index(dmd),
                    })

                # LSPs on this interface
                lsp_labels = []
                for lsp in intf.lsps(self.model):
                    lsp_labels.append({
                        "label": "{} -> {} ({})".format(
                            lsp.source_node_object.name,
                            lsp.dest_node_object.name, lsp.lsp_name),
                        "type": "lsp",
                        "index": self._lsp_index(lsp),
                    })

                intfs.append({
                    "name": intf.name,
                    "remote": intf.remote_node_object.name,
                    "capacity": intf.capacity,
                    "utilization": util_str,
                    "edge_id": self._edge_id(intf),
                    "demands": dmd_labels,
                    "lsps": lsp_labels,
                })
            nodes_dict[node.name] = intfs
        return nodes_dict

    def _demand_index(self, dmd):
        """Return the index of a demand in the sorted demand list."""
        sorted_dmds = sorted(self.model.demand_objects,
                             key=lambda d: (d.source_node_object.name,
                                            d.dest_node_object.name, d.name))
        for i, d in enumerate(sorted_dmds):
            if d is dmd:
                return i
        return -1

    def _lsp_index(self, lsp):
        """Return the index of an LSP in the sorted LSP list."""
        sorted_lsps = sorted(self.model.rsvp_lsp_objects,
                             key=lambda l: (l.source_node_object.name,
                                            l.dest_node_object.name, l.lsp_name))
        for i, l in enumerate(sorted_lsps):
            if l is lsp:
                return i
        return -1

    def _edge_tooltip(self, interface):
        """Build plain-text tooltip for an interface edge."""
        util = interface.utilization
        if util == "Int is down":
            util_str = "Down"
        else:
            util_str = "{:.1f}%".format(util)

        return (
            "{name}\n"
            "From: {src}\n"
            "To: {dst}\n"
            "Capacity: {capacity}\n"
            "Utilization: {util}"
        ).format(
            name=interface.name,
            src=interface.node_object.name,
            dst=interface.remote_node_object.name,
            capacity=interface.capacity,
            util=util_str,
        )

    def _build_legend_html(self):
        """Build HTML for the utilization color legend with clickable toggles."""
        items = ""
        for _, color, label in self.util_ranges:
            items += (
                "<div class='legend-item' data-range='{label}' "
                "style='display:flex;align-items:center;margin:3px 0;cursor:pointer;'>"
                "<div style='width:30px;height:4px;background:{color};"
                "margin-right:8px;border-radius:2px;'></div>"
                "<span>{label}</span></div>"
            ).format(color=color, label=label)

        # Add failed
        items += (
            "<div class='legend-item' data-range='{label}' "
            "style='display:flex;align-items:center;margin:3px 0;cursor:pointer;'>"
            "<div style='width:30px;height:4px;"
            "margin-right:8px;border-radius:2px;"
            "border-top:2px dashed {color};background:none;'></div>"
            "<span>{label}</span></div>"
        ).format(color=self.failed_color, label=self.failed_label)

        return items

    def _generate_html(self):
        """Generate the complete self-contained HTML visualization."""
        nodes_json = json.dumps(self._build_nodes())
        edges_json = json.dumps(self._build_edges())
        legend_html = self._build_legend_html()
        demands_json = json.dumps(self._build_demands_data())
        lsps_json = json.dumps(self._build_lsps_data())
        interfaces_by_node_json = json.dumps(self._build_interfaces_by_node())

        return _HTML_TEMPLATE.format(
            nodes_json=nodes_json,
            edges_json=edges_json,
            legend_html=legend_html,
            demands_json=demands_json,
            lsps_json=lsps_json,
            interfaces_by_node_json=interfaces_by_node_json,
            demand_highlight_color=self.demand_highlight_color,
            lsp_highlight_color=self.lsp_highlight_color,
        )

    def create_visualization(self, output_file=None, open_browser=True):
        """
        Generate the interactive visualization and optionally open it.

        :param output_file: Path to save the HTML file. If None, a temporary
            file is created.
        :param open_browser: If True, open the file in the default browser.
        :return: Path to the generated HTML file.
        """
        html_content = self._generate_html()

        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix=".html", prefix="pyNTM_vis_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            output_file = os.path.abspath(output_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

        print("Interactive visualization saved to: {}".format(output_file))

        if open_browser:
            webbrowser.open("file://" + output_file)

        return output_file


# ---------------------------------------------------------------------------
# Self-contained HTML template with vis.js loaded from CDN
# ---------------------------------------------------------------------------
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>pyNTM Interactive Network Visualization</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Arial, sans-serif; background: #d2c6a5; color: #222; overflow: hidden; }}
  #network-container {{ position: absolute; top: 0; left: 0; bottom: 0; right: 340px; }}
  #sidebar {{
    position: absolute; top: 0; right: 0; bottom: 0; width: 340px;
    background: rgba(245,240,230,0.97); border-left: 1px solid #aaa;
    overflow-y: auto; padding: 10px 12px; font-size: 13px; z-index: 20;
  }}
  #sidebar h3 {{
    font-size: 13px; color: #333; border-bottom: 1px solid #aaa;
    padding-bottom: 3px; margin: 12px 0 6px 0;
  }}
  #sidebar h3:first-child {{ margin-top: 0; }}
  #sidebar select {{
    width: 100%; padding: 4px; margin: 3px 0 5px 0;
    background: #fff; color: #222; border: 1px solid #aaa; border-radius: 3px; font-size: 12px;
  }}
  #sidebar button {{
    padding: 3px 8px; background: #e8e4dc; color: #333;
    border: 1px solid #aaa; border-radius: 3px; cursor: pointer; font-size: 11px; margin: 2px 3px 2px 0;
  }}
  #sidebar button:hover {{ background: #d5d0c5; }}
  #sidebar label {{ display: block; margin: 4px 0; cursor: pointer; font-size: 12px; }}
  .detail-box {{
    margin-top: 4px; padding: 5px 7px; background: rgba(0,0,0,0.05);
    border-radius: 3px; font-size: 11px; max-height: 220px; overflow-y: auto; display: none;
  }}
  .detail-box .intf-line {{ margin: 1px 0; }}
  .obj-link {{ color: #1a5fa0; cursor: pointer; text-decoration: underline; }}
  .obj-link:hover {{ color: #0d3a6e; }}
  .intf-item {{ padding: 4px 0; border-bottom: 1px solid rgba(0,0,0,0.08); }}
  .intf-item:last-child {{ border-bottom: none; }}
  .intf-header {{ font-weight: bold; margin-bottom: 2px; }}
  .legend-item.disabled {{ opacity: 0.35; text-decoration: line-through; }}
  .intf-sub {{ margin-left: 8px; font-size: 11px; color: #555; }}
  #info-panel {{
    position: absolute; bottom: 12px; left: 12px;
    background: rgba(245,240,230,0.95); border: 1px solid #aaa;
    border-radius: 6px; padding: 10px 14px; font-size: 13px;
    z-index: 10; max-width: 500px; display: none;
  }}
  #info-panel h3 {{ margin-bottom: 4px; font-size: 14px; color: #333; }}
</style>
</head>
<body>
<div id="network-container"></div>
<div id="sidebar">
  <h3>Controls</h3>
  <label><input type="checkbox" id="toggle-physics"> Enable physics</label>
  <label><input type="checkbox" id="toggle-labels" checked> Show edge arrows</label>
  <button id="btn-fit">Fit to screen</button>
  <button id="btn-reset">Reset positions</button>

  <h3>Demands</h3>
  <select id="demand-select"><option value="">-- Select a demand --</option></select>
  <button id="btn-clear-demand">Clear</button>
  <div id="demand-info" class="detail-box"></div>

  <h3>RSVP LSPs</h3>
  <select id="lsp-select"><option value="">-- Select an LSP --</option></select>
  <button id="btn-clear-lsp">Clear</button>
  <div id="lsp-info" class="detail-box"></div>

  <h3>Interfaces by Node</h3>
  <select id="node-select"><option value="">-- Select a node --</option></select>
  <div id="intf-list" class="detail-box"></div>

  <h3>Utilization Legend</h3>
  {legend_html}
</div>

<div id="info-panel">
  <h3 id="info-title"></h3>
  <div id="info-body"></div>
</div>

<script>
(function() {{
  var nodesData = {nodes_json};
  var edgesData = {edges_json};
  var demandsData = {demands_json};
  var lspsData = {lsps_json};
  var interfacesByNode = {interfaces_by_node_json};

  var DEMAND_COLOR = '{demand_highlight_color}';
  var LSP_COLOR = '{lsp_highlight_color}';

  var nodes = new vis.DataSet(nodesData);
  var edges = new vis.DataSet(edgesData);
  var container = document.getElementById('network-container');
  var network = new vis.Network(container, {{ nodes: nodes, edges: edges }}, {{
    physics: {{ enabled: false }},
    interaction: {{ hover: true, tooltipDelay: 150, zoomView: true, zoomSpeed: 0.3, dragView: true, dragNodes: true }},
    edges: {{ font: {{ size: 10, color: '#999', face: 'arial' }}, smooth: {{ type: 'curvedCW', roundness: 0.2 }}, hoverWidth: 1.5 }},
    nodes: {{ font: {{ color: '#222222' }} }}
  }});

  // --- Store originals ---
  var origEdge = {{}}, origNode = {{}}, origPos = {{}};
  edgesData.forEach(function(e) {{ origEdge[e.id] = {{ color: e.color, width: e.width, dashes: e.dashes || false, util_range: e.util_range }}; }});
  var hiddenRanges = {{}};
  nodesData.forEach(function(n) {{
    origNode[n.id] = {{ color: JSON.parse(JSON.stringify(n.color)), borderWidth: n.borderWidth }};
    origPos[n.id] = {{ x: n.x, y: n.y }};
  }});

  // --- Populate dropdowns ---
  var demandSelect = document.getElementById('demand-select');
  var lspSelect = document.getElementById('lsp-select');
  var nodeSelect = document.getElementById('node-select');

  demandsData.forEach(function(d, i) {{
    var o = document.createElement('option'); o.value = i; o.textContent = d.label; demandSelect.appendChild(o);
  }});
  lspsData.forEach(function(l, i) {{
    var o = document.createElement('option'); o.value = i; o.textContent = l.label; lspSelect.appendChild(o);
  }});
  Object.keys(interfacesByNode).sort().forEach(function(name) {{
    var o = document.createElement('option'); o.value = name; o.textContent = name; nodeSelect.appendChild(o);
  }});

  // --- Helpers ---
  function restoreAll() {{
    var eu = [], nu = [];
    edges.forEach(function(e) {{ var o = origEdge[e.id]; if(o) eu.push({{ id:e.id, color:o.color, width:o.width, dashes:o.dashes }}); }});
    nodes.forEach(function(n) {{ var o = origNode[n.id]; if(o) nu.push({{ id:n.id, color:JSON.parse(JSON.stringify(o.color)), borderWidth:o.borderWidth }}); }});
    edges.update(eu); nodes.update(nu);
  }}
  function dimAll() {{
    var u = [];
    edges.forEach(function(e) {{ u.push({{ id:e.id, color:{{ color:'rgba(160,150,130,0.45)', highlight:'rgba(160,150,130,0.45)' }}, width:1 }}); }});
    edges.update(u);
  }}
  function hlEdges(ids, color, w) {{
    var u = []; ids.forEach(function(id) {{ u.push({{ id:id, color:{{ color:color, highlight:color }}, width:w, dashes:false }}); }}); edges.update(u);
  }}
  function hlNodes(ids, bc) {{
    var u = []; ids.forEach(function(id) {{
      var o = origNode[id]; if(o) {{ var c = JSON.parse(JSON.stringify(o.color)); c.border = bc; u.push({{ id:id, color:c, borderWidth:4 }}); }}
    }}); nodes.update(u);
  }}
  function clearSelections() {{
    demandSelect.value = ''; lspSelect.value = ''; nodeSelect.value = '';
    document.getElementById('demand-info').style.display = 'none';
    document.getElementById('lsp-info').style.display = 'none';
    document.getElementById('intf-list').style.display = 'none';
    restoreAll();
  }}

  // --- Select demand by index ---
  function selectDemand(idx) {{
    clearSelections();
    demandSelect.value = idx;
    var d = demandsData[idx];
    var info = document.getElementById('demand-info');
    if (d.edge_ids.length === 0) {{
      info.innerHTML = '<b>Traffic:</b> ' + d.traffic + '<br>Demand is unrouted';
      info.style.display = 'block'; return;
    }}
    dimAll(); hlEdges(d.edge_ids, DEMAND_COLOR, 5); hlNodes(d.node_ids, DEMAND_COLOR);
    var html = '<b>Traffic:</b> ' + d.traffic;
    if (d.lsps && d.lsps.length > 0) {{
      html += '<br><b>LSPs:</b>';
      d.lsps.forEach(function(l) {{
        html += '<div class="intf-line">&bull; <span class="obj-link" data-action="lsp" data-index="' + l.index + '">' + l.label + '</span></div>';
      }});
    }}
    html += '<br><b>Interfaces:</b>';
    d.interfaces.forEach(function(intf) {{
      html += '<div class="intf-line">&bull; <span class="obj-link" data-action="intf" data-node="' + intf.node + '" data-edge="' + intf.edge_id + '">' + intf.label + '</span></div>';
    }});
    info.innerHTML = html; info.style.display = 'block';
  }}

  // --- Select LSP by index ---
  function selectLsp(idx) {{
    clearSelections();
    lspSelect.value = idx;
    var l = lspsData[idx];
    var info = document.getElementById('lsp-info');
    if (l.edge_ids.length === 0) {{
      info.textContent = 'LSP is unrouted';
      info.style.display = 'block'; return;
    }}
    dimAll(); hlEdges(l.edge_ids, LSP_COLOR, 5); hlNodes(l.node_ids, LSP_COLOR);
    var html = '<b>Traffic:</b> ' + l.traffic + '&emsp;<b>Reserved BW:</b> ' + l.reserved_bw;
    if (l.demands && l.demands.length > 0) {{
      html += '<br><b>Demands:</b>';
      l.demands.forEach(function(d) {{
        html += '<div class="intf-line">&bull; <span class="obj-link" data-action="demand" data-index="' + d.index + '">' + d.label + '</span></div>';
      }});
    }}
    html += '<br><b>Interfaces:</b>';
    l.interfaces.forEach(function(intf) {{
      html += '<div class="intf-line">&bull; <span class="obj-link" data-action="intf" data-node="' + intf.node + '" data-edge="' + intf.edge_id + '">' + intf.label + '</span></div>';
    }});
    info.innerHTML = html; info.style.display = 'block';
  }}

  // --- Demand / LSP dropdown handlers ---
  demandSelect.addEventListener('change', function() {{
    if (this.value === '') {{ clearSelections(); return; }}
    selectDemand(parseInt(this.value));
  }});
  document.getElementById('btn-clear-demand').addEventListener('click', clearSelections);

  lspSelect.addEventListener('change', function() {{
    if (this.value === '') {{ clearSelections(); return; }}
    selectLsp(parseInt(this.value));
  }});
  document.getElementById('btn-clear-lsp').addEventListener('click', clearSelections);

  // --- Interface by node ---
  nodeSelect.addEventListener('change', function() {{
    restoreAll();
    demandSelect.value = ''; lspSelect.value = '';
    document.getElementById('demand-info').style.display = 'none';
    document.getElementById('lsp-info').style.display = 'none';
    var listDiv = document.getElementById('intf-list');
    var nodeName = this.value;
    if (!nodeName) {{ listDiv.style.display = 'none'; return; }}
    var intfs = interfacesByNode[nodeName] || [];
    if (intfs.length === 0) {{ listDiv.textContent = 'No interfaces'; listDiv.style.display = 'block'; return; }}
    var html = '';
    intfs.forEach(function(intf) {{
      html += '<div class="intf-item">';
      html += '<div class="intf-header">' + intf.name + ' &rarr; ' + intf.remote + '</div>';
      html += '<div class="intf-sub">cap: ' + intf.capacity + '&emsp;util: ' + intf.utilization + '</div>';
      if (intf.demands.length > 0) {{
        html += '<div class="intf-sub"><b>Demands:</b></div>';
        intf.demands.forEach(function(d) {{
          html += '<div class="intf-sub"><span class="obj-link" data-action="demand" data-index="' + d.index + '">' + d.label + '</span></div>';
        }});
      }}
      if (intf.lsps.length > 0) {{
        html += '<div class="intf-sub"><b>LSPs:</b></div>';
        intf.lsps.forEach(function(l) {{
          html += '<div class="intf-sub"><span class="obj-link" data-action="lsp" data-index="' + l.index + '">' + l.label + '</span></div>';
        }});
      }}
      if (intf.demands.length === 0 && intf.lsps.length === 0) {{
        html += '<div class="intf-sub" style="color:#999;">No demands or LSPs</div>';
      }}
      html += '</div>';
    }});
    listDiv.innerHTML = html; listDiv.style.display = 'block';
  }});

  // --- Select interface: switch to Interfaces by Node view, highlight the edge ---
  function selectInterface(nodeName, edgeId) {{
    clearSelections();
    nodeSelect.value = nodeName;
    // Trigger the node select change to populate the interface list
    nodeSelect.dispatchEvent(new Event('change'));
    // Highlight just this one edge
    dimAll();
    hlEdges([edgeId], '#e67300', 5);
    hlNodes([nodeName], '#e67300');
  }}

  // Event delegation for clickable links in sidebar panels
  document.getElementById('sidebar').addEventListener('click', function(evt) {{
    // Clickable object links (demands, LSPs, interfaces)
    var el = evt.target.closest('.obj-link');
    if (el) {{
      var action = el.getAttribute('data-action');
      if (action === 'demand') selectDemand(parseInt(el.getAttribute('data-index')));
      else if (action === 'lsp') selectLsp(parseInt(el.getAttribute('data-index')));
      else if (action === 'intf') selectInterface(el.getAttribute('data-node'), el.getAttribute('data-edge'));
      return;
    }}
    // Legend toggle
    var legendEl = evt.target.closest('.legend-item');
    if (legendEl) {{
      var range = legendEl.getAttribute('data-range');
      if (hiddenRanges[range]) {{
        delete hiddenRanges[range];
        legendEl.classList.remove('disabled');
      }} else {{
        hiddenRanges[range] = true;
        legendEl.classList.add('disabled');
      }}
      // Apply: hide/show edges by util_range
      var updates = [];
      edges.forEach(function(e) {{
        var o = origEdge[e.id];
        if (o && hiddenRanges[o.util_range]) {{
          updates.push({{ id: e.id, hidden: true }});
        }} else {{
          updates.push({{ id: e.id, hidden: false }});
        }}
      }});
      edges.update(updates);
    }}
  }});

  // --- Controls ---
  document.getElementById('toggle-physics').addEventListener('change', function() {{
    network.setOptions({{ physics: {{ enabled: this.checked }} }});
  }});
  document.getElementById('toggle-labels').addEventListener('change', function() {{
    var show = this.checked;
    edges.forEach(function(e) {{ edges.update({{ id: e.id, arrows: {{ to: {{ enabled: show, scaleFactor: 0.8 }} }} }}); }});
  }});
  document.getElementById('btn-fit').addEventListener('click', function() {{
    network.fit({{ animation: {{ duration: 400, easingFunction: 'easeInOutQuad' }} }});
  }});
  document.getElementById('btn-reset').addEventListener('click', function() {{
    var u = []; for (var id in origPos) u.push({{ id: id, x: origPos[id].x, y: origPos[id].y }});
    nodes.update(u); network.fit({{ animation: {{ duration: 400, easingFunction: 'easeInOutQuad' }} }});
  }});

  // --- Info Panel on click ---
  var infoPanel = document.getElementById('info-panel');
  var infoTitle = document.getElementById('info-title');
  var infoBody = document.getElementById('info-body');
  network.on('click', function(params) {{
    if (params.nodes.length > 0) {{
      var n = nodes.get(params.nodes[0]);
      infoTitle.textContent = 'Node: ' + n.label;
      infoBody.innerText = n.title || '';
      infoPanel.style.display = 'block';
    }} else if (params.edges.length > 0) {{
      var e = edges.get(params.edges[0]);
      infoTitle.textContent = 'Interface';
      infoBody.innerText = e.title || '';
      infoPanel.style.display = 'block';
    }} else {{ infoPanel.style.display = 'none'; }}
  }});

  network.once('afterDrawing', function() {{ network.fit({{ animation: false }}); }});
}})();
</script>
</body>
</html>
"""
