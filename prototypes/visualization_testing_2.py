import sys
sys.path.append('../')

import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc

from pyNTM import RSVP_LSP

import json

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


def make_json_edge(source_id, target_id, edge_name, capacity, circuit_id, utilization, util_ranges):
    """
    {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
              'utilization': 'failed', 'interface-name': edge_name}}

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
                             'circuit_id': circuit_id, 'utilization': utilization, 'interface-name': edge_name,
                             'capacity': capacity}
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
int_a_b = model.get_interface_object('A-to-B', 'A')


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
        int_a_name = int_a.name
        int_b_name = int_b.name
        node_a = int_a.node_object
        node_b = int_b.node_object
        node_a_y = node_a.lat
        node_a_x = node_a.lon
        node_b_y = node_b.lat
        node_b_x = node_b.lon
        capacity = int_a.capacity

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
        edges.append(make_json_edge(node_a.name, midpoint_label, int_a_name, capacity, ckt_id, int_a.utilization, util_ranges))
        edges.append(make_json_edge(node_b.name, midpoint_label, int_b_name, capacity, ckt_id, int_b.utilization, util_ranges))
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
            'label': "data(circuit_id)",
            'line-color': "data(group)",
            "font-size": "9px",
            "opacity": 0.4,
        }
    },
    {
        "selector": "edge[group=\"failed\"]",
        "style": {
            "line-color": "#808080",
            "curve-style": "bezier",
            'label': "data(circuit_id)",
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


# Fill in demand source and destination options
demand_sources = set()
demand_destinations= set()
for entry in model.parallel_demand_groups().keys():
    source, dest = entry.split('-')
    demand_sources.add(source)
    demand_destinations.add(dest)
demand_sources_list = list(demand_sources)
demand_destinations_list = list(demand_destinations)
demand_sources_list.sort()
demand_destinations_list.sort()

# Baseline selected interface to 'no int selected'
no_selected_interface_text = 'no int selected'
selected_interface = no_selected_interface_text

no_selected_demand_text = 'no demand selected'
selected_demand = no_selected_demand_text

styles_2 = {
    "content": {
        'width': '100%',
        'height': '100%',
    },
    "right_menu": {
        'width': '24%',
        'height': '60px',
        'position': 'absolute',
        'top': '0',
        'right': '0',
        'zIndex': 100,
        'fontFamily': 'arial'
    },
    "top_content": {
        'height': '100px',
        'width': '100%',
        'position': 'relative',
        'top': '0',
        'right': '0'
    },
    "left_content": {
        "width": '75%',
        'height': '100%',
        'position': 'absolute',
        'top': '0',
        'left': '0',
    },
    'cytoscape': {
        'position': 'absolute',
        'width': '75%',
        'height': '100%',
        'backgroundColor': '#D2B48C'
    },
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 115px)'}

}

# Check here for layout example: https://stackoverflow.com/questions/56175268/how-to-properly-add-style-to-my-dash-app

app = dash.Dash(__name__)

app.layout = html.Div(className='content', children=[
    html.Div(className='left_content', children=[
        cyto.Cytoscape(
            id='cytoscape-prototypes',
            layout={'name': 'preset'},
            style=styles_2['cytoscape'],
            elements=elements,
            stylesheet=default_stylesheet,
            responsive=True
        ),
    ]),
    html.Div(className='right_menu', style=styles_2['right_menu'], children=[
        html.P("Selected Interface:"),
        html.Pre(id='selected-interface-output'),
        html.P("Selected Demand:"),
        html.Pre(id='selected-demand-output'),
        dcc.Tabs(id='tabs', children=[
            dcc.Tab(label='Utilization Visualization Dropdown', children=[
                dcc.Dropdown(
                    id='utilization-dropdown-callback', options=util_display_options,
                    value=[entry['value'] for entry in util_display_options],
                    multi=True,
                )
            ]),
            dcc.Tab(label='Demand Interfaces', children=[
                html.Div(style=styles_2['tab'], children=[
                    dcc.Dropdown(
                        id='demand-source-callback', options=[{'label': source, 'value': source}
                                                              for source in demand_sources_list],
                    ),
                    dcc.Dropdown(
                        id='demand-destination-callback', options=[{'label': dest, 'value': dest}
                                                                   for dest in demand_destinations_list],
                    ),
                    dcc.RadioItems(
                        id='demand-path-interfaces',
                        labelStyle={'display': 'inline-block'},
                        style=styles_2['json-output']
                    )
                ]),
            ]),
            dcc.Tab(label='Interface Info', children=[
                html.Div(style=styles_2['tab'], children=[
                    dcc.RadioItems(
                        id='interface-demand-callback',
                        labelStyle={'display': 'inline-block'},
                        style=styles_2['json-output']
                    ),
                ]),
            ]),
       ]),
    ])
])


# Need to select interfaces that have utilization ranges selected in values from dropdown
@app.callback(Output('cytoscape-prototypes', 'stylesheet'),
              [Input(component_id='cytoscape-prototypes', component_property='selectedEdgeData'),
               Input('utilization-dropdown-callback', 'value'),
               Input('interface-demand-callback', 'value'),
               Input('selected-interface-output', 'children')])
def update_stylesheet(data, edges_to_highlight, selected_demand_info, selected_interface_info):
    """
    Updates stylesheet with style for edges_to_highlight that will change line type
    for the edge to dashed and add pink arrows and circles to the demand edges and
    also turn the nodes for the associated edges pink

    :param edges_to_highlight: list of edge elements to highlight
    :param source: demand source node name
    :param destination: demand destination node name
    :return: updated stylesheet with new elements that will reflect update colors for the
    edges_to_highlight
    """

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

    # If empty space is selected, remove demand path formatting
    # if not(data):
    #     return default_stylesheet + new_style

    # Demand source and destination path visualization
    if selected_demand_info is not None and \
            json.loads(selected_demand_info) != [{'source': '', 'dest': '', 'name': ''}] and\
            selected_demand_info != '':
        print("selected_demand_info line 365 = {}".format(selected_demand_info))
        demand_dict = json.loads(selected_demand_info)
        source = demand_dict['source']
        destination = demand_dict['dest']
        # Find the demands that match the source and destination
        try:
            dmds = model.parallel_demand_groups()['{}-{}'.format(source, destination)]
        except KeyError:
            return default_stylesheet + new_style

        # Find the interfaces on the demand paths for each demand
        interfaces_to_highlight = find_demand_interfaces(dmds)

        for interface in interfaces_to_highlight:
            # Add the edge selectors
            new_entry = {
                "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
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
                "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
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
                    'zIndex': -10
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

    # Selected edge differentiation
    if selected_interface_info != no_selected_interface_text:
        selected_interface_info = json.loads(selected_interface_info)
        # TODO - just add new edge wider to give an outline?
        # TODO - test the
        new_entry_5 = {
            "selector": "edge[source=\"{}\"][circuit_id=\"{}\"]".format(selected_interface_info['source'],
                                                                        selected_interface_info['circuit_id']),
            "style": {
                'line-style': 'dotted',
                'width': '6.5',
            }
        }

        new_style.append(new_entry_5)
    else:
        global selected_demand
        selected_demand = no_selected_demand_text
    return default_stylesheet + new_style

# TODO - Phase 1 goals
#  - DONE - highlight selected interface on map somehow
#  - Select an interface by either clicking on the map or selecting one from the Demand Paths list
#       - set selected_interface to the last value (either click or list selection)
#  - DONE - Space to display selected_interface value
#  - DONE - Space to display selected_demand value
#  - Tabs
#       - DONE - Utilization Visualization dropdown
#       - DONE - Demand Paths
#           - displays interfaces associated with selected_demand
#       - DONE - Interface Info
#           - displays Demands on selected_interface
#  - if empty space is clicked:
#       - DONE = set selected_demand back to no_selected_demand_text
#       - DONE - set selected_interface back to no_selected_interface_text
#       - DONE - display no_selected_interface_text in box that displays selected_interface
#       - DONE - display no_selected_demand_text in box that displays selected_demand
#       - DONE - clear demand options on Interface Info tab
#       - DONE - clear displayed interfaces on Demand Paths tab
#  =========================================================
#   Phase 2 goals:
#   - be able to select a Node
#   - display the selected Node
#   - have menu with checkboxes that allow user to select one or more:
#       - see demands that eminate from the node
#       - see demands that terminate on the node
#       - see demands that transit the node
#       - display the selected demands in a list
#       - display the selected demand paths on the map

# def that displays info about the selected edge and updates selected_interface
@app.callback(Output('selected-interface-output', 'children'),
              [Input('cytoscape-prototypes', 'selectedEdgeData')])
def displaySelectedEdgeData(data):
    """


    :param data: list consisting of a single dict containing info about the edge/interface
    :return: json string of a dict containing metadata about the selected edge
    """
    global selected_interface

    if data:
        data = data[0]
        end_target = [item for item in data['target'].split('-')[1:] if item != data['source']][0]
        int_info = {'source': data['source'], 'interface-name': data['interface-name'], 'dest': end_target, 'circuit_id':data['circuit_id'],
                    'utilization %': data['utilization']}
        selected_interface = json.dumps(int_info)
    else:
        selected_interface = no_selected_interface_text
    return selected_interface


# def that displays info about the selected demand and updates selected_demand
@app.callback(Output('selected-demand-output', 'children'),
              [Input('interface-demand-callback', 'value')])
def display_selected_demand_data(demand):

    global selected_demand
    print("demand line 512 = {}".format(demand))
    if demand:
        print("demand line 514 = {}".format(demand))

        # Convert text to json
        demand = json.loads(demand)

        if demand != [{'source': '', 'dest': '', 'name': ''}]:

            print("line 526 - demand = {}".format(demand))

            # Have to do this, otherwise json.dumps comes out with escapes (\) before all the double quotes

            demand_info = {'source': demand['source'], 'dest': demand['dest'], 'name': demand['name']}
            selected_demand = json.dumps(demand_info)
            return selected_demand
        else:
            selected_demand = no_selected_demand_text
        return selected_demand
    else:
        selected_demand = no_selected_demand_text
        return json.dumps({'label': no_selected_demand_text, 'value': ''})

# def that finds and displays demands on the selected interface
@app.callback(Output('interface-demand-callback', 'options'),
              [Input('selected-interface-output', 'children')])
def demands_on_interface(interface_info):
    """


    :param interface_info: serialized dict info about the interface
    :return: Demands on the interface
    """

    if interface_info != no_selected_interface_text:
        int_dict = json.loads(interface_info)
        interface = model.get_interface_object(int_dict['interface-name'], int_dict['source'])
        demands = interface.demands(model)
        if len(demands) == 0:
            return [{'label': 'no demands on interface', 'value': json.dumps([{'source': '', 'dest': '', 'name': ''}])}]

        demands_on_interface = []
        for demand in demands:
            # Return the demand's value as a dict with demand info (dmd_info)
            src = demand.source_node_object.name
            dest = demand.dest_node_object.name
            name = demand.name
            dmd_info = {'source': src, 'dest': dest, 'name': name}
            demands_on_interface.append({"label": demand.__repr__(), "value": json.dumps(dmd_info)})
        return demands_on_interface

    else:
        
        return [{"label": '', "value": ''}]


# def that finds and displays interfaces on selected_demand's path
@app.callback(Output('demand-path-interfaces', 'options'),
              [Input('selected-demand-output', 'children')])
def demand_interfaces(demand):
    global selected_demand
    if demand:
        if no_selected_demand_text not in demand:
            demand = json.loads(demand)
            dmd = model.get_demand_object(demand['source'], demand['dest'], demand['name'])
            dmd_ints = find_demand_interfaces([dmd])
            interfaces_list = []
            for interface in dmd_ints:
                source_node_name = interface.node_object.name
                dest_node_name = interface.remote_node_object.name
                name = interface.name
                circuit_id = interface.circuit_id
                cost = interface.cost
                int_dict = {'source': source_node_name, 'interface-name': name,
                            'dest': dest_node_name, 'circuit_id': circuit_id, 'cost': cost}
                int_info = {'label': interface.__repr__(), 'value': json.dumps(int_dict)}
                interfaces_list.append(int_info)

            return interfaces_list
        else:
            selected_demand = no_selected_demand_text
            return [{'label': selected_demand, 'value': selected_demand}]
    else:
        selected_demand = no_selected_demand_text
        return [{'label': selected_demand, 'value': selected_demand}]

# #### Utility Functions #### #
def find_demand_interfaces(dmds):
    """
    Finds interfaces for each demand in dmds.  If there
    are RSVP LSPs in path, the interfaces for that LSP path
    are added to the set of output interfaces

    :param dmds: iterable of demand objects
    :return: set of interfaces that any given demand in dmds transits
    """
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
    return interfaces_to_highlight

app.run_server(debug=True)


