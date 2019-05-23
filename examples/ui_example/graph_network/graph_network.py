"""Facilitates network Model visualization"""

#######################################
# These 2 lines are needed to avoid the user interface crashing due to some
# problem with Tkinter interaction with matplotlib when importing Model
# into the ui code
import matplotlib
matplotlib.use("TkAgg")
########################################

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import networkx as nx

from networkx.readwrite import json_graph
import json

#import network_modeling.http_server

import pdb

from matplotlib.patches import FancyArrowPatch, Circle
from pyNTM import Model

# Util ranges mapped to colors
util_ranges_2 = [('darkviolet', 100),
                 ('darkred', 90),
                 ('orangered', 75),
                 ('yellow', 50),
                 ('green', 25),
                 ('royalblue', 0)]


def _set_graph_node_name_and_position(model, G):
    """Sets lat/lon and node names for each node in nx Graph based on
    Node.lat, Node.lon, and Node.name values from the model"""
    for node in model.node_objects:
        node_name = node.name
        G.add_node(node_name)
        lat_lon = (node.lon, node.lat)
        nx.set_node_attributes(G, {node_name: lat_lon}, 'pos')
        nx.set_node_attributes(G, {node_name: node_name}, 'name')
    return G


def _draw_node_labels(G):
    # Given networkx graph G, draw node labels
    nx.draw_networkx_labels(G, pos=nx.get_node_attributes(G, 'pos'),
                            labels={data['name']: data['name']
                                    for data in G.nodes.values()})


def make_network_graph(model, graph_file_name, display_plot=False):
    """
    Create a line graph of the network, showing failed nodes and circuits
    in red, and non-failed nodes and ciruits in green.  This graph cannot show
    multiple parallel circuits between the same nodes.

    ARGUMENTS:
    model:              network model object
    graph_file_name:    name of file to save graph to
    display_plot:       (default=False) optionally display the plot

    lat_lon for a node is simply y,x coordinates at this point; the coordinates
    are not normalized to -90<=lat<=90 or -180<=lon<=180 at this point

    """

    # Get edge and node names from the model
    node_names = (node.name for node in model.node_objects)
    edges = ((circuit.interface_a.node_object.name,
              circuit.interface_b.node_object.name) for circuit in
             model.get_circuit_objects())

    # Define a graph
    G = nx.Graph()
    G.add_edges_from(edges)

    # Set lat/lon for each node in graph
    for name in node_names:
        node = model.get_node_object(name)
        lat_lon = (node.lat, node.lon)
        nx.set_node_attributes(G, {name: lat_lon}, 'pos')
        nx.set_node_attributes(G, {name: name}, 'name')

    model_nodes_in_up_status = model.get_non_failed_node_objects()
    model_nodes_in_down_status = model.get_failed_node_objects()

    # Draw the green/up network nodes
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=[
                               node.name for node in model_nodes_in_up_status],
                           node_color='g')

    # Draw the red/failed network nodes
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=[
                               node.name for node in model_nodes_in_down_status],
                           node_color='r')

    # Add the node labels
    nx.draw_networkx_labels(G, pos=nx.get_node_attributes(G, 'pos'),
                            labels={data['name']: data['name']
                                    for data in G.nodes.values()})

    # Get the failed circuit nodes
    failed_int_edges = ((intf.node_object.name, intf.remote_node_object.name)
                        for intf in model.get_failed_interface_objects())
    failed_circuits = []
    for edge in failed_int_edges:
        if (edge[1], edge[0]) not in failed_circuits:
            failed_circuits.append((edge[0], edge[1]))

    # Get the non-failed circuit nodes
    unfailed_int_edges = ((intf.node_object.name, intf.remote_node_object.name)
                          for intf in model.get_non_failed_interface_objects())
    unfailed_circuits = []
    for edge in unfailed_int_edges:
        if (edge[1], edge[0]) not in unfailed_circuits:
            unfailed_circuits.append((edge[0], edge[1]))

    # Draw the failed circuits
    nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                           edgelist=failed_circuits, edge_color='r')

    # Draw the unfailed circuits
    nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                           edgelist=unfailed_circuits, edge_color='g')

    # Add plot title
    plt.title(graph_file_name)

    # Save the graph file
    plt.savefig(graph_file_name)

    if display_plot == True:
        # Show the plot
        plt.show()


def make_utilization_graph_neat(model, graph_file_name, display_plot=False):
    """
    Create a directed graph of the network, showing failed nodes and circuits
    in red, and non-failed nodes and ciruits in green.  Also determine interface
    utilization and add an edge color to reflect the utilization.
    This graph cannot show multiple parallel circuits between the same nodes.

    lightgray = circuit/node is down

    Interface utilization coloring (colors from named_colors.py):
    0-25%   = blue
    25-50%  = green
    50-75%  = yellow
    75-90%  = orangered
    90-100% = red
    > 100%  = darkviolet

    ARGUMENTS:
    model:              network model object
    graph_file_name:    name of file to save graph to
    display_plot:       (default=False) optionally display the plot

    lat_lon for a node is simply y,x coordinates at this point; the coordinates
    are not normalized to -90<=lat<=90 or -180<=lon<=180 at this point
    """

    # Define a graph
    G = nx.DiGraph()

    # Set tan as background color for graph
    fig = plt.figure(figsize=(18, 9), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor('tan')

    # Set each graph node's name and position values
    G = _set_graph_node_name_and_position(model, G)

    # Get utilization for each interface and match it up with a color
    for ckt in model.get_circuit_objects():
        # Get each interface
        int1, int2 = ckt.get_circuit_interfaces(model)

        edge_1_name = (int1.node_object.name,
                       int1.remote_node_object.name)
        edge_2_name = (int2.node_object.name,
                       int2.remote_node_object.name)

        int_colors = {}
        # Assign colors to each interface in the ckt based on utilization
        if int1.failed == True:
            int_colors[edge_1_name] = 'grey'
            int_colors[edge_2_name] = 'grey'
        else:
            for item in util_ranges_2:
                if int1.utilization * 100 >= item[1]:
                    int_colors[edge_1_name] = item[0]
                    break
            for item in util_ranges_2:
                if int2.utilization * 100 >= item[1]:
                    int_colors[edge_2_name] = item[0]
                    break

        # Get all the existing node positions
        #### Find midpoint between edge nodes ####
        # Get 1st node coordinates
        node_A_pos = G.node[edge_1_name[0]]['pos']
        # Get 2nd node coordinates
        node_B_pos = G.node[edge_1_name[1]]['pos']
        # Find the midpoint offset from 2nd node
        # X,Y offset
        x_offset = node_B_pos[0] - node_A_pos[0]
        y_offset = node_B_pos[1] - node_A_pos[1]

        # Find the coordinates of midpoint
        midpoint_offset_from_node_B = ((x_offset / 2.0), (y_offset / 2.0))
        midpoint_coordinates = (node_B_pos[0] - midpoint_offset_from_node_B[0],
                                node_B_pos[1] - midpoint_offset_from_node_B[1])

        # Add new midpoint and associated edges to Graph G
        node_A = edge_1_name[0]
        node_B = edge_1_name[1]
        midpoint_node = edge_1_name[0] + '-' + edge_1_name[1]
        G.add_node(midpoint_node)
        nx.set_node_attributes(G, {midpoint_node: midpoint_coordinates}, 'pos')
        nx.set_node_attributes(G, {midpoint_node: midpoint_node}, 'name')

        new_midpoint_edges = [(midpoint_node, node_A), (midpoint_node, node_B)]
        G.add_edges_from(new_midpoint_edges)

        # Draw the edges on the graph ### add the labels
        nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                               edgelist=[(midpoint_node, node_A)],
                               edge_color=int_colors[edge_1_name],
                               width=9, arrowsize=9, arrows=False)
        nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                               edgelist=[(midpoint_node, node_B)],
                               edge_color=int_colors[edge_2_name],
                               width=9, arrowsize=9, arrows=False)

        # Determine the labels
        midpoint_label = {midpoint_node: midpoint_node}
        midpoint_pos = {midpoint_node: G.node[midpoint_node]['pos']}

    # Draw node labels and nodes
    _draw_node_labels(G)

    # Draw non-failed nodes
    non_failed_node_names = [node.name for node in model.node_objects
                             if node.failed == False]
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=non_failed_node_names,
                           node_color='cadetblue', edgecolors='black')
    # Draw failed nodes
    failed_node_names = [node.name for node in model.get_failed_node_objects()]
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=failed_node_names,
                           node_color='grey', edgecolors='black')

    # Prepare the legend - TODO this could be automated better
    dv = mlines.Line2D([], [], color='darkviolet', label='100% <= util',
                       lw=5)
    r = mlines.Line2D([], [], color='darkred', label="90% <= util <= 99%",
                      lw=5)
    o = mlines.Line2D([], [], color='orangered', label="75% <= util < 90%",
                      lw=5)
    y = mlines.Line2D([], [], color='yellow', label="50% <= util < 75%",
                      lw=5)
    g = mlines.Line2D([], [], color='green', label="25% <= util < 50%",
                      lw=5)
    b = mlines.Line2D([], [], color='royalblue', label="25% <= util < 50%",
                      lw=5)
    gr = mlines.Line2D([], [], color='gray', label="failed link/node",
                       lw=5)

    legend_handles = [dv, r, o, y, g, b, gr]

    # center the legend, 4 columns, centered on and just below the figure
    plt.legend(handles=legend_handles, bbox_to_anchor=(0.5, -0.1), ncol=4,
               loc='center')

    # Add plot title
    plt.title(graph_file_name)

    # Save the plot pic
    plt.savefig(graph_file_name)

    if display_plot == True:
        # Display the plot
        plt.show()


def make_utilization_graph_curves(model, graph_file_name):
    """
    (BETA) Create a directed graph of the network, **with curved edges**,
    showing failed nodes and circuits
    in red, and non-failed nodes and ciruits in green.  Also determine interface
    utilization and add an edge color to reflect the utilization.
    This graph cannot show multiple parallel circuits between the same nodes.

    lightgray = circuit/node is down

    Interface utilization coloring (colors from named_colors.py):
    0-25%   = blue
    25-50%  = green
    50-75%  = yellow
    85-90%  = orangered
    90-100% = darkred
    > 100%  = darkviolet

    lat_lon for a node is simply y,x coordinates at this point; the coordinates
    are not normalized to -90<=lat<=90 or -180<=lon<=180 at this point
<<<<<<< HEAD

    """
##    arrow_style = "->"

    G = nx.MultiDiGraph()

    edges = ((circuit.interface_a.node_object.name,
              circuit.interface_b.node_object.name) for circuit in
             model.get_circuit_objects())

    G.add_edges_from(edges)

    # Set each graph node's name and position values
    G = _set_graph_node_name_and_position(model, G)

    # Get all failed and non-failed nodes in separate lists
    failed_node_names = [node.name for node in model.get_failed_node_objects()]
    non_failed_node_names = [node.name for node in
                             model.get_non_failed_node_objects()]

    # Get all failed and non-failed interfaces in separate lists
    failed_interface_edges = [(interface.node_object.name,
                               interface.remote_node_object.name)
                              for interface in
                              model.get_failed_interface_objects()]

    # Set lightgrey as background color
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor('tan')

    # Print the failed nodes
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=failed_node_names, node_color='grey',
                           edgecolors='darkred')

    node_positions = nx.get_node_attributes(G, 'pos')

    # Draw failed interfaces
    nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                           edgelist=failed_interface_edges, width=7,
                           arrowsize=2, edge_color='darkred',
                           arrowstyle='-')

    nx.draw_networkx_edges(G, pos=nx.get_node_attributes(G, 'pos'),
                           edgelist=failed_interface_edges, width=5,
                           arrowsize=2, edge_color='grey',
                           arrowstyle='-')

    ######## Draw interfaces for each each non-failed circuit ###########
    non_failed_ckts = [ckt for ckt in model.get_circuit_objects() if
                       ckt.interface_a.failed == False]

    # For each interface in each non-failed circuit, find the interface's
    # utilization color in utilization_ranges
    for ckt in non_failed_ckts:
        # Get each interface
        int1, int2 = ckt.get_circuit_interfaces(model)

        edge_1_name = (int1.node_object.name,
                       int1.remote_node_object.name)
        edge_2_name = (int2.node_object.name,
                       int2.remote_node_object.name)

        int_colors = {}

        # Assign utilization color to interface
        for item in util_ranges_2:
            if int1.utilization * 100 >= item[1]:
                int_colors[edge_1_name] = item[0]
                break

        for item in util_ranges_2:
            if int2.utilization * 100 >= item[1]:
                int_colors[edge_2_name] = item[0]
                break

        # Get node positions
        a_pos = G.node[edge_1_name[0]]['pos']
        b_pos = G.node[edge_1_name[1]]['pos']
        e1_label = str(b_pos) + '-to-' + str(a_pos)

        # Draw the curved edges
        e1 = FancyArrowPatch(posA=b_pos, posB=a_pos,
                             connectionstyle='arc3, rad=0.1',
                             arrowstyle='-|>', linewidth=3,
                             edgecolor=int_colors[edge_1_name],
                             mutation_scale=15,
                             label=e1_label)

        e2 = FancyArrowPatch(posA=a_pos, posB=b_pos,
                             connectionstyle='arc3, rad=0.1',
                             arrowstyle='-|>', linewidth=3,
                             edgecolor=int_colors[edge_2_name],
                             mutation_scale=15)

        e1_outline = FancyArrowPatch(posA=b_pos, posB=a_pos,
                                     connectionstyle='arc3, rad=0.1',
                                     arrowstyle='-|>', linewidth=5,
                                     edgecolor='black',
                                     mutation_scale=15)

        e2_outline = FancyArrowPatch(posA=a_pos, posB=b_pos,
                                     connectionstyle='arc3, rad=0.1',
                                     arrowstyle='-|>', linewidth=5,
                                     edgecolor='black',
                                     mutation_scale=15)
        ax.add_patch(e1_outline)
        ax.add_patch(e2_outline)
        ax.add_patch(e1)
        ax.add_patch(e2)

        # Add the edge labels at the midpoint of straight line between
        # the source,dest nodes
        #<do this>

    # Draw node labels and nodes
    draw_node_labels(G)
    non_failed_node_names = [node.name for node in model.node_objects
                             if node.failed == False]
    nx.draw_networkx_nodes(G, pos=nx.get_node_attributes(G, 'pos'),
                           nodelist=non_failed_node_names,
                           node_color='cadetblue', edgecolors='black')

    # Display the plot
    plt.show()
