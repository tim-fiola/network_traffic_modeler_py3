import sys
sys.path.append('../')

import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc
import json

import dash_bootstrap_components as dbc

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


def make_json_edge(source_id, target_id, edge_name, capacity, label, utilization, util_ranges):
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
                             'label': label, 'utilization': utilization, 'interface-name': edge_name,
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
            'label': "data(label)",
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

selected_interface = 'no int selected'

styles_2 = {
    "content": {
        'width': '100%',
        'height': '100%',
        'z-index': 1000
    },
    "right_menu": {
        'width': '25%',
        'height': '60px',
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
        "width": '75%',
        'height': '100%',
        'position': 'absolute',
        'top': '0',
        'left': '0',
        'z-index': 1000
    },
    'cytoscape': {
        'position': 'absolute',
        'width': '100%',
        'height': '100%',
        'z-index': 999,
        'backgroundColor': '#D2B48C'
    },

}

# Check here for layout example: https://stackoverflow.com/questions/56175268/how-to-properly-add-style-to-my-dash-app

app = dash.Dash(__name__)

# TODO - display demand path interfaces on Demand Paths tab, make each interface selectable

# default_demand_source = ''

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
        html.P(id='cytoscape-tapEdgeData-output'),
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
                    id='demand-source-callback', options=[{'label': source, 'value': source}
                                                          for source in demand_sources_list],
                ),
                dcc.Dropdown(
                    id='demand-destination-callback', options=[{'label': dest, 'value': dest}
                                                               for dest in demand_destinations_list],
                ),
                dcc.RadioItems(
                    id='demand-path-interfaces',
                    labelStyle={'display': 'inline-block'}
                )
            ]),
            dcc.Tab(label='Interface Info', children=[
                dcc.RadioItems(
                    id='interface-demand-callback',
                    labelStyle={'display': 'inline-block'}
                ),
            ]),
       ]),
    ])
])

# TODO - now need to make it when selected interface = 'no int selected', demand path interface selection clears

# ######## DEFS TO UPDATE SELECTED INTERFACE ######## #
# Display demands on an interface and update selected_interfadce
@app.callback(Output('interface-demand-callback', "options"),
              [Input('cytoscape-prototypes', 'selectedEdgeData'),
               Input('demand-path-interfaces', 'value')])
def display_edge_demands(data, dmd_path_int):
    """
    Display demands on an interface and update selected_interfadce

    Compares data and dmd_path_int values to global selected_interface to see which
    has changed.  Finds the associated interface for data or dmd_path_int and then finds
    the demands egressing that interface.

    :param data:
    :param dmd_path_int:

    :return: list of values, where each value has format {"label": demand.__repr__(), "value": demand.__repr__()},
    reflecting the repr for the associated demand
    """
    global selected_interface
    print(selected_interface != 'no int selected')

    if selected_interface != 'no int selected':
        print("selected_interface is . . . :{}".format(selected_interface))
        print("data is from 421: {}".format(data))
        msg = compare_to_selected_interface(data, dmd_path_int, selected_interface)
        # msg = selected_interface
        print("msg is :::{}:::".format(msg))

        # If user clicks on empty space, it clears selected interface
        if msg == 'no int selected':
            return [{"label": '', "value": ''}]

        # Parse msg to get source and dest for interface
        int_src = msg.split()[3].split(',')[0]  # split(',') to remove the comma if it exists
        int_name = msg.split()[7].split(',')[0]  # split(',') to remove the comma to remove comma if it exists
        print("int_src, int_name = {}, {}".format(int_src, int_name))

        interface = model.get_interface_object(int_name, int_src)
        dmds = interface.demands(model)  # This will be a list of demands

        # Need to update selected_interface
        selected_interface = msg

        # Need to put demands in format for return
        demands_on_interface = []
        for demand in dmds:
            demands_on_interface.append({"label": demand.__repr__(), "value": demand.__repr__()})
        return demands_on_interface
    else:
        return [{"label": '', "value": ''}]


# Display info about edge user clicks on or selects in Demand Paths Interface list and updated selected_interface
@app.callback(Output('cytoscape-tapEdgeData-output', 'children'),
              [Input('cytoscape-prototypes', 'tapEdgeData'),
               Input('demand-path-interfaces', 'value')])
def display_tap_edge_data(data, demand_path_int):
    """
    # TODO - what is this def doing?!

    :param data:
    :param demand_path_int:
    :return:
    """

    global selected_interface
    if not(data):
        msg = 'no int selected'
        selected_interface = msg
        return msg

    # Parse selected interface to find interface source and name
    if selected_interface != 'no int selected':
        print("data from 395 is: {}".format(data))
        msg = compare_to_selected_interface(data, demand_path_int, selected_interface)
        # msg = selected_interface
        print("msg = {}".format(msg))

    else:
        if data:
            source = data['source']

            # Normalize destination to destination node, not the midpoint node
            dest_split = data['target'].split('-')[1:]
            dest = [entry for entry in dest_split if entry != source][0]

            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(source, dest, data['interface-name'], data['label'],
                                            data['capacity'], data['utilization'])

        elif not(data):
            msg = 'no int selected'

        elif demand_path_int:
            # demand_selected_interface will be a string; parse it to
            # get info
            int_data = demand_path_int.split()
            source = int_data[11].split("'")[1]
            dest = int_data[14].split("'")[1]
            ckt_id = int_data[17].split("'")[1]
            capacity = int_data[8].split(",")[0]
            int_name = int_data[2].split("'")[1]
            util = model.get_interface_object(int_name, source).utilization

            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(source, dest, int_name, ckt_id, capacity, util)

        else:
            msg = 'no int selected'

    selected_interface = msg
    return msg

# ######## DEFS TO UPDATE TABS ######## #
@app.callback(
    Output(component_id='demand-path-interfaces', component_property='options'),
    [Input(component_id='cytoscape-prototypes', component_property='tapEdgeData'),
     Input(component_id='demand-source-callback', component_property='value'),
     Input(component_id='demand-destination-callback', component_property='value')]
)
def display_demand_path_interfaces(data, source, destination):
    """
    Determines key based on source and destination.  Queries model for demands with matching
    source and destination.

    :param source: demand source node name
    :param destination: demand destination node name
    :return: list of values for demands, each value being {'label': dmd.__repr__(), 'value': dmd.__repr__()}
    for the Demand object
    """

    # Zero out the displayed path interfaces if empty space is selected on the map
    print("data from 449 = {}".format(data))
    if not(data):
        print("======= NO DATA ====================== a777safasdfa")
        source = None
        destination = None
        # return [{"label": '', "value": ''}]

    if source and destination:
        try:
            key = '{}-{}'.format(source, destination)
            demands = model.parallel_demand_groups()[key]

            dmd_int_set = find_demand_interfaces(demands)

            dmd_ints = []
            for dmd in dmd_int_set:
                dmd_ints.append({'label': dmd.__repr__(), 'value': dmd.__repr__()})
            return dmd_ints
        except KeyError:
            return [{"label": '', "value": ''}]
    else:
        return [{"label": '', "value": ''}]

# ######## OTHER DEFS ######## #

@app.callback(
    Output(component_id='demand-source-callback', component_property='value'),
    [Input(component_id='cytoscape-prototypes', component_property='tapEdgeData'),
    Input(component_id='interface-demand-callback', component_property='value')]
)
def update_default_demand_source(data, demand):

    global selected_interface

    if not(data):
        msg = 'no int selected'
        selected_interface = msg
        return ''

    if demand:
        # 'demand' will be a string repr, example:
        #  "Demand(source = C, dest = E, traffic = 20, name = 'dmd_c_e_1')"
        #  parse it to get source
        source = demand.split()[2][:-1]
        return source

@app.callback(
    Output(component_id='demand-destination-callback', component_property='value'),
    [Input(component_id='cytoscape-prototypes', component_property='tapEdgeData'),
    Input(component_id='interface-demand-callback', component_property='value')]
)
def update_default_demand_dest(data, demand):

    global selected_interface

    if not(data):
        msg = 'no int selected'
        selected_interface = msg
        return ''

    if demand:
        # 'demand' will be a string repr, example:
        #  "Demand(source = C, dest = E, traffic = 20, name = 'dmd_c_e_1')"
        #  parse it to get dest
        dest = demand.split()[5][:-1]
        return dest


# Need to select interfaces that have utilization ranges selected in values from dropdown
@app.callback(Output('cytoscape-prototypes', 'stylesheet'),
              [Input(component_id='cytoscape-prototypes', component_property='tapEdgeData'),
               Input('utilization-dropdown-callback', 'value'),
               Input('demand-source-callback', 'value'),
               Input('demand-destination-callback', 'value')])
def update_stylesheet(data, edges_to_highlight, source=None, destination=None):
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
    if not(data):
        return default_stylesheet + new_style

    # Demand source and destination path visualization
    if source is not None and destination is not None:
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

def compare_to_selected_interface(data, demand_path_int, selected_interface):
    """
    Compares data, demand_path_int, global selected_interface.

    Uses info in selected_interface to determine if data or demand_path_int has changed

    Returns a msg that will be used by calling function to update selected_interface


    :param data:
    :param demand_path_int:
    :param selected_interface:
    :return:
    """
    selected_int_split = selected_interface.split(",")
    selected_int_src = selected_int_split[0].split(":")[-1].strip()
    selected_int_name = selected_int_split[2].split(":")[1].strip()
    # Parse data to find interface source and name
    print()
    print()
    print()
    print("+"*20)
    print("data = {}".format(data))
    print("demand_path_int = {}".format(demand_path_int))
    print("selected_interface inbound = {}".format(selected_interface))
    if isinstance(data, list):
        if len(data) == 0:
            return 'no int selected'
        data = data[0]

    if data:
        # Parse data for interface source and interface name
        print("data at 465 is: {}".format(data))
        try:
            data_int_src = data['source']
            data_int_name = data['interface-name']
        except TypeError:
            print("TypeError called")
            import pdb
            pdb.set_trace()

        # Normalize destination to destination node, not the midpoint node
        dest_split = data['target'].split('-')[1:]
        dest = [entry for entry in dest_split if entry != data_int_src][0]

    if demand_path_int:
        # Parse demand_path_int for interface source and interface name
        demand_path_int_data = demand_path_int.split()
        dmd_path_int_source = demand_path_int_data[11].split("'")[1]
        dmd_path_int_name = demand_path_int_data[2].split("'")[1]

    if data and demand_path_int:
        # Compare data and demand_path_int to selected_interface to see which changed
        data_is_same = data_int_src == selected_int_src and data_int_name == selected_int_name
        dmd_path_int_is_same = dmd_path_int_source == selected_int_src and dmd_path_int_name == selected_int_name

        print("data is same = {}".format(data_is_same))
        print("dmd_path_int_is_same = {}".format(dmd_path_int_is_same))


        # If demand_path_interface is not the same, update the msg
        if not (dmd_path_int_is_same):
            int_data = demand_path_int_data
            source = dmd_path_int_source
            dest = int_data[14].split("'")[1]
            ckt_id = int_data[17].split("'")[1]
            capacity = int_data[8].split(",")[0]
            int_name = dmd_path_int_name
            util = model.get_interface_object(int_name, source).utilization

            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(source, dest, int_name, ckt_id, capacity, util)

        # If the data is not the same, it changed, update the msg
        elif not (data_is_same):
            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(data_int_src, dest, data_int_name, data['label'],
                                            data['capacity'], data['utilization'])

        # If data and demand_path_interface refer to the same interface, update the msg
        elif data_int_src == dmd_path_int_source and data_int_name == dmd_path_int_name:

            source = data_int_src
            # Normalize destination to destination node, not the midpoint node
            dest_split = data['target'].split('-')[1:]
            dest = [entry for entry in dest_split if entry != source][0]

            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(source, dest, data_int_name, data['label'],
                                            data['capacity'], data['utilization'])

        else:
            msg = "Unaccounted for scenario in selected interface selection"
            print(msg)

    else:
        if data:
            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(data_int_src, dest, data_int_name, data['label'],
                                            data['capacity'], data['utilization'])
        elif demand_path_int:
            int_data = demand_path_int_data
            source = dmd_path_int_source
            dest = int_data[14].split("'")[1]
            ckt_id = int_data[17].split("'")[1]
            capacity = int_data[8].split(",")[0]
            int_name = dmd_path_int_name
            util = model.get_interface_object(int_name, source).utilization

            msg = "Selected Interface: Source: {}, Dest: {}, name: {}, ckt_id: {}, capacity: {}, " \
                  "utilization: {}%".format(source, dest, int_name, ckt_id, capacity, util)

        elif not(data) and not(demand_path_int):
            msg = 'no int selected'
        else:
            msg = "Unaccounted for scenario in data or demand_path_int present"

    print("returned msg is {}".format(msg))
    print('='*20)

    return msg


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
# app.run_server()