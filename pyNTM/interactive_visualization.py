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


class InteractiveVisualization(object):
    """
    Creates an interactive, browser-based visualization of a pyNTM Model.

    Each circuit is rendered as two directed edges (one per interface direction),
    color-coded by utilization. Nodes are draggable so the user can rearrange
    the topology for clarity.

    Basic usage::

        from pyNTM import PerformanceModel
        from pyNTM.interactive_visualization import InteractiveVisualization

        model = PerformanceModel.load_model_file('model.csv')
        model.update_simulation()

        vis = InteractiveVisualization(model)
        vis.create_visualization()          # opens in browser
        # or
        vis.create_visualization('my_network.html')  # saves to file
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
                    "color": "#eeeeee",
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
            })

            # Edge for int_b direction: node_b -> node_a
            color_b = self._get_utilization_color(int_b.utilization)
            edges.append({
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
            })

        return edges

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
        """Build HTML for the utilization color legend."""
        items = ""
        for _, color, label in self.util_ranges:
            items += (
                "<div style='display:flex;align-items:center;margin:3px 0;'>"
                "<div style='width:30px;height:4px;background:{color};"
                "margin-right:8px;border-radius:2px;'></div>"
                "<span>{label}</span></div>"
            ).format(color=color, label=label)

        # Add failed
        items += (
            "<div style='display:flex;align-items:center;margin:3px 0;'>"
            "<div style='width:30px;height:4px;background:{color};"
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

        return _HTML_TEMPLATE.format(
            nodes_json=nodes_json,
            edges_json=edges_json,
            legend_html=legend_html,
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
  body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; overflow: hidden; }}

  #network-container {{
    width: 100vw;
    height: 100vh;
  }}

  #legend {{
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(30, 30, 50, 0.92);
    border: 1px solid #444;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    z-index: 10;
    backdrop-filter: blur(6px);
  }}
  #legend h3 {{
    margin-bottom: 8px;
    font-size: 14px;
    color: #ccc;
    border-bottom: 1px solid #444;
    padding-bottom: 4px;
  }}

  #controls {{
    position: absolute;
    top: 12px;
    right: 12px;
    background: rgba(30, 30, 50, 0.92);
    border: 1px solid #444;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    z-index: 10;
    backdrop-filter: blur(6px);
  }}
  #controls h3 {{
    margin-bottom: 8px;
    font-size: 14px;
    color: #ccc;
    border-bottom: 1px solid #444;
    padding-bottom: 4px;
  }}
  #controls label {{
    display: block;
    margin: 6px 0;
    cursor: pointer;
  }}
  #controls button {{
    margin-top: 8px;
    padding: 5px 12px;
    background: #334;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }}
  #controls button:hover {{ background: #445; }}

  #info-panel {{
    position: absolute;
    bottom: 12px;
    left: 12px;
    background: rgba(30, 30, 50, 0.92);
    border: 1px solid #444;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    z-index: 10;
    max-width: 500px;
    backdrop-filter: blur(6px);
    display: none;
  }}
  #info-panel h3 {{
    margin-bottom: 6px;
    font-size: 14px;
    color: #ccc;
  }}
  #info-panel table {{
    border-collapse: collapse;
    width: 100%;
  }}
  #info-panel td {{
    padding: 2px 10px 2px 0;
  }}
  #info-panel .label-cell {{
    color: #999;
  }}
</style>
</head>
<body>

<div id="network-container"></div>

<div id="legend">
  <h3>Utilization</h3>
  {legend_html}
</div>

<div id="controls">
  <h3>Controls</h3>
  <label><input type="checkbox" id="toggle-physics"> Enable physics</label>
  <label><input type="checkbox" id="toggle-labels" checked> Show edge arrows</label>
  <button id="btn-fit">Fit to screen</button>
  <button id="btn-reset">Reset positions</button>
</div>

<div id="info-panel">
  <h3 id="info-title"></h3>
  <div id="info-body"></div>
</div>

<script>
(function() {{
  var nodesData = {nodes_json};
  var edgesData = {edges_json};

  var nodes = new vis.DataSet(nodesData);
  var edges = new vis.DataSet(edgesData);

  var container = document.getElementById('network-container');
  var data = {{ nodes: nodes, edges: edges }};

  var options = {{
    physics: {{
      enabled: false
    }},
    interaction: {{
      hover: true,
      tooltipDelay: 150,
      zoomView: true,
      dragView: true,
      dragNodes: true,
      multiselect: true
    }},
    edges: {{
      font: {{ size: 10, color: '#999', face: 'arial' }},
      smooth: {{
        type: 'curvedCW',
        roundness: 0.2
      }},
      hoverWidth: 1.5
    }},
    nodes: {{
      font: {{ color: '#eeeeee' }}
    }}
  }};

  var network = new vis.Network(container, data, options);

  // Store original positions for reset
  var originalPositions = {{}};
  nodesData.forEach(function(n) {{
    originalPositions[n.id] = {{ x: n.x, y: n.y }};
  }});

  // --- Controls ---
  document.getElementById('toggle-physics').addEventListener('change', function() {{
    network.setOptions({{ physics: {{ enabled: this.checked }} }});
  }});

  document.getElementById('toggle-labels').addEventListener('change', function() {{
    var show = this.checked;
    var updates = [];
    edgesData.forEach(function(e, i) {{
      updates.push({{
        id: i + 1,
        arrows: {{ to: {{ enabled: show, scaleFactor: 0.8 }} }}
      }});
    }});
    // vis.js auto-assigns numeric IDs starting from 1
    edges.forEach(function(e) {{
      edges.update({{ id: e.id, arrows: {{ to: {{ enabled: show, scaleFactor: 0.8 }} }} }});
    }});
  }});

  document.getElementById('btn-fit').addEventListener('click', function() {{
    network.fit({{ animation: {{ duration: 400, easingFunction: 'easeInOutQuad' }} }});
  }});

  document.getElementById('btn-reset').addEventListener('click', function() {{
    var updates = [];
    for (var id in originalPositions) {{
      updates.push({{ id: id, x: originalPositions[id].x, y: originalPositions[id].y }});
    }}
    nodes.update(updates);
    network.fit({{ animation: {{ duration: 400, easingFunction: 'easeInOutQuad' }} }});
  }});

  // --- Info Panel on click ---
  var infoPanel = document.getElementById('info-panel');
  var infoTitle = document.getElementById('info-title');
  var infoBody = document.getElementById('info-body');

  network.on('click', function(params) {{
    if (params.nodes.length > 0) {{
      var nodeId = params.nodes[0];
      var node = nodes.get(nodeId);
      infoTitle.textContent = 'Node: ' + node.label;
      infoBody.innerText = node.title || '';
      infoPanel.style.display = 'block';
    }} else if (params.edges.length > 0) {{
      var edgeId = params.edges[0];
      var edge = edges.get(edgeId);
      infoTitle.textContent = 'Interface';
      infoBody.innerText = edge.title || '';
      infoPanel.style.display = 'block';
    }} else {{
      infoPanel.style.display = 'none';
    }}
  }});

  // Initial fit
  network.once('afterDrawing', function() {{
    network.fit({{ animation: false }});
  }});
}})();
</script>
</body>
</html>
"""
