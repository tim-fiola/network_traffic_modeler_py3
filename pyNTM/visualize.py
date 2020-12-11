import dash
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import json

from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from .rsvp import RSVP_LSP
from .demand import Demand

# Utilization ranges and corresponding edge colors
util_ranges = {'0-24': 'royalblue',
               '25-49': 'green',
               '50-74': 'yellow',
               '75-89': 'orangered',
               '90-99': 'darkred',
               '100+': 'darkviolet',
               'failed': 'grey'}


# ## Data Functions ## #
def make_json_node(x, y, id, label, midpoint=False, neighbors=[]):
    """
    Creates json info for node element that stores info about a pyNTM Node object

    :param x: x-coordinate (or longitude) of node
    :param y: y-coordinate (or latitude) of node
    :param id: node identifier within code
    :param label: Node's displayed label on on layout
    :param midpoint: Is this a midpoint node?  True|False
    :param neighbors: directly connected nodes

    :return: json element for graphing a node; if midpoint=True, data includes
    adding the 'midpoint' group and 'neighbors' list.

    Example return of midpoint json element:
        {'data': {'group': 'midpoint', 'id': 'midpoint-A-G',
               'label': 'midpoint-A-G', 'neighbors': ['A', 'G']},

    Example of return of Node object json element:
        {'data': {'group': '', 'id': 'A', 'label': 'A'},
        'position': {'x': 0, 'y': 0}},


    """

    json_node = {}
    json_node['position'] = {'x': x, 'y': y}
    json_node['data'] = {'id': id, 'label': label, 'group': ''}

    if midpoint:
        json_node['data']['group'] = 'midpoint'
        if neighbors:
            json_node['data']['neighbors'] = neighbors

    return json_node


def make_json_edge(source_id, target_id, edge_name, capacity, circuit_id, utilization, util_ranges, cost):
    """
    Creates json info for an edge on the graph, which corresponds to a pyNTM Interface object.
    The edge will source from the graph node (representing a pyNTM Node object) and
    terminate on a midpoint node.

    :param source_id: name of the source node on the graph
    :param target_id: name of the midpoint node on the graph
    :param edge_name: name of the edge (pyNTM Interface.name)
    :param capacity: capacity of the modeled corresponding Interface object
    :param circuit_id: represented Interface's circuit_id
    :param utilization: represented Interface's utilization
    :param util_ranges: utilization range data (for edge color)
    :param cost: represented Interface's cost

    :return: json data for the edge that represents the pyNTM Interface object

    Example return:
         {'data': {'capacity': 100,
                   'circuit_id': '7',
                   'cost': 25,
                   'group': 'royalblue',
                   'interface-name': 'G-F',
                   'source': 'G',
                   'target': 'midpoint-F-G',
                   'utilization': 5.0}}

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

    json_edge = {'data': {'source': source_id, 'target': target_id, "group": group,
                          'circuit_id': circuit_id, 'utilization': utilization, 'interface-name': edge_name,
                          'capacity': capacity, 'cost': cost}
                 }

    return json_edge
