[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![CI](https://github.com/tim-fiola/network_traffic_modeler_py3/actions/workflows/ci.yml/badge.svg)](https://github.com/tim-fiola/network_traffic_modeler_py3/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tim-fiola/network_traffic_modeler_py3/graph/badge.svg?token=YOUR_TOKEN_HERE)](https://codecov.io/gh/tim-fiola/network_traffic_modeler_py3)
[![Documentation Status](https://readthedocs.org/projects/pyntm/badge/?version=latest)](https://pyntm.readthedocs.io/en/latest/?badge=latest)


**pyNTM 4.0.1** is here!  This update clears some technical debt such as migrating the testing from Travis to GitHub actions and updating some packages to clear some problems with outdated dependencies.  It also updates the python and pypy versions.

This release lays the groundwork for additional features to be added.

**HELP**: If you have experience optimizing code for performance and care to contribute, I'm happy to consider pull requests.  The current code base is logically sound and will give good results, but I know that it needs to be optimized for performance (code performance optimization is not my specialty).  In effect, this means that it takes longer for the model to converge, *especially* for models with large amounts of RSVP LSPs.  


pyNTM: network_traffic_modeler_py3
==================================

Written by the author of the Junos Networking Technology Series book "This Week: Deploying MPLS", pyNTM (Network Traffic Modeler) is designed to answer the following questions for service-provider OSPF/IS-IS and MPLS WAN networks such as:

* How will a failure on your wide area network (WAN) affect link utilizations? 
* What about a layer 3 node failure?
* Will all of your RSVP auto-bandwidth LSPs be able to resignal after a link/node failure?  
* Can you WAN handle a 10% increase in traffic during steady state?  What about failover state?

These questions are non-trivial to answer for a medium to large size WAN that is meshy/interconnected, and these are the exact scenarios that a WAN simulation engine is designed to answer.

This is a network traffic modeler written in python 3. The main use cases involve understanding how your layer 3 traffic will transit a given topology.  You can modify the topology (add/remove layer 3 Nodes, Circuits, Shared Risk Link Groups), fail elements in the topology, or add new traffic Demands to the topology. pyNTM is a simulation engine that will converge the modeled topology to give you insight as to how traffic will transit a given topology, either steady state or with failures.

This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  This package is in no way related to those, or any, commercial products.  IGP and RSVP routing is supported. 

pyNTM can be used as an open source solution to answer WAN planning questions; you can also run pyNTM alongside a commercial solution as a validation/check on the commercial solution.


Training
=========
See the training modules at https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-


Documentation
=============

See the documentation on [Read the Docs](http://pyntm.readthedocs.org).


Examples
========

See the [example directory](https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples).

Install
=======

Install via pip:
```bash
pip3 install pyNTM
```

For upgrade:
```bash
pip3 install --upgrade pyNTM
```


pyNTM Model Class
==================================
In pyNTM, the Model object houses the network topology objects: traffic Demands, layer 3 Nodes, Circuits, Shared Risk Link Groups (SRLGs), Interfaces, etc.  The Model class controls how all the contained objects interact with each other during Model convergence to produce simulation results.

The model class is ``Model``.  It supports all pyNTM features:
- IGP routing
- Multiple Circuits (parallel links) between layer 3 Nodes
- RSVP LSPs with bandwidth reservation, auto-bandwidth, and manual metrics
- RSVP LSP IGP shortcuts, whereby LSPs can carry traffic demands downstream
- SRLG (Shared Risk Link Group) support
- Interactive visualization

The legacy class names ``FlexModel``, ``PerformanceModel``, and ``Parallel_Link_Model`` are available as aliases for backward compatibility.

Model files from either the old PerformanceModel format (without circuit_id column) or FlexModel format (with circuit_id column) are automatically detected and loaded correctly.

Visualization
=============
pyNTM includes an interactive network visualization that runs in the browser.  After running a simulation, call ``visualize()`` on the model:

```python
from pyNTM import Model

model = Model.load_model_file('network.csv')
model.update_simulation()
model.visualize()                    # opens in default browser
model.visualize('output.html')       # saves to a specific file
```

The visualization features:
- **Draggable nodes** for rearranging the topology layout
- **Per-direction utilization coloring** on each interface with a toggleable legend to filter by utilization range
- **Demand path tracing** - select a demand to highlight its path, see traffic, LSPs it rides, and interfaces it transits
- **RSVP LSP path tracing** - select an LSP to see its traffic, reserved bandwidth, demands it carries, and interfaces
- **Interface inspection by node** - select a node to list its interfaces with utilization, demands, and LSPs on each
- **Cross-linked navigation** - click any demand, LSP, or interface in any panel to make it the active selection
- **Tooltips** on hover showing interface name, endpoints, capacity, and utilization

The legacy ``WeatherMap`` class (``pyNTM.weathermap``) using Dash/Cytoscape is deprecated in favor of the new ``model.visualize()`` method.


License
=======

Copyright 2019 Tim Fiola

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
