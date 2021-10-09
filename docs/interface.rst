Interfaces
==========

Interfaces represent uni-directional interfaces on a layer 3 node.

A **circuit** is created when two *matching* interfaces (one in each direction) are paired to form a bi-directional connection between layer 3 nodes.

Interfaces are matched into a circuit if:

* They are on different nodes
* They have the same ``capacity``
* They have a matching ``circuit_id``

.. important::
   In the ``PerformanceModel`` subclass, the ``circuit_id`` is hidden because this subclass only allows a single circuit (edge) between any two nodes, so matching interfaces into circuits is deterministic.

Interface ``utilization`` represents how much traffic is egressing the interface divided by the interface's ``capacity`` (``utilization`` =  ``traffic`` / ``capacity``).

Interface Capacity Units
************************

An interface's ``capacity`` and ``traffic`` are described in *units* of traffic, meaning they are not described in Mbps, Gbps, etc.
They are written in this generic way so that the user can determine the traffic units they want to deal with in their modeling exercises.

For example, if an interface has ``capacity`` = 200, it can be 200 Mpbs, 200 Gbps, etc. This example, will use Gbps.

If a single, entire demand (# ECMP = 1) with ``traffic`` = 100 (Gbps) transits the interface, the interface's computed ``utilization`` will be 50% and its ``traffic`` will be 100 (Gbps).

For more information on interfaces,see the `interface docstrings`_.

.. _interface docstrings: ./api.html#interface