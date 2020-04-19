Examples
=========

Demo scripts
----------------

The UI (simple_user_interface.py) is specifically designed to circuit_id common modeling use cases

* explore the network topology and mine data
* provide quick linkage between related objects: Nodes, interfaces, and demands (traffic)
* allow the user to explore the shortest paths and all feasible (loop free) paths between selected nodes
* examine traffic on interfaces above a specified utilization percentage
* examine path(s) for a demand as it transits the WAN

The lsp_practice_code.py script demos how auto-bandwidth RSVP LSPs react to

* link failures
* adding traffic
* adding additional LSPs

The network_modeling_client_code_examples_read_from_*.py files demo the following:

* loading a network topology from a list or from a file
* an included interactive visualization of the network

  - tooltips showing interface name and utilization
  - interface colors indicating utilization range
  - an interactive legend that allows user to select which interface utilization ranges to view
  - ability to move objects
* addition of new circuit and node to the network
* viewing interface traffic
* getting the shortest path
* failing an interface
* demand path changes before/after a link failure
* adding traffic


The examples folder includes an interactive network visualization allowing user to

* view the network
* move nodes
* get tooltips via hovering over links
* filter to visualizing only links in certain utilization ranges

