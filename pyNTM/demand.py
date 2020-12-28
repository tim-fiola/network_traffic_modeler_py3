"""A Demand is a traffic load that traverses the network from a source Node
to a destination Node"""


class Demand(object):
    """
    A representation of traffic load on the modeled network
    """

    def __init__(self, source_node_object, dest_node_object, traffic=0, name='none'):
        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.traffic = traffic
        self.name = name
        self.path = 'Unrouted'
        self._path_detail = 'Unrouted_detail'

        # Validate traffic value
        if not(isinstance(traffic, (int, float))) or traffic < 0:
            raise ValueError('Must be a positive int or float')

    @property
    def _key(self):
        """Unique identifier for the demand: (Node('source').name, Node('dest').name, name)"""
        return (self.source_node_object.name, self.dest_node_object.name, self.name)

    def __repr__(self):
        return 'Demand(source = %s, dest = %s, traffic = %s, name = %r)' % \
               (self.source_node_object.name,
                self.dest_node_object.name,
                self.traffic,
                self.name)

    @property
    def path_detail(self):
        """
        Returns a detailed breakdown of the Demand path.
        Each path will have the following information:

        items: The combination of Interfaces and/or LSPs that the Demand takes
        from source to destination

        splits: each item on the path (Interface and/or LSP) and the number of cumulative
        ECMP path splits that the Demand has transited as it egresses that element.

        path_traffic: the amount of traffic on that specific path.  Path traffic will be the
        result of dividing the Demand's traffic by the highest quantity of cumulative path
        splits for an element in the path

        For example::
            Demand(source = A, dest = E, traffic = 24, name = 'dmd_a_e_1') has 24 units of traffic
            'path_0': {
            'items': [
                      Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'),
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

            path_traffic for path_0 = 24 units of traffic/6 splits  (Interface B-to-E_3 has 6 splits)
                                    = 4 units of traffic/path

            The traffic for the Demand has been split 6 times

        :return:

        """
        return self._path_detail
