Demands
=======

A representation of traffic load on the modeled network.

A demand object must have a source node, a destination node, and a name.

Demand Units
************

A demand's ``traffic`` property shows how many traffic *units* the demand carries. The ``traffic`` property is unit-less, meaning it is not described in Mbps, Gbps, etc.
It is written in this generic way so that the user can determine the traffic units they want to deal with in their modeling exercises.

For example, if a demand has ``traffic`` = 100, it can be 100Mpbs, 100Gbps, etc. This example, will use Gbps.

If the entire demand transits a single interface (# ECMP = 1) with a ``capacity`` of 200 Gbps  (and no other demands transit the interface), the interface's computed ``utilization`` will be 50%.

A demand's path is


The ``path_detail`` Property
****************************

The demand object's ``path_detail`` property can be very useful to determine how much of the demand's
traffic egresses each object (interface, LSP) in the path::

    Returns a detailed breakdown of the Demand path.
    Each path will have the following information:

    items: The combination of Interfaces and/or LSPs that the Demand transits
    from source to destination

    splits: each item on the path (Interface and/or LSP) and the number of cumulative
    ECMP path splits that the Demand has transited as it egresses the source node for
    that element.

    path_traffic: the amount of traffic on that specific path for the demand.  Path traffic will be the
    result of dividing the Demand's traffic by the **max** amount of path splits for an
    element in the path


For example, sample demand ``Demand(source = A, dest = E, traffic = 24, name = 'dmd_a_e_1')`` has 24 units of traffic.

Here is the ``path_0`` entry for the sample demand::

        'path_0': {
            'items': [Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'),
                        remote_node_object = Node('B'), circuit_id = '1'),
                    Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'),
                        remote_node_object = Node('E'), circuit_id = '27')
            ],
            'path_traffic': 4.0,
            'splits': {Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'),
                        remote_node_object = Node('B'), circuit_id = '1'): 2,
                      Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'),
                        remote_node_object = Node('E'), circuit_id = '27'): 6}
        }


The ``path_0`` component of the ``path_detail`` property in this example shows the following:

* ``Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1')`` has **2** splits
* ``Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'), remote_node_object = Node('E'), circuit_id = '27')`` has **6** splits

To get the amount of traffic load from the specific demand that transits each interface, divide the amount of traffic that the demand has by the number of splits for the object:

* ``Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1')`` carries **24 / 2 = 12** units of traffic from ``Demand(source = A, dest = E, traffic = 24, name = 'dmd_a_e_1')``
* ``Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'), remote_node_object = Node('E'), circuit_id = '27')`` carries **24 / 6 = 4** units of traffic from ``Demand(source = A, dest = E, traffic = 24, name = 'dmd_a_e_1')``

Since the minimum amount of traffic found on any object in ``path_0`` is 4 units of traffic, ``path_traffic`` for ``path_0`` = 4.

For more information on demands,see the `demand docstrings`_.

.. _demand docstrings: ./api.html#demand

Please see the `pyNTM Training Modules repository module 2`_ for info and walk-through exercises for demands, including:

* Finding traffic demands egressing a given interface
* Finding all ECMP paths for a specific demand

.. _pyNTM Training Modules repository module 2: https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_training_module_2_v2.pdf


