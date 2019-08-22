"""A class to represent a layer 3 device in the Model"""

from .exceptions import ModelException


class Node(object):
    """
    A class to represent a layer 3 device in the model
    """

    def __init__(self, name, lat=0, lon=0):
        self.name = name
        self._failed = False
        self.lat = lat
        self.lon = lon
        self.srlgs = set()

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
    def failed(self, status):  # TODO - add check for SRLG
        if not isinstance(status, bool):
            raise ModelException('must be boolean')

        # If not failed (if True)
        if status is False:
            # Check for any SRLGs with self as a member and get status
            # of each SRLG
            failed_srlgs = [srlg for srlg in self.srlgs if srlg.failed == True]
            if len(failed_srlgs) > 0:
                self._failed = True

            self._failed = status


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

    # def srlgs(self, model):
    #     """
    #     Returns list of SRLGs in the Model that the Node is a member of.
    #     :param model: Model objevt
    #     :return: List of SRLGs that Node is a member of
    #     """
    #
    #     srlgs = [srlg for srlg in model.srlg_objects if self in srlg]
    #
    #     return srlgs

