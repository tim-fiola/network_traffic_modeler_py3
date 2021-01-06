
[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![Build Status](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3.svg?branch=master)](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3)
[![Coverage Status](https://coveralls.io/repos/github/tim-fiola/network_traffic_modeler_py3/badge.svg?branch=master)](https://coveralls.io/github/tim-fiola/network_traffic_modeler_py3?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pyntm/badge/?version=latest)](https://pyntm.readthedocs.io/en/latest/?badge=latest)


pyNTM: network_traffic_modeler_py3
==================================

This is a network traffic modeler written in python 3. The main use cases involve understanding how your layer 3 traffic will transit a given topology.  You can modify the topology (add/remove layer 3 Nodes, Circuits, Shared Risk Link Groups), fail elements in the topology, or add new traffic Demands to the topology. pyNTM is a simulation engine that will converge the modeled topology to give you insight as to how traffic will transit a given topology, either steady state or with failures.

This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  This package is in no way related to those, or any, commercial products.  IGP and RSVP routing is supported. 


pyNTM Model Classes
==================================
In pyNTM, the Model objects house the network topology objects: traffic Demands, layer 3 Nodes, Circuits, Shared Risk Link Groups (SRLGs), Interfaces, etc.  The Model classes control how all the contained objects interact with each other during Model convergence to produce simulation results.

There are two subclasses of Model objects: the PerformanceModel object and the newer FlexModel object (introduced in version 1.6).  
Starting in version 1.7, what used to be called the Model class is now the PerformanceModel Class.  The former Parallel_Link_Model
class is now known as the FlexModel class.  
There are two main differences between the two types of objects:
- The PerformanceModel object only allows a single Circuit between two layer 3 Nodes; while the FlexModel allows multiple Circuits between the same two Nodes.
- The Performance Model will have better performance (measured in time to converge) than the FlexModel.  This is because the FlexModel has additional checks to account for potential multiple Circuits between Nodes and other topology features such as IGP shortcuts.

The legacy Model and Parallel_Link_Model should still work as they have been made subclasses of the PerformanceModel and FlexModel classes, respectively.

The PerformanceModel class is good to use for the following topology criteria:
- There is only one link (Circuit) between each layer 3 Node
- IGP-only routing and/or RSVP LSP routing with no IGP shortcuts (traffic source and destination matches LSP source and destination)

Which Model Class To Use
==================================
All model classes support:
- IGP routing
- RSVP LSPs carrying traffic demands that have matching source and destination as the RSVP LSPs
- RSVP auto-bandwidth or fixed bandwidth
- RSVP LSP manual metrics

The PerformanceModel class allows for:
- Single Circuits between 2 Nodes
- Error messages if it detects use of IGP shortcuts or multiple Circuits between 2 Nodes

The FlexModel class allows for:
- Multiple Circuits between 2 Nodes
- RSVP LSP IGP shortcuts, whereby LSPs can carry traffic demands downstream, even if the demand does not have matching source and destination as the LSP

In some cases, it's completely valid to model multiple Circuits between Nodes as a single Circuit.  For example: in the case where there are multiple Circuits between Nodes but each Interface has the same metric and the use case is to model capacity between Nodes, it's often valid to combine the Circuit capacities and model as a single Circuit.  In this case, the PerformanceModel object is recommended as it will give better performance.

If it is important to keep each Circuit modeled separately because the parallel Interfaces have different metrics and/or differences in their capabilities to route RSVP, the FlexModel is the better choice.

If there is any doubt as to which class to use, use the FlexModel class.
 
Optimization
==================================
 
There are two main areas where we are looking to optimize:
- Performance - converging the model to produce a simulation, especially in a model with RSVP LSPs, is intensive.  Improving the time it takes to converge the simulation results in better productivity and improved user experience
  - pyNTM supports the pypy3 interpreter, which results in 60-90% better performance than the python3 interpreter

- Data retrieval - the simulation produces an extraordinary amount of data.  Currently, the model is only retaining a fraction of the data generated during the model convergence.  It's our goal to introduce something like an sqlite database in the model objects to hold all this information.  This will improve user experience and allow SQL queries against the model object.


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

If using the *WeatherMap* class, also install the `dash` and `dash-cytoscape` modules explicitly:
```
pip3 install pyNTM
pip3 install dash
pip3 install dash-cytoscape
```

Visualization
=============
Info about the new WeatherMap class that provides visualization is available in the wiki: https://github.com/tim-fiola/network_traffic_modeler_py3/wiki/Visualizing-the-network-with-the-WeatherMap-Class

Training
=========
See the training modules at https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-


Documentation
=============

See the documentation on [Read the Docs](http://pyntm.readthedocs.org).


Examples
========

See the [example directory](https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples).


License
=======

Copyright 2019 Tim Fiola

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
