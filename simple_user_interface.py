"""Simple, menu-driven UI for network_modeling module.
Allows users to interact with and relate between associated
demands, interfaces, and nodes."""

from network_modeling import Model
from network_modeling import ModelException
from network_modeling import Interface
from network_modeling import Demand
from network_modeling import Node 
from network_modeling import graph_network
from network_modeling import RSVP_LSP

from network_modeling import graph_network_interactive 

from tkinter import ttk as ttk
from tkinter import *
from tkinter import filedialog

import re

import pdb

background_color = 'tan'

def update_tabs():
    """
    Updates the info displayed on each tab
    :return: None
    """
    # Update the Node Explorer tab
    examine_selected_node()
    # Update the Demand Explorer tab
    examine_selected_demand()
    # Update the Interface Explorer tab
    examine_selected_interface()
    # Update the Path Explorer tab
    examine_paths()

    if len(model.rsvp_lsp_objects) > 0:
        # Update the RSVP LSP Explorer tab
        examine_selected_lsp()
        print("selected_lsp set to {}".format(selected_lsp.get()))

    print("selected_node set to {}".format(selected_node.get()))
    print("selected_demand set to {}".format(selected_demand.get()))
    print("selected_interface set to {}".format(selected_interface.get()))

def open_file():
    """Opens the file that describes the Model and allows user to save
    a diagram of the network graph"""
    if selected_model_file.get() == '':
        selected_model_file.set(filedialog.askopenfilename(initialdir = "/",
                            title = "Select file",
                            filetypes = (("csv files","*.csv"),
                                            ("all files","*.*"))))

    global model

    selected_file_label = ttk.Label(label_frame,
                                    text ="Network Model file is:")
    selected_file_label.grid(row=1, column=0, sticky='W')
    selected_file_display = ttk.Label(label_frame, text=' '*30)
    selected_file_display = ttk.Label(label_frame,
                    text=selected_model_file.get())
    selected_file_display.grid(row=6, column=0)

    if selected_model_file.get() != '':
        model = Model.load_model_file(selected_model_file.get())
        model.update_simulation()

        model_status_label = ttk.Label(label_frame, text="Model is:")
        model_status_label.grid(row = 8, column=0, sticky='W')
        model_file_display = ttk.Label(label_frame, text=model)
        model_file_display.grid(row=9, column=0, sticky='W')

        # # Update the Node Explorer tab
        # examine_selected_node()
        # # Update the Demand Explorer tab
        # examine_selected_demand()
        # # Update the Interface Explorer tab
        # examine_selected_interface()
        # # Update the Path Explorer tab
        # examine_paths()
        # # Update the RSVP LSP Explorer tab
        # examine_selected_lsp()
        update_tabs()

    # Create a button to produce a network graph
    graph_network_button = Button(label_frame)
    graph_network_button.grid(row=12, column=0, padx=5, pady=5, sticky='W')
    graph_network_button["text"] = "Push to create network graph"
    # Don't add the trailing () or this will execute immediately/automatically

    graph_network_button["command"] = create_interactive_network_graph_and_refresh

    if network_graph_file.get() != '':
        graph_label_text = "Graph file saved at: "+network_graph_file.get()
        graph_file_label = Label(label_frame, text=graph_label_text)
        graph_file_label.grid(row=13, column=0, sticky='W')

def create_network_graph():
    """Makes a network graph"""
    # TODO - deprecated?

    network_graph_file.set(filedialog.asksaveasfilename(initialdir="/",
                        title = "Select or Create file:"))
    graph_network.make_utilization_graph_neat(model, network_graph_file.get(),
                        display_plot=False)

def create_network_graph_and_refresh():
    """Makes a network graph and refreshes open_file_tab"""

    network_graph_file.set(filedialog.asksaveasfilename(initialdir="/",
                        title = "Select or Create file:"))
    graph_network.make_utilization_graph_neat(model, network_graph_file.get(),
                        display_plot=False)
    open_file()


def create_interactive_network_graph_and_refresh():
    """Makes an interactive network graph and refreshes open_file_tab"""
    graph_network_interactive.make_interactive_network_graph(model)


def set_active_interface_from_listbox(event):
    """Sets the selected interface value from a listbox to the
    active_interface"""
    w = event.widget
#    value = (w.curselection())
    value_position = (w.curselection())

    # This next part takes the first value in case the listbox has
    # extra info trailing the interface
    value_in_position = w.get(value_position)

    # Use interface repr, so splitting that using split() yields interface
    # name in position 2
    selected_interface_value = value_in_position

    selected_interface.set(selected_interface_value)

    # Refresh the tabs
    # TODO - add the destroy() function?
    # examine_selected_node()
    # examine_selected_demand()
    # examine_selected_interface()
    # examine_selected_lsp()
    # examine_paths()
    update_tabs()


def set_active_demand_from_listbox(event):
    """Sets the selected demand value from a listbox to the active_demand"""
    w = event.widget
#    value = (w.curselection()) # get the current selection
    value_position = (w.curselection()) # get the position of the current selection
    selected_demand.set(w.get(value_position)) # set selected_demand to the current selection

    # Try to delete the Node Demand Info labelframe to clear the demand paths
    for thing in demand_tab.grid_slaves():
        thing.destroy()
    for thing in node_tab.grid_slaves():
        thing.destroy()
    for thing in interface_tab.grid_slaves():
        thing.destroy()
    for thing in path_tab.grid_slaves():
        thing.destroy()
    for thing in lsp_tab.grid_slaves():
        thing.destroy()

    # Refresh the info on tabs
    # examine_selected_node()
    # examine_selected_demand()
    # examine_selected_interface()
    # examine_paths()
    # examine_selected_lsp()
    update_tabs()


def set_active_object_from_option_menu(event):
    """Refreshes the tabs with the new active object info and displays
    the info based on the new active object"""

    # Try to delete the Node Demand Info labelframe to clear the demand paths
    for thing in demand_tab.grid_slaves():
        thing.destroy()
    for thing in node_tab.grid_slaves():
        thing.destroy()
    for thing in interface_tab.grid_slaves():
        thing.destroy()
    # TODO - this below was commented out; i enabled it
#    for thing in path_tab.grid_slaves():
#        thing.destroy()

    for thing in lsp_tab.grid_slaves():
        thing.destroy()

    # Refresh the Node Info and Demand Info tabs
    # examine_selected_node()
    # examine_selected_demand()
    # examine_selected_interface()
    # examine_paths()
    # examine_selected_lsp()
    update_tabs()


def get_demand_object_from_repr(demand_repr):
    """Returns demand object with an input of the demand's repr"""

    try:
        demand_info = re.split(', | |\)', demand_repr)
        demand_source = demand_info[2]
        demand_dest = demand_info[5]
        demand_name = demand_info[11][1:-1]
        demand_object = model.get_demand_object(demand_source, demand_dest,
                                                        demand_name=demand_name)
        return demand_object
    except IndexError:
        pass


def get_demands_on_interface(selected_interface):
    """Returns a list of demands on the selected_interface"""

    # Display demands on interface
    try:
        interface_data = selected_interface.split("'")
        interface_name = interface_data[1]
        node_name = interface_data[3]

        interface_object = model.get_interface_object(interface_name,
                                                        node_name)
        demands_on_interface = interface_object.demands(model)
    except (ModelException, IndexError):
        interface_object=None
        demands_on_interface=[]

    return demands_on_interface


def get_lsps_on_interface(selected_interface):
    """
    Returns a list of LSPs on the selected_interface
    :param selected_interface: selected interface in ui
    :return: list of lsps on selected_interface
    """

    # Get list of LSPs on interface
    try:
        interface_data = selected_interface.split("'")
        interface_name = interface_data[1]
        node_name = interface_data[3]

        interface_object = model.get_interface_object(interface_name,
                                                        node_name)
        lsps_on_interface = interface_object.lsps(model)
    except (ModelException, IndexError):
        interface_object=None
        lsps_on_interface=[]

    return lsps_on_interface


def display_selected_objects(canvas_object, row_, column_):
    """Displays the selected objects"""

    node_status = 'Unknown'
    demand_status = 'Unknown'
    interface_status = 'Unknown'
    lsp_status = 'Unknown'

    try:
        node_failed = model.get_node_object(selected_node.get()).failed
        if node_failed == True:
            node_status = 'Failed'
        else:
            node_status = 'Not Failed'
    except ModelException:
        pass

    try:
        selected_interface_name = selected_interface.get().split("'")[1]
        selected_interface_node = selected_interface.get().split("'")[3]

        interface_object = model.get_interface_object(selected_interface_name,
                                                      selected_interface_node)

        interface_failed = interface_object.failed

        interface_util = str(round((interface_object.utilization*100),1))

        if interface_failed == True:
            interface_status = 'Failed'
        else:
            interface_status = interface_util+"% utilized"
    # These exceptions are necessary so the menu does not error out
    # before all the key objects are defined
    except (ModelException, AttributeError, IndexError) as e:
        pass

    try:
        demand_object = get_demand_object_from_repr(selected_demand.get())
        demand_routed = demand_object.path

        if demand_routed == 'Unrouted':
            demand_status = 'Unrouted'
        else:
            demand_status = 'Routed'
    # These exceptions are necessary so the menu does not error out
    # before all the key objects are defined
    except (ModelException, AttributeError):
        pass

    try:
        lsp_object = get_lsp_object_from_repr(selected_lsp.get())
        lsp_routed = lsp_object.path

        if lsp_routed == "Unrouted":
            lsp_status = "Unrouted"
        else:
            lsp_status = 'Routed'
    except (ModelException, AttributeError) as e:
        pass

    selected_object_frame = LabelFrame(canvas_object, background=background_color,
                                text="Selected Interface, Demand, and Node")
    selected_object_frame.grid(column=column_, row=row_, columnspan=3, pady=10)
    selected_object_frame.column_width=40
    selected_object_frame.columnconfigure(0, weight=1)
    selected_object_frame.columnconfigure(1, weight=2)
    selected_object_frame.columnconfigure(2, weight=1)

    Label(selected_object_frame, text='Name',
            background=background_color).grid(row=row_+1, column=1)
    Label(selected_object_frame, text='Status',
            background=background_color).grid(row=row_+1, column=2)

    Label(selected_object_frame, text="Selected Node:",
            background=background_color).grid(row=row_+2, column=0, sticky='W')
    Label(selected_object_frame, text=selected_node.get(), width=52,
            borderwidth=1, relief="solid").grid(row=row_+2, column=1)
    Label(selected_object_frame, text=node_status,
            background=background_color).grid(row=row_+2, column=2, sticky='E')

    Label(selected_object_frame, text="Selected Interface:",
            background=background_color).grid(row=row_+3, column=0, sticky='W')
    Label(selected_object_frame, text=selected_interface.get(),
            width=52, justify=LEFT, wraplength=450,
            borderwidth=1, relief="solid").grid(row=row_+3, column=1)
    Label(selected_object_frame, text=interface_status,
            background=background_color).grid(row=row_+3, column=2, sticky='E')

    Label(selected_object_frame, text="Selected Demand:",
            background=background_color).grid(row=row_+4, column=0, sticky='W')
    Label(selected_object_frame, text=selected_demand.get(), width=52,
        borderwidth=1, wraplength=450, relief="solid").grid(row=row_+4, column=1)
    Label(selected_object_frame, text=demand_status,
        background=background_color).grid(row=row_+4, column=2, sticky='E')

    Label(selected_object_frame, text="Selected LSP:",
          background=background_color).grid(row=row_+5, column=0, sticky='W')
    Label(selected_object_frame, text=selected_lsp.get(), width=52,
        borderwidth=1, wraplength=450, relief="solid").grid(row=row_+5, column=1)
    Label(selected_object_frame, text=lsp_status,
        background=background_color).grid(row=row_+5, column=2, sticky='E')

    return selected_object_frame


def display_demands(label_info, canvas_object, list_of_demands, row_,
                column_,):
    """Displays a label for demands and a single-select listbox of the
    demands below the label_info on a given canvas_object.  A horizontal
    scrollbar is included """

    demands_frame = LabelFrame(canvas_object)
    demands_frame.grid(row=row_, column=column_, pady=10)

    Label(demands_frame, text=label_info).grid(row = 0,
                    column=0, sticky='W', padx=10)

    # Horizontal scrollbar - TODO create decorator for the scrollbar?
    horizontal_scrollbar = Scrollbar(demands_frame, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=3, column=0, sticky=E+W)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(demands_frame, orient=VERTICAL)
    vertical_scrollbar.grid(row=1, column=1, sticky=N+S)

    demand_listbox = Listbox(demands_frame, selectmode='single', height=10,
                            width=40, xscrollcommand=horizontal_scrollbar.set,
                            yscrollcommand=vertical_scrollbar.set)
    demand_listbox.grid(row = 1, column=0, sticky='W', padx=10)

    vertical_scrollbar.config(command=demand_listbox.yview)

    horizontal_scrollbar.config(command=demand_listbox.xview)

    demand_counter = 1

    if list_of_demands != None:
        for demand in list_of_demands:
            demand_listbox.insert(demand_counter, demand)
            demand_counter += 1
    else:
        pass

    demand_listbox.bind("<<ListBoxSelect>>", set_active_demand_from_listbox)
    demand_listbox.bind("<Double-Button-1>", set_active_demand_from_listbox)

    return demand_listbox


def display_list_of_things(label_info, canvas_object, list_of_things,
                           row_, column_, command_to_activate):
    """
    Displays a label for list and a single-select listbox of the
    list items below the label_info on a given canvas_object.  A horizontal
    scrollbar is included
    :param label_info: string label for displayed list
    :param canvas_object: object to display listbox in
    :param list_of_things: a list object
    :param row_: row number in canvas_object
    :param column_: column number in canvas_object
    :param command_to_activate: command to set selected object as active
    :return: Listbox object with label_info above it at row_, column_ in canvas_object
    """

    demands_frame = LabelFrame(canvas_object)
    demands_frame.grid(row=row_, column=column_, pady=10)

    Label(demands_frame, text=label_info).grid(row = 0,
                    column=0, sticky='W', padx=10)

    # Horizontal scrollbar - TODO create decorator for the scrollbar?
    horizontal_scrollbar = Scrollbar(demands_frame, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=3, column=0, sticky=E+W)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(demands_frame, orient=VERTICAL)
    vertical_scrollbar.grid(row=1, column=1, sticky=N+S)

    listbox = Listbox(demands_frame, selectmode='single', height=10,
                            width=40, xscrollcommand=horizontal_scrollbar.set,
                            yscrollcommand=vertical_scrollbar.set)
    listbox.grid(row = 1, column=0, sticky='W', padx=10)

    vertical_scrollbar.config(command=listbox.yview)

    horizontal_scrollbar.config(command=listbox.xview)

    item_counter = 1

    if list_of_things != None:
        for item in list_of_things:
            listbox.insert(item_counter, item)
            item_counter += 1
    else:
        pass

    listbox.bind("<<ListBoxSelect>>", command_to_activate)
    listbox.bind("<Double-Button-1>", command_to_activate)

    return listbox


def display_interfaces(label_info, canvas_object, list_of_interfaces,
                        row_, column_):
    """Displays interfaces from list of interfaces in single selectable listbox.
    A label with label_info will appear above the listbox."""
    # Display Node's Interfaces Label
    Label(canvas_object, text=label_info).grid(row=row_, column=column_,
                                                sticky='W', padx=10)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(canvas_object, orient=VERTICAL)
    vertical_scrollbar.grid(row=row_+1, column=column_+2, sticky=N+S)

    horizontal_scrollbar = Scrollbar(canvas_object, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=(row_+2), column=column_, sticky=E+W,
                            columnspan=2)

    # Create a listbox with the available interfaces
    interfaces_listbox = Listbox(canvas_object, selectmode='single',
                height = 8, width=40, xscrollcommand=horizontal_scrollbar.set,
                yscrollcommand=vertical_scrollbar.set)
    interfaces_listbox.grid(row=row_+1, column=column_, columnspan=2,
                                sticky='W', padx=10)

    horizontal_scrollbar.config(command=interfaces_listbox.xview)
    vertical_scrollbar.config(command=interfaces_listbox.yview)

    intf_counter = 1

    for intf_name in list_of_interfaces:
        interfaces_listbox.insert(intf_counter, intf_name)
        intf_counter += 1

    interfaces_listbox.bind("<<ListBoxSelect>>", set_active_interface_from_listbox)
    interfaces_listbox.bind("<Double-Button-1>", set_active_interface_from_listbox)

    return interfaces_listbox

# TODO - use display_list_of_things_instead
def display_lsp_list(label_info, canvas_object, list_of_lsps,
                       row_, column_):
    """
    Displays interfaces from list of lsps in single selectable listbox.
    A label with label_info will appear above the listbox.
    :param label_info: Label for displayed list
    :param canvas_object: object where list will be displayed
    :param list_of_lsps: list of RSVP_LSP objects
    :param row_: row position
    :param column_: column position
    :return:
    """
    # Display LSP list's Label
    Label(canvas_object, text=label_info).grid(row=row_, column=column_,
                                               sticky='W', padx=5)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(canvas_object, orient=VERTICAL)
    vertical_scrollbar.grid(row=row_ + 1, column=column_ + 2, sticky=N + S)

    horizontal_scrollbar = Scrollbar(canvas_object, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=(row_ + 2), column=column_, sticky=E + W,
                              columnspan=2)

    # Create a listbox with the available interfaces
    lsps_listbox = Listbox(canvas_object, selectmode='single',
                                 height=8, width=40, xscrollcommand=horizontal_scrollbar.set,
                                 yscrollcommand=vertical_scrollbar.set)
    lsps_listbox.grid(row=row_ + 1, column=column_, columnspan=2,
                            sticky='W', padx=5)

    horizontal_scrollbar.config(command=lsps_listbox.xview)
    vertical_scrollbar.config(command=lsps_listbox.yview)

    lsp_counter = 1

    for intf_name in list_of_lsps:
        lsps_listbox.insert(lsp_counter, intf_name)
        lsp_counter += 1

    lsps_listbox.bind("<<ListBoxSelect>>", set_active_lsp_from_listbox)
    lsps_listbox.bind("<Double-Button-1>", set_active_lsp_from_listbox)

    return lsps_listbox


def display_lsp(label_info, canvas_object, lsp, row_, column_):
    """

    :param label_info:
    :param canvas_object:
    :param lsp:
    :param row_:
    :param column_:
    :return:
    """
    Label(canvas_object, text=label_info).grid(row=row_, column=column_,
                                               sticky='W', padx=5)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(canvas_object, orient=VERTICAL)
    vertical_scrollbar.grid(row=row_ + 1, column=column_ + 2, sticky=N + S)

    horizontal_scrollbar = Scrollbar(canvas_object, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=(row_ + 2), column=column_, sticky=E + W,
                              columnspan=2)

    # Create a listbox with the lsp
    lsp_listbox = Listbox(canvas_object, selectmode='single',
                height = 8, width=40, xscrollcommand=horizontal_scrollbar.set,
                yscrollcommand=vertical_scrollbar.set)
    lsp_listbox.grid(row=row_+1, column=column_, columnspan=2,
                                sticky='W', padx=5)

    horizontal_scrollbar.config(command=lsp_listbox.xview)
    vertical_scrollbar.config(command=lsp_listbox.yview)

    lsp_listbox.insert(1, lsp.__repr__())

    lsp_listbox.bind("<<ListBoxSelect>>", set_active_lsp_from_listbox)
    lsp_listbox.bind("<Double-Button-1>", set_active_lsp_from_listbox)

    return lsp_listbox


def examine_selected_node():
    """Controls information displayed on node_tab"""

    # TODO - is this destroy needed?
    for thing in node_tab.grid_slaves():
        thing.destroy()

    # ### Display info in row 0 ######################################
    row1_frame = Frame(node_tab)
    row1_frame.grid(column=0, row=0, sticky='W',
                    padx=10, pady=10)


    #### Create a frame to show selected object info ####
    display_selected_items = display_selected_objects(row1_frame, 0, 4)
    display_selected_items.grid(padx=10, pady=10)

    #### Frame to choose a node ####
    choose_node_frame = LabelFrame(row1_frame)
    choose_node_frame.grid(row=0, column=0, padx=10, pady=10)
    # Label for choosing node
    Label(choose_node_frame, text="Choose a node:").grid(row=0, column=0,
                                                         sticky='W', pady=10)

    # Dropdown menu to choose a node
    node_choices_list = [node.name for node in model.node_objects]
    node_choices_list.sort()

    # Put the node selection button on the node_tab.
    # This option menu will call examine_selected_node when the choice is made.
    node_dropdown_select = OptionMenu(choose_node_frame, selected_node,
                                    *node_choices_list,
                                    command=set_active_object_from_option_menu)
    node_dropdown_select.grid(row=0, column=1, sticky='E')

    # Label to confirm selected Node
    Label(choose_node_frame, text="Selected node is:").grid(row=1, column=0, sticky='W')

    # Display the selected Node
    Label(choose_node_frame, text='-----------------------------------').\
                grid(row=1, column=1, sticky='E')
    Label(choose_node_frame, text=selected_node.get()).grid(row=1, column=1, sticky='E')

    ## Get selected_nodes Interfaces and display them in a listbox
    try:
        interface_choices = (interface for interface in \
                    model.get_node_object(selected_node.get()).interfaces(model))
    except:
        interface_choices = []
        pass

    #### Frame to display node's interfaces ####
    node_intf_frame = LabelFrame(row1_frame)
    node_intf_frame.grid(row=0, column=1)

    interface_info = [str(round((interface.utilization * 100),1))+'%   '+ interface.__repr__() for \
                    interface in interface_choices]

    display_interfaces("Selected Node's Interfaces", node_intf_frame,
                            interface_info, 0, 2)

    # #####################################################

    if selected_node.get() != '':
        #### Create a frame to node show demand info ####
        demands_frame = LabelFrame(node_tab, text="Node Demand Info")
        demands_frame.grid(column=0, row=4, columnspan=4, sticky='W', pady=10)

        # Display Demands Sourced From Node
        source_demand_choices = \
            model.get_demand_objects_source_node(selected_node.get())

        display_demands("Demands sourced from node", demands_frame,
                        source_demand_choices, 0,0)

        # Display Demands Destined To Node
        dest_demand_choices = model.get_demand_objects_dest_node(selected_node.get())

        display_demands("Demands destined to node", demands_frame,
                        dest_demand_choices, 0, 1)

        # #### Create a frame to show LSP info ####
        row5_frame = LabelFrame(node_tab, text="Node LSP Info")
        row5_frame.grid(column=0, row=5, columnspan=2, sticky='W',
                                padx=15, pady=10)

    # Display demands on interface
    # try:
    #     demands_on_interface = get_demands_on_interface(selected_interface.get())
    # except (ModelException, IndexError):
    #     interface_object=None
    #     demands_on_interface=[]
    # display_demands("Demands Egressing Selected Interface", row5_frame,
    #                     demands_on_interface, 0, 1)

    if selected_node.get() != '':
        node_name = selected_node.get()
        lsps_to_selected_node = [lsp for lsp in model.rsvp_lsp_objects
                                 if lsp.dest_node_object.name == node_name]
        lsps_from_selected_node = [lsp for lsp in model.rsvp_lsp_objects
                                   if lsp.source_node_object.name == node_name]

        from_node_lsps = display_list_of_things("LSPs from selected node", row5_frame,
                                                lsps_from_selected_node, 0, 0,
                                                set_active_lsp_from_listbox)
        to_node_lsps = display_list_of_things("LSPs to selected node", row5_frame,
                                              lsps_to_selected_node, 0, 2,
                                              set_active_lsp_from_listbox)
        to_node_lsps.grid(sticky="NEWS")
        from_node_lsps.grid(sticky="NEWS")

    # TODO - fail selected node


def examine_selected_demand():
    """
    Controls the display of information on demand_tab
    Displays a dropdown list on demand_tab, allowing user to select a demand.
    Displays selected objects on demand_tab
    Displays all paths for selected_demand on demand_tab
    Displays demands egressing selected_interface on demand_tab
    Displays demands on selected_lsp on demand_tab
    :return:
    """

    for thing in demand_tab.grid_slaves():
        thing.destroy()

    # Label for choosing interface
    top_row_frame = Frame(demand_tab)
    top_row_frame.grid(row=0, column=0, sticky='EW')
    Label(top_row_frame, text="Choose a demand:").grid(row=0, column=0, sticky='W', pady=10)

    # Dropdown menu to choose a demand
    demand_choices_list = [demand for demand in model.demand_objects]

    demand_choices_list_sorted = sorted(demand_choices_list,
                                key=lambda demand: demand.source_node_object.name)

    demand_dropdown_select = OptionMenu(top_row_frame, selected_demand,
                                        *demand_choices_list_sorted,
                                        command=set_active_object_from_option_menu)
    demand_dropdown_select.grid(row=0, column=1, sticky='W')
#    demand_dropdown_select.config(width=70) # hard codes the width

    # Display the selected objects
    display_selected_objects(top_row_frame, 0, 2)

    #### Display the selected demand's path(s) ####
    demand_path_parent_frame = Frame(demand_tab)
    demand_path_parent_frame.grid(row=3, column=0, columnspan=3, sticky='W')

    # demand_path_frame = LabelFrame(demand_path_parent_frame, text="Demand Path Info; displays all ECMP paths.")
    #
    # demand_path_frame.grid(row=3, column=0, sticky='NSEW', padx=10, pady=10) # Sticky NSEW keeps window from resizing
    # demand_path_frame.config(width=1200, height=225)
    # # These keep the demand_path_frame size consistent
    # demand_path_frame.grid_rowconfigure(0, weight=1)
    # demand_path_frame.grid_columnconfigure(0, weight=1)
    # demand_path_frame.grid_propagate(False)
    #
    # demand_path_frame.grid(row=3, column=0, padx=10, pady=10)

    try:
        demand_object = get_demand_object_from_repr(selected_demand.get())
        try:
            dmd_paths = demand_object.path
        # TODO - get rid of this catch by testing for path != 'Unrouted'
        except AttributeError:
            pass

        if isinstance(dmd_paths[0], RSVP_LSP):
            row_num = 0
            label_info = "LSPs that carry demand"
            display_list_of_things(label_info, demand_path_parent_frame,
                                   dmd_paths, row_num, 0,
                                   set_active_lsp_from_listbox)
        else:
            display_multiple_paths(dmd_paths, demand_path_parent_frame)

    # TODO - get rid of this catch by testing for selected_demand.get() != ''
    except (IndexError, UnboundLocalError):
        pass

    # Get demands on selected interface
    demands_on_interface = get_demands_on_interface(selected_interface.get())
    # Get demands on selected_lsp on demand_tab
    demands_on_lsp = get_demands_on_lsp(selected_lsp.get())

    row_4_frame = Frame(demand_tab)
    row_4_frame.grid(row=4, column=0, padx=10, pady=10)
    int_demands = display_demands("Demands Egressing Selected Interface", row_4_frame,
                        demands_on_interface, 0, 0)
    int_demands.grid(padx=10, pady=10)

    lsp_demands = display_demands("Demands on Selected LSP", row_4_frame,
                    demands_on_lsp, 0, 1)
    lsp_demands.grid(padx=10, pady=10)


def examine_selected_interface():
    """Controls display of information on interface_tab"""

    ## TODO - add reserved bandwidth to display
    ## TODO - add reservable bandwidth to display
    ## TODO - add LSPs on interface

    for thing in interface_tab.grid_slaves():
        thing.destroy()

    #### Filter to interfaces above a certain utilization ####
    utilization_frame = LabelFrame(interface_tab)
    utilization_frame.grid(row=0, column=0)
    utilization_pct = [x for x in range(0,100)]

    # Label for pct util selection
    pct_label = Label(utilization_frame, text=("Display interfaces with "
                                               "utilization % greater than:"))
    pct_label.grid(row=0, column=0, columnspan=2, sticky='W')
    pct_label.config(width=50)

    # Dropdown menu for pct util
    pct_dropdown_select = OptionMenu(utilization_frame, min_pct,
        *utilization_pct, command=set_active_object_from_option_menu)
    pct_dropdown_select.grid(row=0, column=4, sticky='W' )

    msg = "Interfaces above "+str(min_pct.get())+"% utilization"

    interface_list = [str(round((interface.utilization * 100),1))+'%   '\
+ interface.__repr__() for interface in model.interface_objects if \
((interface.utilization*100) >= min_pct.get())]

    interface_list.sort(key=lambda x: float(x.split('%')[0]))

    int_util = display_interfaces(msg, utilization_frame, interface_list, 2, 1)
    int_util.grid(sticky='W')

    selected_objects_int_tab = LabelFrame(interface_tab)
    selected_objects_int_tab.grid(row=0, column=6, padx=10, sticky='W')

    display_selected_objects(selected_objects_int_tab, 0, 8)


    # ##### Display demands and LSPs on selected_interface ##### #

    lsp_and_demand_egress_frame = Frame(interface_tab)
    lsp_and_demand_egress_frame.grid(row=2, column=0, padx=10, pady=10)

    demands_on_interface = get_demands_on_interface(selected_interface.get())

    demand_list = display_list_of_things("Demands Egressing Selected Interface",
                                         lsp_and_demand_egress_frame,
                                         demands_on_interface, 0, 0,
                                         set_active_demand_from_listbox)
    demand_list.grid(padx=10, pady=10)

    lsps_on_interface = get_lsps_on_interface(selected_interface.get())

    lsp_list = display_list_of_things("LSPs Egressing Selected Interface", lsp_and_demand_egress_frame,
                                      lsps_on_interface, 0, 1, set_active_lsp_from_listbox)
    lsp_list.grid(padx=10, pady=10)

    # TODO - fail selected interface


def examine_paths():
    """Controls display of information on path_tab"""

    # TODO - define all frames on path_tab in one area to keep track better

    for thing in path_tab.grid_slaves():
        thing.destroy()

    node_select_and_lsp_frame = LabelFrame(path_tab)
    node_select_and_lsp_frame.grid(row=0, column=0, sticky='W', padx=10, pady=10, rowspan=2, columnspan=3)

    #### Select source and dest nodes ####
    node_choices = [node.name for node in model.node_objects]
    node_choices.sort()

    src_node_select_frame = node_dropdown_select("Select a source node",
            node_choices, source_node, 0, 0, node_select_and_lsp_frame)
    src_node_select_frame.grid(sticky='W')

    dest_node_select = node_dropdown_select("Select a dest node",
            node_choices, dest_node, 1, 0, node_select_and_lsp_frame)
    dest_node_select.grid(sticky='W')

    if source_node.get() != '' and dest_node.get() != '':
        # Display all LSPs between source/dest nodes
        # Create a frame to hold the LSPs
        shortest_path = model.get_shortest_path(source_node.get(), dest_node.get())
        lsp_frame = LabelFrame(node_select_and_lsp_frame, text="LSPs between source/dest nodes; "
                               "shortest path cost = {}".format(shortest_path['cost']))
        lsp_frame.grid(row=0, column=1, sticky='W', padx=30, pady=10, rowspan=2)

        # Get LSPs
        lsps = (lsp for lsp in model.rsvp_lsp_objects if (lsp.source_node_object.name == source_node.get() and
                                                          lsp.dest_node_object.name == dest_node.get()))

        display_list_of_things('', lsp_frame, lsps, 0, 0, set_active_lsp_from_listbox)


        #### Display shortest path(s) ####
        # Find shortest paths
        try:
            shortest_path = model.get_shortest_path(source_node.get(), dest_node.get())

            paths = shortest_path['path']
            cost = shortest_path['cost']

            # Create a frame to hold the shortest path(s)
            shortest_path_frame = LabelFrame(path_tab, text="Shortest Paths ({})".format(len(paths)))
            shortest_path_frame.grid(row = 2, column = 0, sticky='W', padx=10)

            column_counter = 0
            path_counter = 0

            for path in paths:
                list_of_interfaces = path
                label = "Shortest Path %s, cost = %s"%(str(path_counter),
                                                                str(cost))
                display_interfaces(label, shortest_path_frame, list_of_interfaces,
                    1, column_counter)
                column_counter += 2
                path_counter += 1

        # TODO - this catch may not be necessary given the if statement it's nested in
        except ModelException as e:
            pass

        #### Display all paths ####
        # Note - python, wtf?! Getting the horizontal scrollbar to work with
        # multiple listboxes was WAY more difficult than it should have been
        try:
            all_paths = model.get_feasible_paths(source_node.get(),
                                                            dest_node.get())

            # Create label frame to hold the feasible path(s) # frame_canvas
            feasible_path_frame = LabelFrame(path_tab, text="All Feasible Paths ({})".format(len(all_paths)))
            feasible_path_frame.grid(row=3, column=0, padx=10, pady=10)

            feasible_path_frame.config(width=1200, height=220)

            feasible_path_frame.grid_rowconfigure(0, weight=1)
            feasible_path_frame.grid_columnconfigure(0, weight=1)
            feasible_path_frame.grid_propagate(False)

            display_multiple_paths(all_paths, feasible_path_frame)

        # TODO - this catch may not be necessary given the if statement it's nested in
        except ModelException as e:
            pass


def display_multiple_paths(paths, frame):
    """
    Displays multiple paths horizontally, each path within its own Frame,
    which will have a horizontal scrollbar for the path.
    Path Frames will be arranged horizontally within a Canvas object; the
    Canvas object will have a horizontal scrollbar to view all Path Frames.
    :param paths: list of paths to display
    :param frame: Frame that supports the scrollbar and Canvas to display paths
    :return: None
    """

    # Canvas within frame object; this canvas can hold multiple path_frames.
    # This Canvas will have a horizontal scrollbar
    canvas = Canvas(frame)
    canvas.grid(row=0, column=0, sticky='NEWS')

    # Horizontal Scrollbar
    horizontal_scrollbar = Scrollbar(frame, orient=HORIZONTAL,
                                     command=canvas.xview)
    horizontal_scrollbar.grid(row=4, column=0, sticky='ew')
    canvas.configure(xscrollcommand=horizontal_scrollbar.set)
    # Create a frame to house the path(s)
    path_frame = Frame(canvas)  # frame_buttons
    canvas.create_window((0, 0), window=path_frame, anchor='nw')
    column_counter = 0
    path_counter = 0
    for path in paths:
        cost = 0
        for intf in path:
            cost += intf.cost
        list_of_interfaces = path
        label = "Path {}, cost = {}".format(str(path_counter), cost)

        # display_interfaces(label, path_frame, list_of_interfaces,
        #                    1, column_counter)
        display_list_of_things(label, path_frame, list_of_interfaces,
                               1, column_counter, set_active_interface_from_listbox)

        column_counter += 2
        path_counter += 1
    # These next 3 things need to be in this order or the horizontal
    # scrollbar for the multiple listboxes doesn't work; holy cow, python,
    # it shouldn't be this difficult
    path_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def node_dropdown_select(label, node_choices, target_variable, row_, column_, canvas_object):
    """
    Creates a labelframe with a node select option menu
    :param label: text displayed above the dropdown
    :param node_choices: list of nodes
    :param target_variable: variable to be selected from list
    :param row_: row number
    :param column_: column number
    :param canvas_object: LabelFrame to place this menu in to
    :return:
    """
    #### Frame to choose a node ####
    choose_node_frame = LabelFrame(canvas_object)
    choose_node_frame.grid(row=row_, column=column_, padx=10, pady=10)
    # Label for choosing node
    Label(choose_node_frame, text=label).grid(row=0, column=0, sticky='W',
                                              pady=10)

    # Dropdown menu to choose a node
#    node_choices_list = node_choices

    # Put the node selection button on the node_tab.
    # This option menu will call examine_selected_node when the choice is made.
    node_dropdown_select = OptionMenu(choose_node_frame, target_variable,
                                    *node_choices,
                                    command=set_active_object_from_option_menu)
    node_dropdown_select.grid(row=0, column=1, sticky='E')

    # Label to confirm selected Node
    Label(choose_node_frame, text="Selected node is:").grid(row=1, column=0, sticky='W')

    # Display the selected Node
    Label(choose_node_frame, text='-----------------------------------').\
                grid(row=1, column=1, sticky='E')
    Label(choose_node_frame, text=target_variable.get()).grid(row=1, column=1, sticky='E')

    return choose_node_frame


# ###############################
# ####   LSP Tab Functions   ####
# ###############################
def lsp_dropdown_select(label, lsp_choices, target_variable, row_, column_):
    """
    Creates a labelframe with a lsp select option menu
    :param label: label for lsp_frame
    :param lsp_choices: list of LSPs to select from
    :param target_variable: selected_lsp; will be used to get selected_lsp value
    :param row_: row on lsp_tab for menu
    :param column_: column on lsp_tab for menu
    :return: frame for choosing an LSP
    """
    # Frame to choose a node
    choose_lsp_frame = LabelFrame(lsp_tab)

    choose_lsp_frame.grid(row=row_, column=column_, padx=10, pady=10)
    # Label for choosing node
    Label(choose_lsp_frame, text=label).grid(row=0, column=0, sticky='W',
                                              pady=10)

    # Dropdown menu to choose an lsp
#    lsp_choices_list = lsp_choices

    # Put the node selection button on the node_tab.
    # This option menu will call examine_selected_node when the choice is made.
    lsp_dropdown_select = OptionMenu(choose_lsp_frame, target_variable,
                                     *lsp_choices,
                                     command=set_active_object_from_option_menu)
    lsp_dropdown_select.grid(row=0, column=1, sticky='E')

    # Label to confirm selected Node
    Label(choose_lsp_frame, text="Selected lsp is:").grid(row=1, column=0, sticky='W')

    # Display the selected Node
    Label(choose_lsp_frame, text='-----------------------------------'). \
        grid(row=1, column=1, sticky='E')
    Label(choose_lsp_frame, text=target_variable.get()).grid(row=1, column=1, sticky='E')

    return choose_lsp_frame


def set_active_lsp_from_listbox(event):
    """
    Sets the selected lsp value from a listbox to the active_lsp
    :param event: event
    :return:
    """

    w = event.widget
    value_position = (w.curselection())  # get the position of the current selection
    selected_lsp.set(w.get(value_position))  # set selected_lsp to the current selection

    for thing in demand_tab.grid_slaves():
        thing.destroy()
    for thing in node_tab.grid_slaves():
        thing.destroy()
    for thing in interface_tab.grid_slaves():
        thing.destroy()
    for thing in lsp_tab.grid_slaves():
        thing.destroy()

    # examine_selected_node()
    # examine_selected_demand()
    # examine_selected_interface()
    # examine_selected_lsp()
    # examine_paths()
    update_tabs()


def examine_selected_lsp():
    """
    Controls the display of information on the lsp_tab
    :return:
    """

    display_selected_objects(lsp_tab, 0, 1)

    #### Frame to choose an LSP ####
    choose_lsp_frame = LabelFrame(lsp_tab)
    choose_lsp_frame.grid(row=0, column=0, padx=10, pady=10)
    # Label for choosing LSP
    Label(choose_lsp_frame, text="Choose an LSP:").grid(row=0, column=0, sticky='W',
                                                        pady=10)

    # Dropdown menu to choose LSP
    lsp_choices_list = [lsp for lsp in model.rsvp_lsp_objects]

    # Sort the LSP list by source_node
    lsp_choices_list_sorted = sorted(lsp_choices_list, key=lambda lsp: lsp.source_node_object.name)

    # Display menu to select LSP
    lsp_dropdown_select = OptionMenu(choose_lsp_frame, selected_lsp,
                                     *lsp_choices_list_sorted,
                                     command=set_active_object_from_option_menu)

    # Specify position of menu to select LSP
    lsp_dropdown_select.grid(row=0, column=1, sticky='NW')

    if selected_lsp.get() != '':
        lsp_object = get_lsp_object_from_repr(selected_lsp.get())
        lsp_reserved_bw = lsp_object.reserved_bandwidth

        demands_on_lsp = get_demands_on_lsp(selected_lsp.get())

        display_demands("Demands on Selected LSP (reserved bandwidth = {})"
                        .format(lsp_reserved_bw), lsp_tab,
                        demands_on_lsp, 4, 0)

        path = get_lsp_object_from_repr(selected_lsp.get()).path
        path_ints = path['interfaces']
        path_cost = path['path_cost']
        baseline_path_reservable_bw = path['baseline_path_reservable_bw']
        label = ("LSP path info: cost = {}, baseline_path_reservable_bw = "
                 "{}".format(path_cost, baseline_path_reservable_bw))

        # TODO - specify dimensions of display_interfaces box; right here it looks weird
#        display_interfaces(label, lsp_tab, path_ints, 5, 0)
        display_list_of_things(label, lsp_tab, path_ints, 5, 0,
                               set_active_interface_from_listbox)


def get_demands_on_lsp(selected_lsp_get):
    """
    Returns a list of demands on selected_lsp
    :param selected_lsp_get: selected_lsp.get()
    :return: list of demands on the selected_lsp
    """

    try:
#        lsp_data = selected_lsp.split("'")
#        lsp_name = lsp_data[1]
#        lsp_source = lsp_data
#        lsp_dest = lsp_data

#        pdb.set_trace()

        lsp_object = get_lsp_object_from_repr(selected_lsp_get)
        demands_on_lsp = lsp_object.demands_on_lsp(model)

    # These exceptions have to be caught
    # AttributeError - so demands_on_lsp does not error out when selected_lsp is None
    except (ModelException, IndexError, AttributeError):
        demands_on_lsp = []

    return demands_on_lsp


def get_lsp_object_from_repr(lsp_repr):
    """
    Returns RSVP_LSP object from the associated repr for the object
    :param lsp_repr: RSVP_LSP.__repr__()
    :return: Associated RSVP_LSP object
    """

    try:
        lsp_info = re.split(', | |\)', lsp_repr)
        lsp_name = lsp_info[8][1:-1]
        lsp_source = lsp_info[2]
        lsp_dest = lsp_info[5]
        lsp_object = model.get_rsvp_lsp(lsp_source, lsp_dest, lsp_name)

        return lsp_object
    except IndexError:
        pass

# Establish the canvas
ui_window = Tk()
ui_window.title('Network modeler UI')
ui_window.geometry('1600x750')
ui_window.resizable(1,1) ###

# Create a tabbed notebook in the canvas ui_window
nb = ttk.Notebook(ui_window) # Creates ttk notebook in ui window

# Establish names for key elements in the notebook
selected_demand = StringVar(nb)
selected_node = StringVar(nb)
selected_interface = StringVar(nb)
selected_model_file = StringVar(nb)
selected_lsp = StringVar(nb)
source_node = StringVar(nb)
dest_node = StringVar(nb)
network_graph_file = StringVar(nb)

model = None
min_pct = IntVar(nb) # Min percent utilization to search over interfaces for

# Notebook grid spans 70 columns and 69 rows and spreads out the notebook
# in all directions
nb.grid(row=1, column=0, columnspan=80, rowspan=69, sticky='NESW')

rows = 0
while rows < 70:
    ui_window.rowconfigure(rows, weight=1)
    ui_window.columnconfigure(rows, weight=1)
    rows += 1

#### File Open Tab ####
# Open a model file
open_file_tab = ttk.Frame(nb)
nb.add(open_file_tab, text="Open Model File")

# Establish a frame label
label_frame = ttk.LabelFrame(open_file_tab, text="Select a Network Model File")
label_frame.grid(column=0, row=0, padx=8, pady=8, sticky='W')

# Make a button to load a file
load_file_button = ttk.Button(open_file_tab)
load_file_button["text"] = "Push button to load network model file"
load_file_button.grid(row=11, column=0, sticky='W')
load_file_button["command"] = open_file

#### Node Tab ####
node_tab = ttk.Frame(nb)
nb.add(node_tab, text="Node Explorer")

#### Demand Tab ####    
demand_tab = ttk.Frame(nb)
nb.add(demand_tab, text="Demand Explorer")

#### LSP Tab ####
lsp_tab = ttk.Frame(nb)
nb.add(lsp_tab, text="RSVP LSP Explorer")

#### Interface Tab ####
interface_tab = ttk.Frame(nb)
nb.add(interface_tab, text="Interface Explorer")

#### Paths Tab ####
path_tab = ttk.Frame(nb)
nb.add(path_tab, text="Path Explorer")

ui_window.mainloop()
    
    
    
    
