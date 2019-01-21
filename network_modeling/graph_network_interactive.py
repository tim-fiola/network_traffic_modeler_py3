"""Facilitates network Model visualization"""


### NOTE - for interactive visualization, must update mpld3 manually
# to overcome this mpld3 bug: https://github.com/mpld3/mpld3/issues/434
#
# run:
# python3 -m pip install --user "git+https://github.com/javadba/mpld3@display_fix"


#######################################
## These 2 lines are needed to avoid the user interface crashing due to some
## problem with Tkinter interaction with matplotlib when importing Model
## into the ui code
import matplotlib as mpl
mpl.use("TkAgg")
########################################

import json

import matplotlib.lines as mlines
from matplotlib.patches import FancyArrowPatch, Circle
import matplotlib.pyplot as plt
import mpld3
from mpld3 import plugins, utils
import networkx as nx
from networkx.readwrite import json_graph
import threading
import time
import pdb

from .model import Model



class LinkedDragPlugin(plugins.PluginBase):
    JAVASCRIPT = r"""
    mpld3.register_plugin("drag", DragPlugin);
    DragPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    DragPlugin.prototype.constructor = DragPlugin;
    DragPlugin.prototype.requiredProps = ["idpts", "idline"];
    DragPlugin.prototype.defaultProps = {}
    function DragPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    DragPlugin.prototype.draw = function(){
        var ptsobj = mpld3.get_element(this.props.idpts, this.fig);
        var lineobj = mpld3.get_element(this.props.idline, this.fig);

        var drag = d3.behavior.drag()
            .origin(function(d) { return {x:ptsobj.ax.x(d[0]),
                                          y:ptsobj.ax.y(d[1])}; })
            .on("dragstart", dragstarted)
            .on("drag", dragged)
            .on("dragend", dragended);

        lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));

        lineobj.data = ptsobj.offsets;


        ptsobj.elements()
           .data(ptsobj.offsets)
           .style("cursor", "default")
           .call(drag);

        function dragstarted(d) {
          d3.event.sourceEvent.stopPropagation();
          d3.select(this).classed("dragging", true);
        }

        function dragged(d, i) {
          d[0] = ptsobj.ax.x.invert(d3.event.x);
          d[1] = ptsobj.ax.y.invert(d3.event.y);
          d3.select(this)
            .attr("transform", "translate(" + [d3.event.x,d3.event.y] + ")");
          lineobj.path.attr("d", lineobj.datafunc(ptsobj.offsets));
        }

        function dragended(d, i) {
          d3.select(this).classed("dragging", false);
        }
    }

    mpld3.register_plugin("drag", DragPlugin);
    """

    def __init__(self, points, line):
        if isinstance(points, mpl.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "drag",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      }


# Util ranges mapped to colors
util_ranges = [ ('darkviolet', 100),
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
        nx.set_node_attributes(G, {node_name: node.failed}, 'failed')
    return G

def _prep_network_model_for_graph(model):
    """Prepares Model data for interactive graphing.  Returns json data
    from networkx DiGraph."""

    # Define a networkx directed graph
    G = nx.DiGraph()
 
    # Set each graph node's name and position values
    G = _set_graph_node_name_and_position(model, G)   
 
    ######################
    # Get utilization for each interface and match it up with a color
    ckt_generator = (ckt for ckt in model.get_circuit_objects())
    for ckt in ckt_generator:
        # Get each interface
        int1, int2 = ckt.get_circuit_interfaces(model)

        edge_1_name = (int1.node_object.name,
                    int1.remote_node_object.name)
        edge_2_name = (int2.node_object.name,
                    int2.remote_node_object.name)
                    
        int_colors = {}
        int_util = {}
        # Assign colors to each interface in the ckt based on utilization
        if int1.failed == True:
            int_colors[edge_1_name] = 'grey'
            int_colors[edge_2_name] = 'grey'
        else:
            for color, util in util_ranges:
                if int1.utilization*100 >= util:
                    int_colors[edge_1_name] = color
                    int_util[edge_1_name] = int1.utilization*100
                    break
            for color1, util1 in util_ranges:
                if int2.utilization*100 >= util1:
                    int_colors[edge_2_name] = color1
                    int_util[edge_2_name] = int2.utilization*100
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
        midpoint_offset_from_node_B = ((x_offset/2.0), (y_offset/2.0))
        midpoint_coordinates = (node_B_pos[0] - midpoint_offset_from_node_B[0],
                                node_B_pos[1] - midpoint_offset_from_node_B[1])

        # Add new midpoint and associated edges to Graph G
        node_A = edge_1_name[0]
        node_B = edge_1_name[1]
        midpoint_node = 'midpoint '+edge_1_name[0]+'-'+edge_1_name[1]
        midpoint_node_failed = model.get_node_object(node_A).failed
        G.add_node(midpoint_node)
        nx.set_node_attributes(G, {midpoint_node: midpoint_coordinates}, 'pos')
        nx.set_node_attributes(G, {midpoint_node: midpoint_node}, 'name')
        nx.set_node_attributes(G, {midpoint_node: midpoint_node_failed}, 'failed')


        new_midpoint_edges = [(midpoint_node, node_A), (midpoint_node, node_B)]
        
         # Find the color and utilization for each edge and add edge to G      
        for edge in new_midpoint_edges:
            # Find the utilization color
            points = edge[0].split()[1].split('-')
            interface_source = edge[1] # formerly source point
            interface_dest = [point for point in points if point != interface_source][0] # formerly source
            
            int_color = int_colors[interface_source, interface_dest]
            
            # Find the utilization
            if int_color != 'grey': # int is not failed, get utilization
                int_utilization = int(int_util[interface_source, interface_dest])
            else: # int is failed
                int_utilization = 'failed - 0'
                
            G.add_edge(edge[0], edge[1], color=int_color, 
                                utilization = (str(int_utilization)+'%'))
       
        ##################    

    # Convert graph to json
    data = json_graph.node_link_data(G)
    
    return data

def _find_link_source_node(link):
    """Given a link, finds the actual source node from the link['source'] and
    link['target'].  Returns the name of the source node."""

    parts = link['source'].split()[1].split('-')
    
    if link['target'] == parts[0]:
        link_source = parts[1] 
    else:
        link_source = parts[0]

    return link_source

def _create_legend_line_collections(ax):
    """Create the line collections and labels for the interactive legend.
    Returns a list of lists of line object handles and a list of line ."""

    # Create interactive legend
    handles, labels = ax.get_legend_handles_labels() # return lines and labels

    # Lists to hold the lines of each color                    
    grey_lines = []
    royalblue_lines = []
    green_lines = []
    yellow_lines = []
    orangered_lines = []
    darkred_lines = []
    darkviolet_lines = [] 

    # Use the label position in labels to assign the line from handles
    # to the right list
    for x in range(0, len(labels)):
        if labels[x] == 'grey':
            grey_lines.append(handles[x])
        elif labels[x] == 'royalblue':
            royalblue_lines.append(handles[x])            
        elif labels[x] == 'green':
            green_lines.append(handles[x])                       
        elif labels[x] == 'yellow':
            yellow_lines.append(handles[x])
        elif labels[x] == 'orangered':
            orangered_lines.append(handles[x])
        elif labels[x] == 'darkred':
            darkred_lines.append(handles[x])
        elif labels[x] == 'darkviolet':
            darkviolet_lines.append(handles[x])
            

    line_group_labels = ['failed', '0-24% utilization', '25-49% utilization', 
                        '50-74% utilization', '75-89% utilization', 
                        '90-99% utilization', '>100% utilization']

    line_collections = [grey_lines, royalblue_lines, green_lines, yellow_lines,
                        orangered_lines, darkred_lines, darkviolet_lines]  

    # Make sure all line lists have at least one entry, or else
    # interactive legend breaks.  If a line list has no members,
    # add a small, dummy member with the correct color
    for x in range(0, len(line_collections)):
        color_list = ['grey', 'royalblue', 'green', 'yellow',
                      'orangered', 'darkred', 'darkviolet']
        if len(line_collections[x]) == 0:
            # Create a dummy line
            line = ax.plot([0,0.01], [0,0.01], color=color_list[x], 
                        linewidth=1.0, label='dummy')
            line_collections[x].append(line[0])

    return line_collections, line_group_labels


def _create_interactive_network_graph(json_data):
    """Creates a network graph with draggable nodes.  Interface
    colors represent utilization.  Tooltips show node name 
    and interface info.
    
    This graph cannot show multiple parallel circuits 
    between the same nodes. 
    
    lightgray = circuit/node is down

    Interface utilization coloring (colors from named_colors.py):
    0-25%   = blue
    25-50%  = green
    50-75%  = yellow
    75-90%  = orangered
    90-100% = red
    > 100%  = darkviolet    
    
    """
    # Prepare the plot
    fig, ax = plt.subplots(figsize=(15, 15))

    ax.set_facecolor('tan')

    # Plot the lines on ax
    links_iterator = (link for link in json_data['links'])
    for link in links_iterator: 

        # Edge x,y coordinates 
        x_coordinates = []
        y_coordinates = []

        # Get the utilization
        util = None
        if 'failed' in link['utilization']:
            util_split = link['utilization'].split('%')
            util = util_split[0].split()[-1]
        else:
            util = link['utilization'].split('%')[0]

        util_int = int(util)

        #### Node plot stuff ####

        node_tool_tip_labels = []
        
        # Get the source node
        src = link['source']

        # Get the target node
        target = link['target']
        
        # Get source node position and label
        for node in json_data['nodes']:
            if node['name'] == src:
                source_y, source_x = node['pos']
                node_tool_tip_labels.append(node['name'])
                break

        # Get target node position and label
        for node in json_data['nodes']:
            if node['name'] == target:
                target_y, target_x = node['pos']
                if node['failed'] == False:
                    node_tool_tip_labels.append(node['name'])
                else:
                    node_tool_tip_labels.append((node['name']+' (failed)'))
                break

        # Get the coordinates of the nodes for the line
        src_x = None
        src_y = None
        dest_x = None
        dest_y = None

        node_iterator = (node for node in json_data['nodes'])
        for node in node_iterator:
            if node['name'] == link['source']:
                src_y, src_x = node['pos']
            if node['name'] == link['target']:
                dest_y, dest_x = node['pos']

            if None not in (src_x, src_y,
                            dest_x, dest_y != [None, None, None, None]):
                break

        x_coordinates = [src_x, dest_x]
        y_coordinates = [src_y, dest_y]

        # Plot only the relevant nodes to the line
        nodes_on_plot = ax.plot(x_coordinates, y_coordinates, 'o', 
                                color='r', alpha=0.7, markersize=15, 
                                markeredgewidth=1)

        # Plot the line     
        line = ax.plot(x_coordinates, y_coordinates, color=link['color'], 
                        linewidth=5.0, label=link['color'])

        # Need to normalize some stuff for the line labels for the line tooltips
        link_source = _find_link_source_node(link)
        
        line_labels = ['from-'+link['target']+'-to-'+link_source+'; \
                            utilization = '+link['utilization']]
        
        # Add the tooltip labels to lines.
        # Notice we use the *LineLabelTooltip
        mpld3.plugins.connect(fig, mpld3.plugins.LineLabelTooltip(line[0],
                                                label = line_labels))


        # Drag plugin for nodes
        mpld3.plugins.connect(fig, LinkedDragPlugin(nodes_on_plot[0], line[0]))
        
        # Add the tooltip node labels
        # Notice we use the *PointLabelTooltip
        mpld3.plugins.connect(fig, mpld3.plugins.PointLabelTooltip(nodes_on_plot[0],
                                labels = node_tool_tip_labels ))


    # Plot the midpoint node labels
    for node in (node for node in json_data['nodes'] if 'midpoint' in node['id']):
        x, y = node['pos'][1], node['pos'][0]
        text = node['name']
        ax.text(x, y, text, fontsize=10, color='k', fontname='monospace')  

    # Plot the router node labels
    for node in (node for node in json_data['nodes'] if 'midpoint' not in node['id']):

        x, y = node['pos'][1], node['pos'][0]
        if node['failed'] == False:
            text = node['name']
        else:
            text = node['name']+' (failed)'
        ax.text(x, y, text, fontsize=15, color='k', fontname='monospace')

    ### Create interactive legend
    line_collections, line_group_labels = _create_legend_line_collections(ax)

    interactive_legend = plugins.InteractiveLegendPlugin(line_collections,
                                                         line_group_labels,
                                                         alpha_unsel=0.2,
                                                         alpha_over=1.8, 
                                                         start_visible=True)    
    fig.subplots_adjust(right=0.85)
    plugins.connect(fig, interactive_legend)

    time_now = str(time.asctime())
    ax.set_title("Network Graph:" + time_now, size=15)

    plot_thread = threading.Thread(target=_run_plot)
    plot_thread.start()
    
def _run_plot():
    try:
        mpld3.show()
    except Exception as e:
        print("Encountered exception.")
        print(e)
        print()
        print("This may be due to an mpld3 bug described in the link below:")
        print("https://github.com/mpld3/mpld3/issues/434")
        print()
        print("To overcome this bug, run the following command from the CLI to")
        print("get the mpld3 patch from github:")
        print('python3 -m pip install --user "git+https://github.com/javadba/mpld3@display_fix"')
        print()

def make_interactive_network_graph(model):
    """Takes a Model object as argument and returns an interactive
    network plot."""
    json_data = _prep_network_model_for_graph(model)
    _create_interactive_network_graph(json_data)

