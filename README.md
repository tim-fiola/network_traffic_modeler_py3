
[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![Build Status](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3.svg?branch=master)](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3)
[![Coverage Status](https://coveralls.io/repos/github/tim-fiola/network_traffic_modeler_py3/badge.svg?branch=master)](https://coveralls.io/github/tim-fiola/network_traffic_modeler_py3?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pyntm/badge/?version=latest)](https://pyntm.readthedocs.io/en/latest/?badge=latest)


pyNTM: network_traffic_modeler_py3
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  This package is in no way related to those, or any, commercial products.  IGP and RSVP auto-bandwidth routing is supported. 

In pyNTM, the Model objects house the network topology objects: layer 3 Nodes, Circuits, Shared Risk Link Groups (SRLGs), Interfaces, etc.

There are two types of Model objects: the traditional Model object and the newer Parallel_Link_Model object (introduced in version 1.6).  There are two main differences between the two types of objects:
- The traditional Model object only allows a single Circuit between two layer 3 Nodes; while the Parallel_Link_Model allows multiple Circuits between the same two Nodes.
- The traditional Model will have better performance (measured in time to converge) than the Parallel_Link_Model.  This is because the Parallel_Link_Model has additional checks to account for potential multiple Circuits between Nodes.

In some cases, it's completely valid to model multiple Circuits between Nodes as a single Circuit.  For example: in the case where there are multiple Circuits between Nodes but each Interface has the same metric and the use case is to model capacity between Nodes, it's often valid to combine the Circuit capacities and model as a single Circuit.  In this case, the Model object is recommended as it will give better performance.
If it is important to keep each Circuit modeled separately because the parallel Interfaces have different metrics and/or differences in their capabilities to route RSVP, the Parallel_Link_Model is the better choice.
 

There are two main areas where we are looking to optimize:
- Performance - converging the model to produce a simulation, especially in a model with RSVP LSPs, is intensive.  Improving the time it takes to converge the simulation results in better productivity and improved user experience.  Possible Cython implementation or PyPy interpreter could add value here.
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

Training
=========
See the training modules on this repo's wiki page at https://github.com/tim-fiola/network_traffic_modeler_py3.git


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
