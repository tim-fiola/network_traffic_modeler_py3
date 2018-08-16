# network_traffic_modeler_py3
This is the network traffic modeler written in python 3.  Version 1.2.  All further updates to network_traffic_modeler will be in python3 and in this repository.

Recent improvement: I modified the code to fully leverage networkx for path computation, which makes this code perform very well at scale.  I am testing scale on a model with over 1430 interfaces and 374 nodes.

Other changes: Some code refactoring was necessary to increase consistency and improve user experience.

DESCRIPTION:
A set of native python APIs to create a network model, visualize the model, and run
network simulations.       

This code allows users to define a layer 3 network topology, define a traffic
matrix, and then run a simulation to determine how the traffic will traverse
the topology.  If you've used Cariden MATE or WANDL, this code solves for
some of the same basic use cases those do (but those solve for much
more as well).

Changes to the topology can be done to simulate new routers, circuits,
circuit capacity, network failures, etc.
Changes to the traffic matrix can be done to simulate increases/decreases
in existing traffic or additional traffic matrix entries.

Examine and run the client code to get an understanding of how this code works.

Currently this modeling code supports simple OSPF/ISIS routing and only layer 3.  
There is no RSVP or layer 1 SRLG support at the moment.

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
    - increasing/decreasing the magnitude of an existing demand in the traffic matrix failover       

NOTES:
- interface addresses are only used to match interfaces into circuits and do
not have any practical bearing on the simulation results


Use Cases TO DO:
- Specific Model calls to
    - Remove a Node
    - Remove an Interface/Circuit
    - Remove a demand
    - Change demand magnitude
    *** These can all be done now, but require a few API calls to do so

User experience TO DO:
- modify __dir__ to not show internal methods

Needed optimizations:
- add guardrails to Demand and Interface attributes (traffic must be a float), etc
