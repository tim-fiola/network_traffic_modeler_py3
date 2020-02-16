From the readme:
=====

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


From init file:
====

======== TO DO ===========
simple_user_interface.py TO DO:
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

API TO DO:
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
- increasing/decreasing the magnitude of an existing demand in the traffic matrix failover       

NOTES:
- interface circuit_ids are only used to match interfaces into circuits and do
not have any practical bearing on the simulation results


Use Cases TO DO:
- Save an existing model to a file
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


User experience TO DO:
- new client code that uses the load_model and save_model calls
- make simple UI
- for network graph, have option to only show circuits with interfaces above a 
  certain % utilization (important for scaled networks)
- add node tags
- for network graph plot, have option to only show nodes with certain user specified tags
- modify __dir__ to not show internal methods