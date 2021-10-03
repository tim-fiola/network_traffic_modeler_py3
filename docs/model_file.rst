The Network Model File
======================

The network model file contains basic information about the network topology:

* Interfaces
* Nodes (layer 3 node/router)
* Demands (traffic)
* RSVP LSPs

There are two network model subclasses: FlexModel and PerformanceModel. In general, the FlexModel can accommodate more
topology variations, but at the price of a slightly longer convergence time while the PerformanceModel can only handle
simpler network architectures, but with the benefit of better convergence time.

All model classes support:

* IGP routing
* RSVP LSPs carrying traffic demands that have matching source and destination as the RSVP LSPs
* RSVP auto-bandwidth or fixed bandwidth
* RSVP LSP manual metrics

The PerformanceModel class allows for:

* Single Circuits between 2 Nodes
* Error messages if it detects use of IGP shortcuts or multiple Circuits between 2 Nodes

The FlexModel class allows for:

* Multiple Circuits between 2 Nodes
* RSVP LSP IGP shortcuts, whereby LSPs can carry traffic demands downstream, even if the demand does not have matching source and destination as the LSP

The model file categories for each model subclass are explained below.

Interfaces
----------

Interfaces represent the logical interfaces on a layer 3 Node (Router).
In the context of a simulation, demands (traffic) egress interfaces.
A circuit is created when two *matching* interfaces (one in each direction) are paired to form a bi-directional connection between layer 3 nodes.

The process of *matching* circuits depends on the model object used.

Since there can only be a single connection (circuit) between any two nodes, the ``PerformanceModel`` automatically matches the interfaces into circuits.

The ``FlexModel`` requires a ``circuit_id`` to appropriately match two interfaces into a circuit. The ``circuit_id`` must be included for each interface in the model file's ``INTERFACES_TABLE``.
There must be exactly two instances of a given ``circuit_id`` in the ``INTERFACES_TABLE``: any more or any less will result in extra/unmatched interfaces and will cause an error when the file is loaded.


PerformanceModel
****************

INTERFACES_TABLE

* node_object_name - name of node	where interface resides
* remote_node_object_name	- name of remote node
* name - interface name
* cost - IGP cost/metric for interface
* capacity - capacity
* rsvp_enabled (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
* percent_reservable_bandwidth (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this
value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100


FlexModel
*********

INTERFACES_TABLE

* node_object_name - name of node	where interface resides
* remote_node_object_name	- name of remote node
* name - interface name
* cost - IGP cost/metric for interface
* capacity - capacity
* circuit_id - id of the circuit; used to match two Interfaces into Circuits

  * each circuit_id can only appear twice in the model
  * circuit_id can be string or integer

* rsvp_enabled (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
* percent_reservable_bandwidth (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this
value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100
* manual_metric (optional) - manually assigned metric for LSP, if not using default metric from topology
shortest path


Nodes
-----

Nodes represent layer 3 devices in the topology. Many nodes can be inferred by the presence of an interface on the ``node_object`` column in the ``INTERFACES_TABLE`` in the model file.
Any node inferred by the ``node_object`` column in the ``INTERFACES`` table does not have to be explicitly declared in the ``NODES`` table.
However, the ``NODES`` table does have a couple of use cases:

* It can be used to add attributes to inferred nodes: ``lat`` (latitude, or y-coordinate), ``lon`` (longitude, or x-coordinate), and ``igp_shortcuts_enabled`` (whether IGP shortcuts are enabled for the node)
* It can be used to declare a node that does not have any interfaces yet (aka an *orphan* node)

.. note::
   ``lat`` and ``lon`` can be used instead for (y, x) grid coordinates; there are no restrictions on the integer values those attributes can have.

PerformanceModel
****************

NODES_TABLE

* name - name of node
* lon	- longitude (or y-coordinate) (optional)
* lat - latitude (or x-coordinate) (optional)


FlexModel
*********

NODES_TABLE

* name - name of node
* lon - longitude (or y-coordinate)
* lat - latitude (or x-coordinate)
* igp_shortcuts_enabled(default=False) - Indicates if IGP shortcuts enabled for the Node
  * If ``True``, network internal traffic transiting the layer 3 node can now use LSPs en route to the destination, if they are available


Demands
-------

Demands represent traffic on the network. Each demand represents an amount of traffic ingressing the network at a specific layer 3 (source) node and egressing the network at a specific layer 3 (destination) node.



PerformanceModel and FlexModel
******************************

For both model classes, the ``DEMANDS_TABLE`` table has four headers, all of which are required:

* ``source`` - the source node for the traffic; the node in the model where the traffic originates
* ``dest`` - the destination node for the traffic; the node in the model where the traffic terminates
* ``traffic`` - the amount of traffic in the demand
* ``name`` - the name of the demand; there can be multiple demands with matching source and dest nodes - the name is the differentiator

  * there cannot be multiple demands with matching ``source``, ``dest``, and ``name`` values

RSVP LSPs
---------


PerformanceModel and FlexModel
******************************

These are in the ``RSVP_LSP_TABLE``.

* ``source`` - the source node for the LSP; the node in the model where the LSP originates
* ``dest`` - the destination node for the LSP; the node in the model where the LSP terminates
* ``name`` - the name of the LSP; there can be multiple LSPs with matching source and dest nodes - the name is the differentiator

  * there cannot be multiple LSPs with matching ``source``, ``dest``, and ``name`` values

* ``configured_setup_bw`` - if LSP has a fixed, static configured setup bandwidth, place that static value here,
if LSP is auto-bandwidth, then leave this blank for the LSP
* ``manual_metric`` - manually assigned metric for LSP, if not using default metric from topology
shortest path
