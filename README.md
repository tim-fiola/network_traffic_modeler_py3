
[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![Build Status](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3.svg?branch=master)](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3)
[![Coverage Status](https://coveralls.io/repos/github/tim-fiola/network_traffic_modeler_py3/badge.svg?branch=master)](https://coveralls.io/github/tim-fiola/network_traffic_modeler_py3?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pyntm/badge/?version=latest)](https://pyntm.readthedocs.io/en/latest/?badge=latest)


pyNTM: network_traffic_modeler_py3
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  This package is in no way related to those, or any, commercial products.  

IGP and RSVP auto-bandwidth routing is supported. 

The modeling class is where pyNTM builds the network topology: Nodes, Interfaces, Circuits, Demands (traffic) all interact in the modeling class.  It is these interactions that produce a simulation.

There are 2 types of pyNTM modeling classes: 
- the traditional Model class
- the new Parallel_Link_Model class

The primary difference between the 2 class types is the capability for Parallel_Link_Model class to support multiple links (Circuits) between layer 3 Nodes.  
The Model class, on the other hand, only supports a single link (Circuit) between layer 3 Nodes.  The Model class, however, will produce better performance than the Parallel_Link_Model because the Parallel_Link_Model has additional overhead to check for multiple links between the layer 3 Nodes.

For some use cases, it may be valid to simulate multiple links between Nodes as a single link.  For example, if there are 2 links between layer 3 Nodes and each link has the same metric on each component Interface.  In that case, it can be completely valid to simulate both Circuits as a single Circuit with capacity = capacity of Circuit1 + capacity of Circuit2.  
For example, Circuit1 between Nodes A and B is comprised of Interface1 and Interface2.  Circuit2 between the same Nodes (A and B) is comprised of Interfac3 and Interface4.

If Interface1 and Interface3 have the same metric and same capability to route RSVP LSPs and Interface2 and Interface4 have the same metric and capability to route RSVP LSPs, it may be valid to simulate Circuit1 and Circuit2 as a single AggCircuit.

A-Interface1---Circuit1---Interface2-B

A-Interface3---Circuit2---Interface4-B

A---AggCircuit---B


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
