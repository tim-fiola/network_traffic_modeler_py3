.. pyNTM documentation master file, created by
   sphinx-quickstart on Wed May 22 18:43:55 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyNTM's documentation!
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do (but those solve for much more as well).

Changes to the topology can be done to simulate new routers, circuits, circuit capacity, network failures, etc. Changes to the traffic matrix can be done to simulate increases/decreases in existing traffic or additional traffic matrix entries.

Examine and run the client code to get an understanding of how this code works.

Currently this modeling code supports simple OSPF/ISIS routing. There is no layer 1 SRLG support at the moment.
RSVP auto-bandwidth is also supported in this release in beta form: the RSVP code works properly but it does not scale well.

IGP routing should perform well at scale as it leverages path calculations from the networkx module. There are no implied or explicit warranties associated with this app.


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

Note: interface addresses are only used to match interfaces into circuits and do not have any practical bearing on the simulation results

Contents
==========

.. toctree::
   :maxdepth: 2

   install
   examples
   api
   changelog


Indices and tables
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
