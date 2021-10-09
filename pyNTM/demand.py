"""A Demand is a traffic load that traverses the network from a source Node
to a destination Node"""


class Demand(object):
    """
    A representation of traffic load on the modeled network
    """

    def __init__(self, source_node_object, dest_node_object, traffic=0, name="none"):
        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.traffic = traffic
        self.name = name
        self.path = "Unrouted"
        self._path_detail = "Unrouted_detail"

        # Validate traffic value
        if not (isinstance(traffic, (int, float))) or traffic < 0:
            raise ValueError("Must be a positive int or float")

    @property
    def _key(self):
        """Unique identifier for the demand: (Node('source').name, Node('dest').name, name)"""
        return (self.source_node_object.name, self.dest_node_object.name, self.name)

    def __repr__(self):
        return "Demand(source = %s, dest = %s, traffic = %s, name = %r)" % (
            self.source_node_object.name,
            self.dest_node_object.name,
            self.traffic,
            self.name,
        )

    @property
    def path_detail(self):
        """
        Returns a detailed breakdown of the Demand path.
        Each path will have the following information:

        items: The combination of Interfaces and/or LSPs that the Demand takes
        from source to destination

        splits: each item on the path (Interface and/or LSP) and the number of cumulative
        ECMP path splits that the Demand has transited as it egresses the source node for
        that element.

        Splits can be used to calculate how much of the Demand's traffic is on a certain path
        (see path_traffic below) or how much of the Demand's traffic is on a certain element.

        The demand object's ``path_detail`` property can be very useful to determine how much of the demand's
        traffic egresses each object (interface, LSP) in the path.

        For example, sample demand ``Demand(source = A, dest = E, traffic = 24, name = 'dmd_a_e_1')``
        has 24 units of traffic.

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

        * ``Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1')`` carries **24 / 2 = 12** units of traffic from the sample demand.
        * ``Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'), remote_node_object = Node('E'), circuit_id = '27')`` carries **24 / 6 = 4** units of traffic from the sample demand.

        Since the minimum amount of traffic found on any object in ``path_0`` is 4 units of traffic, ``path_traffic`` for ``path_0`` = 4.

        :return: Dict of path entries (keys).  The value for each key is another dict with 3 keys: 'items', 'splits', and 'path_traffic'.  Each is described above.  # noqa E501
        """

        return self._path_detail
