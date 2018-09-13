"""Simple, menu-driven UI for network_modeling module.
Allows users to interact with and relate between associated
demands, interfaces, and nodes."""

from network_modeling import Model
from network_modeling import ModelException
from network_modeling import Interface
from network_modeling import Demand
from network_modeling import Node 
from network_modeling import graph_network
 
from tkinter import ttk as ttk
from tkinter import *
from tkinter import filedialog

import re

import pdb

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
                
        # Update the Node Explorer tab
        examine_selected_node()
        
        # Update the Demand Explorer tab
        examine_selected_demand()
        
        # Update the Interface Explorer tab
        examine_selected_interface()
        
        # Update the Path Explorer tab
        examine_paths()

    # Create a button to produce a network graph
    graph_network_button = Button(label_frame)
    graph_network_button.grid(row=12, column=0, padx=5, pady=5, sticky='W')
    graph_network_button["text"] = "Push to create network graph"
    # Don't add the trailing () or this will execute immediately/automatically

    graph_network_button["command"] = create_network_graph_and_refresh 
    
    if network_graph_file.get() != '':
        graph_label_text = "Graph file saved at: "+network_graph_file.get()
        graph_file_label = Label(label_frame, text=graph_label_text)
        graph_file_label.grid(row=13, column=0, sticky='W')
    
    
        
        



def create_network_graph():
    """Makes a network graph"""


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
     
        
def set_active_interface_from_listbox(event):
    """Sets the selected interface value from a listbox to the 
    active_interface"""
    w = event.widget
    print(w) #debug
    value = (w.curselection()) # TODO -- comment this out and test
    value_position = (w.curselection())
    
    # This next part takes the first value in case the listbox has 
    # extra info trailing the interface
    value_in_position = w.get(value_position)
    
    # Use interface repr, so splitting that using split() yields interface
    # name in position 2
    selected_interface_value = value_in_position
    
    selected_interface.set(selected_interface_value)
    print(selected_interface.get())#debug
    
    # Refresh the tabs
    # TODO - add the destroy() function?
    examine_selected_node()
    examine_selected_demand()
    examine_selected_interface()

def set_active_demand_from_listbox(event):
    """Sets the selected demand value from a listbox to the active_demand"""
    w = event.widget
    print(w) #debug
    value = (w.curselection()) # get the current selection
    value_position = (w.curselection()) # get the position of the current selection
    selected_demand.set(w.get(value_position)) # set selected_demand to the current selection
    print(selected_demand.get())#debug 
    
    # Try to delete the Node Demand Info labelframe to clear the demand paths
    for thing in demand_tab.grid_slaves():
        thing.destroy()
    for thing in node_tab.grid_slaves():
        thing.destroy()
    for thing in interface_tab.grid_slaves():
        thing.destroy()
        
    # Refresh the Node Info and Demand Info tabs        
    examine_selected_node()
    examine_selected_demand()
    examine_selected_interface()
    

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
    #for thing in path_tab.grid_slaves():
        #thing.destroy()
    
    # Refresh the Node Info and Demand Info tabs
    examine_selected_node()
    examine_selected_demand()
    examine_selected_interface()
    examine_paths()
    
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
        
def get_demands_on_interface(interface):
    """Returns a list of demands on the specified interface"""

    # Display demands on interface
    try:
        interface_data = interface.split("'")
        interface_name = interface_data[1]
        node_name = interface_data[3]
        
        interface_object = model.get_interface_object(interface_name, 
                                                        node_name)
        demands_on_interface = interface_object.demands(model)
    except (ModelException, IndexError):
        interface_object=None
        demands_on_interface=[]
        
    return demands_on_interface
    
def display_selected_objects(canvas_object, row_, column_):
    """Displays the selected objects"""
 
    node_status = 'Unknown'
    interface_status = 'Unknown'
    demand_status = 'Unknown'
    interface_info = 'Unknown'

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
       
        interface_info = interface_object
       
        if interface_failed == True:
            interface_status = 'Failed'
        else:
            interface_status = interface_util+"% utilized"
        
    except (ModelException, AttributeError, IndexError) as e:
        pass    
        
    try:
        demand_object = get_demand_object_from_repr(selected_demand.get())
        demand_routed = demand_object.path 

        if demand_routed == 'Unrouted':
            demand_status = 'Unrouted'
        else:
            demand_status = 'Routed'
    except (ModelException, AttributeError):
        pass


    selected_object_frame = LabelFrame(canvas_object, 
                                text="Selected Interface, Demand, and Node")
    selected_object_frame.grid(column=column_, row=row_, columnspan=3, pady=10)
    selected_object_frame.column_width=40
    selected_object_frame.columnconfigure(0, weight=1)
    selected_object_frame.columnconfigure(1, weight=2)
    selected_object_frame.columnconfigure(2, weight=1)
    
    Label(selected_object_frame, text='Name').grid(row=row_+1, column=1)
    Label(selected_object_frame, text='Status').grid(row=row_+1, column=2)
    
    Label(selected_object_frame, text="Selected Node:").grid(row=row_+2, 
                                                column=0, sticky='W')
    Label(selected_object_frame, text=selected_node.get(), width=52, 
                borderwidth=1, relief="solid").grid(row=row_+2, column=1)
    Label(selected_object_frame, text=node_status,).grid(row=row_+2, 
                                                        column=2, sticky='E')
                                                        
    Label(selected_object_frame, text="Selected Interface:").grid(row=row_+3, 
                                                    column=0, sticky='W')
    Label(selected_object_frame, text=selected_interface.get(), 
        width=52, justify=LEFT, wraplength=450, borderwidth=1, 
        relief="solid").grid(row=row_+3, column=1)
    Label(selected_object_frame, text=interface_status).grid(row=row_+3,
                                                        column=2, sticky='E')
                                                        
    Label(selected_object_frame, text="Selected Demand:").grid(row=row_+4, 
                                                    column=0, sticky='W')
    Label(selected_object_frame, text=selected_demand.get(), width=52, 
        borderwidth=1, wraplength=450, relief="solid").grid(row=row_+4, 
                                                        column=1)   
    Label(selected_object_frame, text=demand_status).grid(row=row_+4, 
                                                        column=2, sticky='E') 
    
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
    for demand in list_of_demands:
        demand_listbox.insert(demand_counter, demand)
        demand_counter += 1
        
    demand_listbox.bind("<<ListBoxSelect>>", set_active_demand_from_listbox)
    demand_listbox.bind("<Double-Button-1>", set_active_demand_from_listbox) 

def display_interfaces(label_info, canvas_object, list_of_interfaces,
                        row_, column_):
    """Displays interfaces from list of interfaces in single selectable listbox.
    A label with label_info will appear above the listbox."""
    # Display Node's Interfaces Label
    Label(canvas_object, text=label_info).grid(row=row_, column=column_, 
                                                sticky='W', padx=5)

    # Vertical scrollbar
    vertical_scrollbar = Scrollbar(canvas_object, orient=VERTICAL)
    vertical_scrollbar.grid(row=row_+1, column=column_+2, sticky=N+S)
    
    # Horizontal scrollbar - TODO create decorator for the scrollbar?
    horizontal_scrollbar = Scrollbar(canvas_object, orient=HORIZONTAL)
    horizontal_scrollbar.grid(row=(row_+2), column=column_, sticky=E+W,
                            columnspan=2)
                                                        
    # Create a listbox with the available interfaces for the Node
    interfaces_listbox = Listbox(canvas_object, selectmode='single', 
                height = 8, width=40, xscrollcommand=horizontal_scrollbar.set,
                yscrollcommand=vertical_scrollbar.set)
    interfaces_listbox.grid(row=row_+1, column=column_, columnspan=2, 
                                sticky='W', padx=5)

    horizontal_scrollbar.config(command=interfaces_listbox.xview)
    vertical_scrollbar.config(command=interfaces_listbox.yview)
    
    intf_counter = 1

    for intf_name in list_of_interfaces:
        interfaces_listbox.insert(intf_counter, intf_name)
        intf_counter += 1

    interfaces_listbox.bind("<<ListBoxSelect>>", set_active_interface_from_listbox)
    interfaces_listbox.bind("<Double-Button-1>", set_active_interface_from_listbox) 

    return interfaces_listbox

def examine_selected_node(*args):
    """Examine the selected_node"""
    
    #### Frame to choose a node ####
    choose_node_frame = LabelFrame(node_tab)
    choose_node_frame.grid(row=0, column=0, padx=10, pady=10)
    # Label for choosing node
    Label(choose_node_frame, text="Choose a node:").grid(row=0, column=0, sticky='W', 
                                                pady=10)

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
    node_intf_frame = LabelFrame(node_tab)
    node_intf_frame.grid(row=0, column=1)
    
    interface_info = [str(round((interface.utilization * 100),1))+'%   '+ interface.__repr__() for \
                    interface in interface_choices]

    interface_listbox = display_interfaces("Node's Interfaces", node_intf_frame, 
                            interface_info, 0, 2)
                            
    #### Create a frame to node show demand info ####
    demands_frame = LabelFrame(node_tab, text="Node Demand Info")
    demands_frame.grid(column=0, row=4, columnspan=4, sticky='W', pady=15)

    # Display Demands Sourced From Node 
    source_demand_choices = \
        model.get_demand_objects_source_node(selected_node.get())
        
    display_demands("Demands sourced from node", demands_frame,
                    source_demand_choices, 0,0)

    # Display Demands Destined To Node 
    
    dest_demand_choices = model.get_demand_objects_dest_node(selected_node.get())
    
    display_demands("Demands destined to node", demands_frame, 
                    dest_demand_choices, 0, 1)

    #### Create a frame to show interface demand info ####
    intf_demands_frame = LabelFrame(node_tab, text="Interface Demand Info")
    intf_demands_frame.grid(column=5, row=4, columnspan=2, sticky='W', 
                            padx=15, pady=15)
    
    # Display demands on interface
    try:
        demands_on_interface = get_demands_on_interface(selected_interface.get())       
    except (ModelException, IndexError):
        interface_object=None
        demands_on_interface=[]
    
    display_demands("Demands Egressing Selected Interface", intf_demands_frame, 
                        demands_on_interface, 0, 1)
  
    #### Create a frame to show selected object info ####
    display_selected_objects(node_tab, 0, 4)
    

    # TODO - fail selected interface or node    
    

def examine_selected_demand(*args):
    """Examine selected_interface object"""
    
    # Label for choosing interface
    choose_demand_label = Label(demand_tab, 
        text="Choose a demand:").grid(row=0, column=0, sticky='W', pady=10)

    # Dropdown menu to choose a demand
    demand_choices_list = [demand for demand in model.demand_objects]

    demand_choices_list_sorted = sorted(demand_choices_list, 
                                key=lambda demand: demand.source_node_object.name)

    demand_dropdown_select = OptionMenu(demand_tab, selected_demand, 
                                    *demand_choices_list_sorted,
                                    command=set_active_object_from_option_menu)
    demand_dropdown_select.grid(row=0, column=1, sticky='EW')
 
    # Display the selected objects
    display_selected_objects(demand_tab, 0, 3)

    #### Display the selected demand's path(s) ####

    demand_path_frame = LabelFrame(demand_tab, 
                    text="Demand Path Info (Ordered hops from source to destination)")
    demand_path_frame.grid(row=3, column=0, columnspan=10, sticky='W', 
                            padx=10, pady=10)
    
    try:
       
        demand_object = get_demand_object_from_repr(selected_demand.get())
        
        try:
            dmd_paths = demand_object.path
        except AttributeError:
            pass
        
        column_num = 0
        
        for path in dmd_paths:
            label_info = "Demand hops ordered from source to dest"
            
            interface_info = [str(round((interface.utilization * 100),1))\
                    +'%   '+ interface.__repr__() for interface in path]
                    
            display_interfaces(label_info, demand_path_frame, 
                                    interface_info, 0, column_num)
            column_num += 3
        
    except (IndexError, UnboundLocalError):
        pass
        
    demands_on_interface = get_demands_on_interface(selected_interface.get())               

    demands_on_int = display_demands("Demands Egressing Selected Interface", demand_tab, 
                        demands_on_interface, 4, 3)
        
def examine_selected_interface(*args):
    """Allows user to explore interfaces with different characteristics"""
    
    #### Filter to interfaces above a certain utilization ####
    utilization_frame = LabelFrame(interface_tab)
    utilization_frame.grid(row=0, column=0)
    utilization_pct = [x for x in range(0,100)]
    
    # Label for pct util selection
    pct_label = Label(utilization_frame, text="Select the minimum interface \
percent to filter against:")
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
    
    demands_on_interface = get_demands_on_interface(selected_interface.get())               

    intf_demands = display_demands("Demands Egressing Selected Interface", interface_tab, 
                        demands_on_interface, 6, 0)
 
def examine_paths(*args):
    """Allows user to examine shortest paths and all paths between the
    selected source and destination nodes in the Model"""

    #### Select source and dest nodes ####
    node_choices = [node.name for node in model.node_objects]
    node_choices.sort()
    
    src_node_select_frame = node_dropdown_select("Select a source node",
            node_choices, source_node, 0, 0)
    src_node_select_frame.grid(sticky='W')
            
    dest_node_select = node_dropdown_select("Select a dest node", 
            node_choices, dest_node, 1, 0)
    dest_node_select.grid(sticky='W')
    
    #### Display shortest path(s) ####
    
    # Find shortest paths
    try:
        source_node_object = model.get_node_object(source_node.get())
        dest_node_object = model.get_node_object(dest_node.get())
      
        shortest_path = model.get_shortest_path(source_node.get(), 
                                                        dest_node.get())
        
        paths = shortest_path['path']
        cost = shortest_path['cost']
            
        # Create a frame to hold the shortest path(s)
        shortest_path_frame = LabelFrame(path_tab, text="Shortest Paths")
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
          
    except ModelException:
        pass

    #### Display all paths ####
    # Note - python, wtf?! Getting the horizontal scrollbar to work with
    # multiple listboxes was WAY more difficult than it should have been
    try:
        source_node_object = model.get_node_object(source_node.get())
        dest_node_object = model.get_node_object(dest_node.get())
        
        all_paths = model.get_feasible_paths(source_node.get(), 
                                                        dest_node.get())

        # Create label frame to hold the feasible path(s) # frame_canvas
        feasible_path_frame = LabelFrame(path_tab, text="All Paths")
        feasible_path_frame.grid(row = 3, column = 0, padx=10, pady=10)
        
        feasible_path_frame.grid_rowconfigure(0, weight=1)
        feasible_path_frame.grid_columnconfigure(0, weight=1)
        feasible_path_frame.grid_propagate(False)

        # canvas
        feasible_path_canvas = Canvas(feasible_path_frame)
        feasible_path_canvas.grid(row=0, column=0, sticky='news')

        # Horizontal Scrollbar
        horizontal_scrollbar = Scrollbar(feasible_path_frame, orient=HORIZONTAL,
                    command=feasible_path_canvas.xview)
        horizontal_scrollbar.grid(row=4, column=0, sticky='ew')
        feasible_path_canvas.configure(xscrollcommand=horizontal_scrollbar.set)   
             
        # Create a frame to house the path(s)
        path_frame = Frame(feasible_path_canvas) # frame_buttons
        feasible_path_canvas.create_window((0,0), window=path_frame, 
                                                        anchor='nw')
                
        column_counter = 0
        path_counter = 0

        for path in all_paths:
            list_of_interfaces = path
            label = "Feasible Path %s"%(str(path_counter))
            display_interfaces(label, path_frame, list_of_interfaces,
                1, column_counter)
            column_counter += 2
            path_counter += 1 
            
        # These next 3 things need to be in this order or the horizontal 
        # scrollbar for the multiple listboxes doesn't work; holy cow, python,
        # it shouldn't be this difficult    
        path_frame.update_idletasks() 
        feasible_path_frame.config(width=1200, height=300)
        feasible_path_canvas.config(scrollregion=feasible_path_canvas.bbox("all"))

    except ModelException:
        pass    

def node_dropdown_select(label, node_choices, target_variable, row_, column_):
    """"Creates a labelframe with a node select option menu"""
    #### Frame to choose a node ####
    choose_node_frame = LabelFrame(path_tab)
    choose_node_frame.grid(row=row_, column=column_, padx=10, pady=10)
    # Label for choosing node
    Label(choose_node_frame, text=label).grid(row=0, column=0, sticky='W', 
                                                pady=10)

    # Dropdown menu to choose a node
    node_choices_list = node_choices

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


# Establish the canvas
ui_window = Tk()
ui_window.title('Network modeler UI')
ui_window.geometry('1600x750')
ui_window.resizable(1,1) ###

# Create a tabbed notebook in the canvas ui_window
nb = ttk.Notebook(ui_window) # Creates ttk notebook in ui window

# Establish names for selected demand, node, and interface in the notebook
selected_demand = StringVar(nb)
selected_node = StringVar(nb)
selected_interface = StringVar(nb)
selected_model_file = StringVar(nb)
source_node = StringVar(nb)
dest_node = StringVar(nb)
network_graph_file = StringVar(nb)


#selected_model_file.set(None)

model = None
min_pct = IntVar(nb) # Min percent utilization to search over interfaces for

# Notebook grid spans 70 columns and 69 rows and spreads out the notebook
# in all directions
nb.grid(row=1, column=0, columnspan=70, rowspan=69, sticky='NESW') 

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
# Create a new tab and add it to the notebook
node_tab = ttk.Frame(nb)
nb.add(node_tab, text="Node Explorer")

#### Demand Tab ####    
# Create a new tab and add it to the notebook
demand_tab = ttk.Frame(nb)
nb.add(demand_tab, text="Demand Explorer")

# TODO - Interface Tab with list of top utilized interfaces 
# and be able to set utilization % and see all ints that exceed it
#### Interface Tab ####
interface_tab = ttk.Frame(nb)
nb.add(interface_tab, text="Interface Explorer")

#### Create Paths Tab ####
path_tab = ttk.Frame(nb)
nb.add(path_tab, text="Path Explorer")


ui_window.mainloop()   
    
    
    
    
