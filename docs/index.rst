.. pyNTM documentation master file, created by
   sphinx-quickstart on Wed May 22 18:43:55 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyNTM's documentation!
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.

Typical Use Cases
-----------------

* How will a failure on your wide area network (WAN) affect link utilizations?
* What about a layer 3 node failure?
* Will all of your RSVP auto-bandwidth LSPs be able to resignal after a link/node failure?
* Can you WAN handle a 10% increase in traffic during steady state?  What about failover state?

These questions are non-trivial to answer for a medium to large size WAN that is meshy/interconnected, and these are the exact scenarios that a WAN simulation engine is designed to answer.

Changes to the topology can be done to simulate new routers, circuits, circuit capacity, network failures, etc. Changes to the traffic matrix can be done to simulate increases/decreases in existing traffic or additional traffic matrix entries.

This is the network traffic modeler written in python 3. The main use cases involve understanding how your layer 3 traffic will transit a given topology.  You can modify the topology (add/remove layer 3 Nodes, Circuits, Shared Risk Link Groups), fail elements in the topology, or add new traffic Demands to the topology. pyNTM is a simulation engine that will converge the modeled topology to give you insight as to how traffic will transit a given topology, either steady state or with failures.

This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  This package is in no way related to those, or any, commercial products.  IGP and RSVP routing is supported.

pyNTM can be used as an open source solution to answer WAN planning questions; you can also run pyNTM alongside a commercial solution as a validation/check on the commercial solution.


Training
--------
See the training modules at https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-

Example Scripts
---------------

See the [example directory](https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples).

Examine and run the `client code examples`_, these docs, and check out the `pyNTM training repository`_ to get an understanding of how to use this code and the use cases.

.. _pyNTM training repository: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-

.. _client code examples: https://github.com/tim-fiola/network_traffic_modeler_py3/tree/master/examples

For a network with hundreds of nodes and thousands of LSPs, it may take several minutes for the model to converge when ``update_simulation`` is called.

There are no implied or explicit warranties associated with this app.

Full API set use cases include
-------------------------------

* simulating how traffic will transit your layer 3 network, given a traffic matrix
* simulating how your traffic will failover if any link(s) or node(s) fail
* simulating how a given network augment will affect link utilization and traffic flow, possible augments include

  - adding a new link
  - adding a new node with links
  - changing a link's capacity
  - adding a new traffic matrix entry (demand) to the traffic matrix
  - increasing/decreasing the magnitude of an existing demand in the traffic matrix failover

Note: interface circuit_ids are only used to match interfaces into circuits and do not have any practical bearing on the simulation results

Contents
==========

.. toctree::
   :maxdepth: 2

   install
   examples
   model
   model_file
   rsvp_lsp
   demand
   interface
   srlg
   workflows
   visualization
   development
   api
   changelog

Indices and tables
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

