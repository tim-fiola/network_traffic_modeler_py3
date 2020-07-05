"""A class to represent a layer 3 device in the Model"""

from .exceptions import ModelException
from .srlg import SRLG


class Node(object):
    """
    A class to represent a layer 3 device in the model.

    Attribute lat, lon can be used as y, x values, respectively for
    graphing purposes.

    """

    def __init__(self, name, lat=0, lon=0):
        self.name = name
        self._failed = False
        self._lat = lat
        self._lon = lon
        self._srlgs = set()
        self._igp_shortcuts_enabled = False

        # Validate lat, lon values
        if not(isinstance(lat, float)) and not(isinstance(lat, int)):
            raise ValueError('lat must be a float value')
        if not(isinstance(lon, float)) and not(isinstance(lon, int)):
            raise ValueError('lon must be a float value')

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
        # return hash(tuple(sorted(self.__dict__.items())))
        return hash(self.name)

    def _key(self):
        return self.name

    @property
    def failed(self):
        """
        Is node failed?  Boolean.  It is NOT recommended to directly
        modify this property.  Rather, use Node.fail or Node.unfail.

        :return: Boolean - is node failed?
        """
        return self._failed

    @failed.setter
    def failed(self, status):
        if not isinstance(status, bool):
            raise ModelException('must be boolean')

        if status is False:  # False means Node would not be failed
            # Check for any SRLGs with self as a member and get status
            # of each SRLG
            failed_srlgs = [srlg for srlg in self.srlgs if srlg.failed is True]
            if len(failed_srlgs) > 0:
                self._failed = True
                raise ModelException("Node must be failed since it is a member of one or more SRLGs that are failed")
            else:
                self._failed = False

        else:
            self._failed = True

    @property
    def lat(self):
        """Latitude or y-coordinate of Node on a plot"""
        return self._lat

    @lat.setter
    def lat(self, status):
        if isinstance(status, float) or isinstance(status, int):
            self._lat = status
        else:
            raise ValueError("lat attribute must be integer or float.")

    @property
    def lon(self):
        """Longitude or x-coordinate of Node on a plot"""
        return self._lon

    @lon.setter
    def lon(self, status):
        if isinstance(status, float) or isinstance(status, int):
            self._lon = status
        else:
            raise ValueError("lon attribute must be integer or float.")

    @property
    def igp_shortcuts_enabled(self):
        """Are IGP shortcuts enabled for RSVP LSPs on this Node?
        This is only applicable in the FlexModel; PerformanceModel
        subclass ignores this attribute
        """
        return self._igp_shortcuts_enabled

    @igp_shortcuts_enabled.setter
    def igp_shortcuts_enabled(self, status):
        if isinstance(status, bool):
            self._igp_shortcuts_enabled = status
        elif status == 'True':
            self.igp_shortcuts_enabled = True
        elif status == 'False':
            self.igp_shortcuts_enabled = False
        else:
            raise ValueError("igp_shortcuts must be boolean")

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

        :param model: model Object
        :return: List of adjacent Nodes in model
        """

        adjacencies = self.interfaces(model)

        adjacent_nodes = set()

        for adjacency in adjacencies:
            adjacent_nodes.add(adjacency.remote_node_object)

        return adjacent_nodes

    def add_to_srlg(self, srlg_name, model, create_if_not_present=False):
        """
        Adds self to an SRLG with name=srlg_name in model.

        :param srlg_name: name of srlg
        :param model: Model object
        :param create_if_not_present: Boolean.  Create the SRLG if it
        does not exist in model already.  True will create SRLG in
        model; False will raise ModelException
        :return: None
        """

        # See if model has existing SRLG with name='srlg_name'
        # get_srlg will be the SRLG object with name=srlg_name in model
        # or it will be False if the SRLG with name=srlg_name does not
        # exist in model
        try:
            get_srlg = model.get_srlg_object(srlg_name)
        except ModelException:
            get_srlg = False

        if get_srlg is False:
            # SRLG does not exist
            if create_if_not_present is True:
                new_srlg = SRLG(srlg_name, model)
                model.srlg_objects.add(new_srlg)
                self._srlgs.add(new_srlg)
            else:
                msg = "An SRLG with name {} does not exist in the Model".format(srlg_name)
                raise ModelException(msg)
        else:
            # SRLG does exist in model; add self to that SRLG
            get_srlg.node_objects.add(self)
            self._srlgs.add(get_srlg)

    def remove_from_srlg(self, srlg_name, model):
        """
        Removes self from SRLG with srlg_name in model

        :param srlg_name: name of SRLG
        :param model: Model object
        :return: none
        """
        # See if model has existing SRLG with name='srlg_name'
        # get_srlg will be the SRLG object with name=srlg_name in model
        # or it will be False if the SRLG with name=srlg_name does not
        # exist in model
        try:
            get_srlg = model.get_srlg_object(srlg_name)
        except ModelException:
            get_srlg = False

        if get_srlg is False:
            msg = "An SRLG with name {} does not exist in the Model".format(srlg_name)
            raise ModelException(msg)
        else:
            # Remove self from SRLG
            get_srlg.node_objects.remove(self)
            self._srlgs.remove(get_srlg)

            # If SRLG was failed, change self.failed = False when removed.  If
            # setting self.failed = False generates a ModelException, pass.  The
            # ModelException would happen if the Node was part of a different SRLG
            # that was still failed
            # if get_srlg.failed:
            #     try:
            #         self.failed = False
            #     except ModelException:
            #         pass

            self.failed = False

    @property
    def srlgs(self):
        return self._srlgs

    # TODO add node.fail and node.unfail - low priority - not really
    #  necessary since Model has fail_/unfail_node
