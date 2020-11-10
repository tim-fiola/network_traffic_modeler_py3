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

def make_json_node(x, y, id, label, midpoint=False, neighbors=[]):
    """

    :param x: x-coordinate (or longitude) of node
    :param y: y-coordinate (or latitude) of node
    :param id: node identifier within code
    :param label: Node's displayed label on on layout
    :param midpoint: Is this a midpoint node?  True|False
    :param neighbors: directly connected nodes

    :return:
    """

    json_node = {}
    json_node['position'] = {'x': x, 'y': y}
    json_node['data'] = {'id': id, 'label': label, 'group': ''}

    if midpoint:
        json_node['data']['group'] = 'midpoint'
        if neighbors:
            json_node['data']['neighbors'] = neighbors

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
        new_node = make_json_node(midpoint_x, midpoint_y, midpoint_label, midpoint_label,
                                  midpoint=True, neighbors=[node_a.name, node_b.name])
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

midpoints = [element for element in elements if element['data']['group'] == 'midpoint']

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

# list of utilization ranges to display
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

styles_2 = {
    "content": {
        'width': '100%',
    },
    "right_menu": {
        'width': '25%',
        'position': 'absolute',
        'top': '0',
        'right': '0'
    },
    "top_content": {
        'height': '100px',
        'width': '100%',
        'position': 'relative',
        'top': '0',
        'right': '0'
    },
    "left_content": {
        "width": '85%',
        'position': 'absolute',
        'top': '0',
        'left': '0'
    }


}

# Check here for layout example: https://stackoverflow.com/questions/56175268/how-to-properly-add-style-to-my-dash-app

app = dash.Dash(__name__)

app.layout = html.Div(className='content', style=styles_2['content'], children=[

    html.Div(className='left_content', children=[
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
    html.Div(className='right_menu', style=styles_2['right_menu'], children=[
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
                    id='demand-source-callback', options=[{'label': node.name, 'value': node.name}
                                                          for node in model.node_objects]
                ),
                dcc.Dropdown(
                    id='demand-destination-callback', options=[{'label': node.name, 'value': node.name}
                                                               for node in model.node_objects]
                ),
            ])
       ]),
    ])
])


# Display info about edge user hovers over
@app.callback(Output('cytoscape-mouseoverEdgeData-output', 'children'),
              [Input('cytoscape-prototypes', 'mouseoverEdgeData')])
def display_tap_edge_data(data):
    if data:
        msg = "Source: {}, Dest: {}, ckt_id {}, utilization {}%".format(data['source'], data['target'],
                                                                        data['label'], data['utilization'])
        return msg


# Need to select interfaces that have utilization ranges selected in values from dropdown
@app.callback(Output('cytoscape-prototypes', 'stylesheet'),
              [Input('utilization-dropdown-callback', 'value'),
               Input('demand-source-callback', 'value'),
               Input('demand-destination-callback', 'value')])
def update_stylesheet(edges_to_highlight, source=None, destination=None):
    new_style = []

    # Utilization color for edges
    for color in edges_to_highlight:
        new_entry = {
            "selector": "edge[group=\"{}\"]".format(color),
            "style": {
                "opacity": 1.0
            }
        }

        new_style.append(new_entry)

    # Demand source and destination path visualization
    if source is not None and destination is not None:
        # Find the demands that match the source and destination
        try:
            dmds = model.parallel_demand_groups()['{}-{}'.format(source, destination)]
        except KeyError:
            return default_stylesheet + new_style

        # Find the demand paths for each demand
        interfaces_to_highlight = set()
        for dmd in dmds:
            dmd_path = dmd.path[:]
            for path in dmd_path:
                for hop in dmd_path:
                    if isinstance(hop, RSVP_LSP):
                        for lsp_hop in hop.path['interfaces']:
                            interfaces_to_highlight.add(lsp_hop)
                        dmd_path.remove(hop)
                    else:
                        for interface in hop:
                            interfaces_to_highlight.add(interface)

        for interface in interfaces_to_highlight:  # TODO - color nodes on path pink as well

            # Add the edge selectors
            new_entry = {
                "selector": "edge[label=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                       interface.node_object.name),
                "style": {
                    "width": '4',
                    'line-style': 'dashed',
                    'target-arrow-color': "pink",
                    'target-arrow-shape': 'triangle',
                    'mid-target-arrow-color': 'pink',
                    'mid-target-arrow-shape': 'triangle',
                    'source-arrow-color': "pink",
                    'source-arrow-shape': 'circle',
                }
            }

            new_style.append(new_entry)

            new_entry_2 = {
                "selector": "edge[label=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                       interface.remote_node_object.name),
                "style": {
                    "width": '4',
                    'line-style': 'dashed',
                    'source-arrow-color': "pink",
                    'source-arrow-shape': 'triangle',
                    'mid-source-arrow-color': 'pink',
                    'mid-source-arrow-shape': 'triangle',
                    'target-arrow-color': "pink",
                    'target-arrow-shape': 'circle',
                }
            }

            new_style.append(new_entry_2)

            # Add the node selectors
            new_entry_3 = {
                "selector": "node[id=\"{}\"]".format(interface.node_object.name),
                "style": {
                    'background-color': 'pink'
                }
            }

            new_style.append(new_entry_3)

            new_entry_4 = {
                "selector": "node[id=\"{}\"]".format(interface.remote_node_object.name),
                "style": {
                    'background-color': 'pink'
                }
            }

            new_style.append(new_entry_4)

    return default_stylesheet + new_style




# THIS DOES NOT WORK; CREATES ADDITIONAL EDGES THAT ARE SEPARATE FROM THE EXISTING EDGES
# @app.callback(Output('cytoscape-prototypes', 'elements'),
#               [Input('demand-source-callback', 'value'), Input('demand-destination-callback', 'value')])
# def highlight_demand_paths(source, destination):
#     # Find edges that match the Interfaces in each path in dmd_path_modified
#     interfaces_to_highlight = set()
#
#     if source is not None and destination is not None:
#         # Find the demands that match the source and destination
#         dmds = model.parallel_demand_groups()['{}-{}'.format(source, destination)]
#
#         # Find the demand paths for each demand
#         for dmd in dmds:
#             dmd_path = dmd.path[:]
#             for path in dmd_path:
#                 for hop in dmd_path:
#                     if isinstance(hop, RSVP_LSP):
#                         for lsp_hop in hop.path['interfaces']:
#                             interfaces_to_highlight.add(lsp_hop)
#                         dmd_path.remove(hop)
#                     else:
#                         for interface in hop:
#                             interfaces_to_highlight.add(interface)
#
#     pprint('interfaces_to_highlight:')
#     pprint(interfaces_to_highlight)
#     print()
#     print()
#
#     # Create new edges
#     elements_to_highlight = []
#     label = 'demand_path_{}-to-{}'.format(source, destination)
#     for entry in interfaces_to_highlight:
#         interface_source = entry.node_object.name
#         interface_destination = entry.remote_node_object.name
#
#         midpoint_nodes = [node for node in midpoints if
#                          node['data']['group']=='midpoint' and
#                          interface_source in node['data']['neighbors'] and
#                          interface_destination in node['data']['neighbors']]
#
#         print('midpoint_nodes =')
#         pprint(midpoint_nodes)
#
#         midpoint_node = midpoint_nodes[0]
#
#         print('midpoint_node = {}'.format(midpoint_node))  # Todo - debug
#
#         target = midpoint_node['data']['label']
#
#         new_edge_1 = {
#             'data': {
#                 'source': "{}".format(interface_source),
#                 'target': "{}".format(target),
#                 'label': label,
#                 'group': "path-info",
#                 "curve-style": "bezier",
#                 'width': '6',
#                 'line-style': 'dashed',
#                 'target-arrow-color': "pink",
#                 'target-arrow-shape': 'triangle',
#             }
#         }
#
#         new_edge_2 = {
#             'data': {
#                 'source': "{}".format(entry.remote_node_object.name),
#                 'target': "{}".format(target),
#                 'label': label,
#                 'group': "path-info",
#                 "curve-style": "bezier",
#                 'width': '6',
#                 'line-style': 'dashed',
#                 'target-arrow-color': "pink",
#                 'target-arrow-shape': 'triangle',
#             }
#         }
#
#
#         elements_to_highlight.append(new_edge_1)
#         elements_to_highlight.append(new_edge_2)
#
#     return elements + elements_to_highlight

app.run_server(debug=True)
