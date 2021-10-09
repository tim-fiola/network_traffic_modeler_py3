Common Workflows
================

There is an existing pyNTM training repository on GitHub that extensively covers common workflows with pyNTM.

`pyNTM Training Modules repository module 1`_ covers what network modeling is, the problem it solves for, and the common use cases

.. _pyNTM Training Modules repository module 1: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_training_module_1.pdf

Please see the `pyNTM Training Modules repository module 2`_ for info and walk-through exercises for

* Directions on how to get started using pyNTM
* Setting up a practice/demo environment
* Finding Shortest Path(s)
* Failing/Unfailing Interfaces
* Finding traffic demands egressing a given interface
* Finding all ECMP paths for a specific demand
* Simple visualization exercise

.. _pyNTM Training Modules repository module 2: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_training_module_2_v2.pdf

Please see the `pyNTM Training Modules repository module 3`_ for info and walk-through exercises for

* Adding a new Node
* Adding a new link
* Adding traffic to the traffic matrix
* Changing Interface/Circuit capacity
* Changing an Interface metric
* Working with RSVP LSPs

.. _pyNTM Training Modules repository module 3: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_training_module_3.pdf

Please see the `pyNTM Training Modules repository module 4`_ for info and walk-through exercises for

* RSVP LSP model data files
* RSVP types and behaviors
* Auto bandwidth
* Fixed bandwidth
* LSPs and Demands
* Getting an LSP path
* Seeing demands on an LSP
* Demand path when demand is on LSP
* Shared Risk Link Groups (SRLGs)
* Adding an SRLG
* Failing an SRLG

.. _pyNTM Training Modules repository module 4: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_training_module_4.pdf

Please see the `pyNTM Training Modules repository module 5`_ for info and walk-through exercises for

* How to create a visualization using the WeatherMap
* WeatherMap visual components overview

.. _pyNTM Training Modules repository module 5: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_visualization_training.pdf

Checking Network Health
***********************

There are a some results to watch for in your simulations that will indicate a network augment or re-architecture of your existing or planned network may be helpful.

IGP routing is deterministic and much simpler to interpret; one obvious warning sign is over-utilized links.

It gets a bit more difficult with RSVP, especially with auto-bandwidth enabled, to determine if the network is under stress.
RSVP auto-bandwidth behavior can be non-deterministic, meaning that there may be multiple different end-states the network will converge to, depending on the order in which the LSPs signal and how long each layer 3 node takes to compute the paths for its LSPs and a host of other factors.

With this being the case, there are a few behavior in the model to watch for when running RSVP that may indicate a network augment or re-architecture may be helpful:

* Large quantities of LSPs not on the shortest path
* LSPs reserving less bandwidth than they are carrying
* Some LSPs not being able to signal due to lack of available setup bandwidth in the path
