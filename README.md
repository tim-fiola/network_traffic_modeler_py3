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

User experience TO DO:
- modify __dir__ to not show internal methods
- modify Node.lat and Node.lon (latitute, longitude) to have guardrails for 
staying within lat/lon boundaries.  Right now they just serve as holders of 
coordinate data

Needed optimizations:
- add guardrails to Demand and Interface attributes (traffic must be a float), etc
