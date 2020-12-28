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
        return self._path_detail
