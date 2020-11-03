import sys
sys.path.append('../')

import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc

from pyNTM import RSVP_LSP

from pprint import pprint

from pyNTM import FlexModel

def make_json_node(x, y, id, label, midpoint=False):
    """

    :param x: x-coordinate (or longitude) of node
    :param y: y-coordinate (or latitude) of node
    :param id: node identifier within code
    :param label: Node's displayed label on on layout
    :param midpoint: Is this a midpoint node?  True|False

    :return:
    """

    json_node = {}
    json_node['position'] = {'x': x, 'y': y}
    json_node['data'] = {'id': id, 'label': label, 'group': ''}

    if midpoint:
        json_node['data']['group'] = 'midpoint'

    return json_node


def make_json_edge(source_id, target_id, label, utilization, util_ranges):
    """
    {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
              'utilization': 'failed'}}

    """

    group = None

    if utilization == 'Int is down':
        group = 'failed'
    elif utilization >= 100:
        group = util_ranges['100+']
    else:
        for range in util_ranges.keys():
            try:
                lower = int(range.split('-')[0])
                upper = int(range.split('-')[1])

                if utilization >= lower and utilization <= upper:
                    group = util_ranges[range]
                    break
            except (ValueError, IndexError):
                pass

    json_edge = {
                    'data': {'source': source_id, 'target': target_id, "group": group,
                             'label': label, 'utilization': utilization}
                 }

    return json_edge


util_ranges = {'0-24': 'royalblue',
               '25-49': 'green',
               '50-74': 'yellow',
               '75-89': 'orangered',
               '90-99': 'darkred',
               '100+': 'darkviolet',
               'failed': 'grey'}

# Make the Parallel_Link_Model
model = FlexModel.load_model_file('model_test_topology_multidigraph.csv')
model.update_simulation()
print()


def create_elements(model, group_midpoints=True):
    """

    :param model: pyNTM Model object
    :param group_midpoints: True|False.  Group all circuit midpoints that have common nodes.  This
    is helpful if you have multiple circuits between common nodes.  It will collapse the midpoint
    nodes for all the circuits into a common midpoint node.

    :return: element data (nodes, edges) for graphing in dash_cytoscape
    """

    edges = []
    nodes = []
    for ckt in model.circuit_objects:
        int_a = ckt.interface_a
        int_b = ckt.interface_b
        node_a = int_a.node_object
        node_b = int_b.node_object
        node_a_y = node_a.lat
        node_a_x = node_a.lon
        node_b_y = node_b.lat
        node_b_x = node_b.lon

        try:
            ckt_id = int_a.circuit_id
        except (AttributeError, ValueError):
            ckt_id = "circuit_{}-{}".format(node_a.name, node_b.name)

        midpoint_x = sum([node_a_x, node_b_x]) / 2
        midpoint_y = sum([node_a_y, node_b_y]) / 2

        # Create the midpoint node between the endpoints
        if group_midpoints:
            midpoint_label = 'midpoint-{}-{}'.format(node_a.name, node_b.name)
        else:
            midpoint_label = 'midpoint-{}'.format(ckt_id)
        new_node = make_json_node(midpoint_x, midpoint_y, midpoint_label, midpoint_label, midpoint=True)
        nodes.append(new_node)
        # Create each end node
        nodes.append(make_json_node(node_a.lon, node_a.lat, node_a.name, node_a.name))
        nodes.append(make_json_node(node_b.lon, node_b.lat, node_b.name, node_b.name))

        # Create the edges
        # {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
        #           'utilization': 'failed'}}

        # Make edges with midpoints
        edges.append(make_json_edge(node_a.name, midpoint_label, ckt_id, int_a.utilization, util_ranges))
        edges.append(make_json_edge(node_b.name, midpoint_label, ckt_id, int_b.utilization, util_ranges))
    elements = nodes + edges

    return elements


elements = create_elements(model)

default_stylesheet = [
    {
        "selector": 'edge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "curve-style": "bezier",
            'label': "data(label)",
            'line-color': "data(group)",
            "font-size": "9px",
            "opacity": 0.4
        }
    },
    {
        "selector": "edge[group=\"failed\"]",
        "style": {
            "line-color": "#808080",
            "curve-style": "bezier",
            'label': "data(label)",
            'line-style': 'dashed'
        }
    },
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            'background-color': 'lightgrey',
            "font-size": "9px",
            "text-halign": 'center',
            'text-valign': 'center',
            'text-wrap': 'wrap',
            'width': '20px',
            'height': '20px',
            'border-width': 1,
            'border-color': 'dimgrey'
        }
    },
    {
        "selector": 'node[group=\"failed\"]',
        "style": {
            'text-color': '#FF0000',
            'shape': 'rectangle',
            'label': "data(label)",
            'background-color': 'red'

        }
    },
    {
        "selector": 'node[group=\"midpoint\"]',
        "style": {
            'label': "data(label)",
            'shape': 'rectangle',
            'width': '10px',
            'height': '10px'
        }
    },
]

util_display_options = []
for util_range, color in util_ranges.items():
    util_display_options.append({'label': util_range, 'value': color})


styles = {
    'container': {
        'position': 'fixed',
        'display': 'flex',
        'flex-direction': 'column',
        'height': '95vh',
        'width': '100%',
    },
    'cy-container': {
        'flex': '1',
        'position': 'relative'
    },
    'cytoscape': {
        'position': 'absolute',
        'width': '100%',
        'height': '100%',
        'z-index': 999
    },
    'tab': {'height': 'calc(98vh - 80px)'}
}

app = dash.Dash(__name__)

app.layout = html.Div(style=styles['container'], children=[

    html.Div(className='eight columns', style=styles['cy-container'], children=[
        cyto.Cytoscape(
            id='cytoscape-prototypes',
            layout={'name': 'preset'},
            style=styles['cytoscape'],
            elements=elements,
            stylesheet=default_stylesheet,
            responsive=True
        ),
        html.P(id='cytoscape-mouseoverEdgeData-output'),
        ]),
        html.Div(className='four columns', children=[
            dcc.Tabs(id='tabs', children=[
                dcc.Tab(label='Utilization Visualization Dropdown', children=[
                    dcc.Dropdown(
                        id='utilization-dropdown-callback', options=util_display_options,
                        value=[entry['value'] for entry in util_display_options],
                        multi=True,
                    )
                ]),

                dcc.Tab(label='Demand Paths', children=[
                    dcc.Dropdown(
                        id='demand-source-callback', options=[node.name for node in model.node_objects]
                    ),
                    dcc.Dropdown(
                        id='demand-destination-callback', options=[node.name for node in model.node_objects]
                    ),
                ])
           ]),
        ])
])


# Display info about edge user hovers over
@app.callback(Output('cytoscape-mouseoverEdgeData-output', 'children'),
              [Input('cytoscape-prototypes', 'mouseoverEdgeData')])
def displayTapEdgeData(data):
    if data:
        msg = "Source: {}, Dest: {}, utilization {}%".format(data['source'], data['target'], data['utilization'])
        return msg


# Need to select interfaces that have utilization ranges selected in values from dropdown
@app.callback(Output('cytoscape-prototypes', 'stylesheet'), [Input('utilization-dropdown-callback', 'value')])
def update_stylesheet(edges_to_highlight):
    new_style = []
    for color in edges_to_highlight:
        new_entry = {
            "selector": "edge[group=\"{}\"]".format(color),
            "style": {
                "opacity": 1.0
            }
        }

        new_style.append(new_entry)

    return default_stylesheet + new_style

@app.callback(Output('cytoscape-prototypes', 'stylesheet'),
              [Input('demand-source-callback', 'value'), ['demand-destination-callback', 'value']])
def highlight_demand_paths(source, destination):
    # Find the demands that match the source and destination
    dmds = []
    for demand in model.demand_objects:
        if (demand.source_node_object.name == source and
                demand.dest_node_object.name == destination):
            dmds.append(demand)

    # Find edges that match the Interfaces in each path in dmd_path_modified
    edges_to_highlight = []

    # Find the demand paths for each demand
    for dmd in dmds:
        dmd_path = dmd.path
        dmd_path_modified = []  # Will hold the final paths that only have Interfaces
        for path in dmd_path:
            for hop in dmd_path:
                if isinstance(hop, RSVP_LSP):
                    for lsp_hop in hop:
                        dmd_path_modified.append(hop)
                else:
                    dmd_path_modified.append(hop)

        dmd_path_modified.append(path)

        for path in dmd_path_modified:
            for interface in path:
                # Get edge with matching interface source and ckt id (label)
                edge_to_get = [element for element in elements if
                               element['data']['source'] == interface.source_node_object.name and
                               element['data']['label'] == interface.circuit_id]
                edges_to_highlight.append(edge_to_get)

    # Modify the stylesheet for edges_to_highlight











app.run_server(debug=True)
