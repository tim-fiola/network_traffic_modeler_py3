The Network Model File
======================

The network model file contains basic information about the network topology:

* Interfaces
* Nodes (layer 3 node/router)
* Demands (traffic)
* RSVP LSPs

Since there is a lot of information needed to create a model, using the model file to load network data is recommended.

The network model file is a **tab-separated** values file.

The sections below describe the model file's table headers.

Model File Interface Headers
----------------------------

Interfaces represent the logical interfaces on a layer 3 Node (Router).
In the context of a simulation, demands (traffic) egress interfaces.
A circuit is created when two *matching* interfaces (one in each direction) are paired to form a bi-directional connection between layer 3 nodes.

The model supports two interface table formats, which are auto-detected based on the header line:

* **Without circuit_id** - interfaces between the same two nodes are automatically paired into circuits
* **With circuit_id** - a ``circuit_id`` column is used to explicitly match interfaces into circuits, which is required when there are multiple parallel circuits between the same nodes

INTERFACES_TABLE (without circuit_id)
*************************************

* ``node_object_name`` - name of node where interface resides
* ``remote_node_object_name`` - name of remote node
* ``name`` - interface name
* ``cost`` - IGP cost/metric for interface
* ``capacity`` - capacity
* ``rsvp_enabled`` (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
* ``percent_reservable_bandwidth`` (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100

INTERFACES_TABLE (with circuit_id)
**********************************

* ``node_object_name`` - name of node where interface resides
* ``remote_node_object_name`` - name of remote node
* ``name`` - interface name
* ``cost`` - IGP cost/metric for interface
* ``capacity`` - capacity
* ``circuit_id`` - id of the circuit; used to match two Interfaces into Circuits

  * each ``circuit_id`` value can only appear twice in the model
  * ``circuit_id`` can be string or integer

* ``rsvp_enabled`` (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
* ``percent_reservable_bandwidth`` (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100

.. important::
   Column order matters. If you wish to use an optional column to the right of an optional column you don't want to specify a value for, you must still include the optional headers to the left of the column you wish to specify a value for.

   For example, if you wish to specify a ``percent_reservable_bandwidth`` for an interface but not explicitly specify ``rsvp_enabled``, you must also include the ``rsvp_enabled`` columns and then leave those row values blank in each unused column.

   This example specifies ``percent_reservable_bandwidth`` of 30 for interface ``A-to-B_1``::

    INTERFACES_TABLE
    node_object_name	remote_node_object_name	name	cost	capacity    circuit_id  rsvp_enabled    percent_reservable_bandwidth
    A	B	A-to-B_1    20	120 1       30
    B	A	B-to-A_1    20	120 1   True  50

Model File Node Headers
-----------------------

Nodes represent layer 3 devices in the topology. Many nodes can be inferred by the presence of an interface on the ``node_object`` column in the ``INTERFACES_TABLE`` in the model file.
Any node inferred by the ``node_object`` column in the ``INTERFACES`` table does not have to be explicitly declared in the ``NODES`` table.
However, the ``NODES`` table does have a couple of use cases:

* It can be used to add attributes to inferred nodes: ``lat`` (latitude, or y-coordinate), ``lon`` (longitude, or x-coordinate), and ``igp_shortcuts_enabled`` (whether IGP shortcuts are enabled for the node)
* It can be used to declare a node that does not have any interfaces yet (aka an *orphan* node)

.. note::
   ``lat`` and ``lon`` can be used instead for (y, x) grid coordinates; there are no restrictions on the integer values those attributes can have.

NODES_TABLE
***********

* ``name`` - name of node
* ``lon`` - longitude (or y-coordinate) (optional)
* ``lat`` - latitude (or x-coordinate) (optional)
* ``igp_shortcuts_enabled`` (default=``False``) - Indicates if IGP shortcuts enabled for the Node (optional)

  * If ``True``, network internal traffic transiting the layer 3 node can now use LSPs en route to the destination, if they are available

.. important::
   Column order matters.  If you wish to use an optional column to the right of an optional column you don't want to specify a value for, you must still include the optional headers to the left of the column you wish to specify a value for.

   If you wish to include ``igp_shortcuts_enabled`` values for a given node, you must include the ``name``, ``lon`` and ``lat`` column headers and then leave the unused row values for those columns blank.

   For example, to enable ``igp_shortcuts_enabled`` for the ``SLC`` node, but not specify ``lon`` or ``lat``::

      NODES_TABLE
      name lon lat igp_shortcuts_enabled
      SLC           True

Model File Demand Headers
-------------------------

Demands represent traffic on the network. Each demand represents an amount of traffic ingressing the network at a specific layer 3 (source) node and egressing the network at a specific layer 3 (destination) node.

DEMANDS_TABLE
*************

The ``DEMANDS_TABLE`` table has four headers, all of which are required:

* ``source`` - the source node for the traffic; the node in the model where the traffic originates
* ``dest`` - the destination node for the traffic; the node in the model where the traffic terminates
* ``traffic`` - the amount of traffic in the demand
* ``name`` - the name of the demand; there can be multiple demands with matching source and dest nodes - the name is the differentiator

  * there cannot be multiple demands with matching ``source``, ``dest``, and ``name`` values

RSVP LSPs
---------

RSVP_LSP_TABLE
**************

The ``RSVP_LSP_TABLE`` has the following columns:

* ``source`` - the source node for the LSP; the node in the model where the LSP originates
* ``dest`` - the destination node for the LSP; the node in the model where the LSP terminates
* ``name`` - the name of the LSP; there can be multiple LSPs with matching source and dest nodes - the name is the differentiator

  * There cannot be multiple LSPs with matching ``source``, ``dest``, and ``name`` values

* ``configured_setup_bw`` (optional) - if LSP has a fixed, static configured setup bandwidth, place that static value here, if LSP is auto-bandwidth, then leave this blank for the LSP
* ``manual_metric`` (optional) - manually assigned metric for LSP, if not using default metric from topology shortest path

.. important::
   Column order matters.  If you wish to use an optional column to the right of an optional column you don't want to specify a value for, you must still include the optional headers to the left of the column you wish to specify a value for.

   If you wish to specify a ``manual_metric`` for an LSP but not explicitly specify ``configured_setup_bw``, you must also include the ``configured_setup_bw`` column and then leave those row values blank in each unused column.

   For example, to specify a ``manual_metric`` for the LSP with name ``lsp_a_b_2`` but not specify ``configured_setup_bw``::

    RSVP_LSP_TABLE
    source	dest	name    configured_setup_bw manual_metric
    A	B	lsp_a_b_1   10  19
    A	B	lsp_a_b_2       6