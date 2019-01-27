# network_traffic_modeler_py3
This is the network traffic modeler written in python 3.  Version 1.5.  All further updates to network_traffic_modeler will be in python3 and in this repository.

The big add in this commit is interactive network visualization allowing user to 
  - view network
  - move nodes
  - get tooltips via hovering over links
  - filter to visualizing only links in certain utilization ranges
  
Also check out the BUILD.MD file (authored by nelsg) for directions on how to run this modeler in a virtual environment and auto-download all dependencies.

--------------
The UI (simple_user_interface.py) is specifically designed to address common modeling use cases:
- provide quick linkage between related objects: Nodes, interfaces, and demands (traffic)
- allow the user to explore the shortest paths and all feasible (loop free) paths between selected nodes
- examine traffic on interfaces above a specified utilization percentage

--------------
Full API set use cases include:
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

--------------
Capabilities TO DO:
- Add RSVP auto-bandwidth capabilities (in progress)
- Enable UI to fail nodes/interfaces

--------------
Use Cases TO DO:
- Specific Model calls to
    - Remove a Node
    - Remove an Interface/Circuit
    - Remove a demand
    - Change demand magnitude
    *** These can all be done now, but require a few API calls to do so

--------------
User experience TO DO:
- modify __dir__ to not show internal methods
- modify Node.lat and Node.lon (latitute, longitude) to have guardrails for 
staying within lat/lon boundaries.  Right now they just serve as holders of 
coordinate data

--------------
Needed optimizations:
- optimize path finding for non-LSP demands by making a single networkx model for a group of demands versus making the networkx model for each demand
- add guardrails to Demand and Interface attributes (traffic must be a float), etc
