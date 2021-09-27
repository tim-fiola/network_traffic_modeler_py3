The Network Model File
======================

The network model file contains basic information about the network topology:

* Interfaces
* Nodes (layer 3 node/router)
* Demands (traffic)
* RSVP LSPs

Interfaces
**********

Interfaces represent the logical interfaces on a layer 3 Node (Router).
In the context of a simulation, demands (traffic) egress interfaces.
A circuit is created when two *matching* interfaces (one in each direction) are paired to form a bi-directional connection between layer 3 nodes.

The process of *matching* circuits depends on the model object used.

The ``PerformanceModel`` automatically matches the interfaces into circuits.

The ``FlexModel`` requires a ``circuit_id`` to appropriately match two interfaces into a circuit. The ``circuit_id`` must be included for each interface in the model file's ``INTERFACES_TABLE``.
There must be exactly two instances of a given ``circuit_id`` in the ``INTERFACES_TABLE``: any more or any less will result in extra/unmatched interfaces and will cause an error when the file is loaded.

Nodes
*****

Nodes represent layer 3 devices in the topology. Many nodes can be inferred by the presence of an interface on the ``node_object`` column in the ``INTERFACES_TABLE`` in the model file.
Any node inferred by the ``node_object`` column in the ``INTERFACES`` table does not have to be explicitly declared in the ``NODES`` table.
However, the ``NODES`` table does have a couple of use cases:

* It can be used to add attributes to inferred nodes: ``lat`` (latitude, or y-coordinate), ``lon`` (longitude, or x-coordinate), and ``igp_shortcuts_enabled`` (whether IGP shortcuts are enabled for the node)
* It can be used to declare a node that does not have any interfaces yet (aka an *orphan* node)

.. note::
   ``lat`` and ``lon`` can be used instead for (y, x) grid coordinates; there are no restrictions on the integer values those attributes can have.

Demands
*******

Demands represent traffic on the network. Each demand represents an amount of traffic ingressing the network at a specific layer 3 (source) node and egressing the network at a specific layer 3 (destination) node.

In the ``DEMANDS_TABLE`` table section, there are four headers:

* ``source`` - the source node for the traffic; the node in the model where the traffic originates
* ``dest`` - the destination node for the traffic; the node in the model where the traffic terminates
* ``traffic`` - the amount of traffic in the demand
* ``name`` - the name of the demand; there can be multiple demands with matching source and dest nodes - the name is the differentiator

  * there cannot be multiple demands with matching ``source``, ``dest``, and ``name`` values

RSVP LSPs
*********

These are in the ``RSVP_LSP_TABLE``.  This table has three columns:

* ``source`` - the source node for the LSP; the node in the model where the LSP originates
* ``dest`` - the destination node for the LSP; the node in the model where the LSP terminates
* ``name`` - the name of the LSP; there can be multiple LSPs with matching source and dest nodes - the name is the differentiator

  * there cannot be multiple LSPs with matching ``source``, ``dest``, and ``name`` values

* ``configured_setup_bw`` -
* ``manual_metric`` -