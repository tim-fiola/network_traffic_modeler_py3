# network_traffic_modeler_py3

A set of native python APIs to create a network model and run
network simulations.       

There are no implied or explicit warranties associated with this app.

**This code now features an interactive network graph capability that lets the
user:
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
=========================================================

Currently this modeling code supports simple OSPF/ISIS routing and only layer 3.  
There is no RSVP or layer 1 SRLG support at the moment, but that is in development.

This code should perform well at scale as it leverages path calculations 
from the networkx module.

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
    - increasing/decreasing the magnitude of an existing demand in the 
      traffic matrix failover       

NOTES:
- interface addresses are only used to match interfaces into circuits and do
  not have any practical bearing on the simulation results


======== TODO ===========

simple_user_interface.py TODO:
- Select multiple points on interactive graph and drag to new position
- better notification to user if model file has a problem in simple ui
- fail node or interface from simple ui
- add demand from simple ui
- remove demand from simple ui
- add circuit from simple ui
- remove circuit from simple ui
- add node from simple ui
- remove node from simple ui
- save model from simple ui

API TODO:
- a save_model call
- optimize model convergence by creating a networkx model once and routing
  demands across it versus the current method that creates the networkx topology
  for each demand
- new client code that uses a save_model call
- embed node label in interactive network graph so label drags with node point
- Node tags
    - add node tags
    - for network graph plot, have option to only show nodes with 
      certain user specified tags
- modify __dir__ to not show internal methods
- RSVP auto-bandwidth LSP
- Specific Model calls to
    - Remove a Node
    - Remove an Interface/Circuit
    - Remove a demand
    - Change demand magnitude
    *** These can all be done now, but require a few API calls to do s


Completed enhancements since last release
- make interactive network plot - done
- for network graph, have option to only show circuits with interfaces above a 
  certain % utilization (important for scaled networks) - done
- new client code that uses the load_model call - done

