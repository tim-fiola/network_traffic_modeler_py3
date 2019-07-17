"""A class to represent a router in the Model"""

from .exceptions import ModelException


class Node(object):
    """
    A class to represent a router in the model
    """

    def __init__(self, name, lat=0, lon=0):
        self.name = name
        self._failed = False
        self.lat = lat
        self.lon = lon

        # Validate lat, lon values
        if (lat > 90 or lat < -90):
            raise ValueError('lat must be in range -90 to +90')
        if (lon > 180 or lon < -180):
            raise ValueError('lon must be in range -180 to +180')

    def __repr__(self):
        return 'Node(%r)' % self.name

    # Modify __eq__ and __hash__ default behavior for Node class
    # to allow us to easily determine if a Node instance is equivalent to another.
    # By default, equivalency test is 1) id, 2) hash, 3) equality.  The id test will
    # fail and so it will move to hash and then equality.  Modifying the __eq__ to
    # focus on the Node.name equivalency and and __hash__ to focus on the
    # hash of the Node.name will make equivalency testing possible
    def __eq__(self, other_node):
        return self.__dict__ == other_node.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def _key(self):
        return self.name

    @property
    def failed(self):
        return self._failed

    @failed.setter
    def failed(self, status):
        if isinstance(status, bool):
            self._failed = status
        else:
            raise ModelException('must be boolean')

    def interfaces(self, model):
        """
        Returns interfaces for a given node

        :param model: model structure
        :return adjacency_list: (list) list of interfaces on the given node
        """
        adjacency_list = []

        interface_iterator = (interface for interface in model.interface_objects)

        for interface in interface_iterator:
            if interface.node_object.name == self.name:
                adjacency_list.append(interface)

        return adjacency_list

    def adjacent_nodes(self, model):
        """
        Returns a list of adjacent nodes
        """

        adjacencies = self.interfaces(model)

        adjacent_nodes = set()

        for adjacency in adjacencies:
            adjacent_nodes.add(adjacency.remote_node_object)

        return adjacent_nodes
