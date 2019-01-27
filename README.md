# network_traffic_modeler_py3
This is the network traffic modeler written in python 3.  Version 1.2.  All further updates to network_traffic_modeler will be in python3 and in this repository.

The big adds in this commit are:
- the addition of a simple, menu-based UI.  Simply download this repository and run the simple_user_interface.py script.  Load up either of the sample network models.  
- a standardized file format for the network model data
- ability to load a model from a network model file

The UI is specifically designed to address common modeling use cases:
- provide quick linkage between related objects: Nodes, interfaces, and demands (traffic)
- allow the user to explore the shortest paths and all feasible (loop free) paths between selected nodes
- examine traffic on interfaces above a specified utilization percentage


=======
    - move interface endpoints for better viewing
    - filter visualization to interfaces with a certain % utilization(s)
    - zoom and pan 

This code allows users to define a layer 3 network topology, define a traffic
matrix, and then run a simulation to determine how the traffic will traverse
the topology.  If you've used Cariden MATE or WANDL, this code solves for
some of the same basic use cases those do (but those solve for much
more as well).

Changes to the topology can be done to simulate new routers, circuits,
circuit capacity, network failures, etc.
Changes to the traffic matrix can be done to simulate increases/decreases
in existing traffic or additional traffic matrix entries.

**TO GET STARTED:
- Simply run one of the client code examples from the CLI
- OR - To use the simple UI:
    - Run simple_user_interface.py from the CLI
    - When prompted in the UI, load the sample_network_model_file.csv file
    - Explore the network topology and traffic paths in the UI using the various tabs 
      dropdown menus on each tab

=============ADDED FEATURES==========

Completed enhancements since last release
- make interactive network plot - done
- for network graph, have option to only show circuits with interfaces above a 
  certain % utilization (important for scaled networks) - done
- new client code that uses the load_model call - done



Use cases include:
  - simulating how traffic will transit your layer 3 network, given a
  traffic matrix
  - simulating how your traffic will failover if any link(s) or node(s) fail
  - simulating how a given network augment will affect link utilization
  and traffic flow; possible augments include: 
    - adding a new link
    - adding a new node with links
    - changing a link's capacity
    - adding a new traffic matrix entry (demand) to the traffic matrix
    - increasing/decreasing the magnitude of an existing demand in the traffic matrix failover       

NOTES:
- interface addresses are only used to match interfaces into circuits and do
not have any practical bearing on the simulation results

Capabilities TO DO:
- Add RSVP auto-bandwidth capabilities
- Enable UI to fail nodes/interfaces

Use Cases TO DO:
- Specific Model calls to
    - Remove a Node
    - Remove an Interface/Circuit
    - Remove a demand
    - Change demand magnitude
    *** These can all be done now, but require a few API calls to do so

Needed optimizations:
- add guardrails to Demand and Interface attributes (traffic must be a float), etc
