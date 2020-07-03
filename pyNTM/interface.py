"""An object representing a Node interface"""

from .exceptions import ModelException
# from .rsvp import RSVP_LSP
from .srlg import SRLG


class Interface(object):
    """An object representing a Node's Interface"""

    def __init__(self, name, cost, capacity, node_object, remote_node_object,
                 circuit_id=None, rsvp_enabled=True, percent_reservable_bandwidth=100):
        self.name = name
        self.cost = cost
        self.capacity = capacity
        self.node_object = node_object
        self.remote_node_object = remote_node_object
        self.circuit_id = circuit_id  # Has no role in Model object, only in Parallel_Model_Object
        self.traffic = 0.0
        self._failed = False
        self._reserved_bandwidth = 0.0
        self._srlgs = set()
        self.rsvp_enabled = rsvp_enabled
        self.percent_reservable_bandwidth = percent_reservable_bandwidth

    @property
    def _key(self):
        """Unique ID for interface object"""
        return (self.name, self.node_object.name)

    # Modify the __hash__ and __eq__ methods to make comparisons easier
    def __eq__(self, other_object):
        if not isinstance(other_object, Interface):
            return NotImplemented

        return [self.node_object, self.remote_node_object, self.name,
                self.capacity, self.circuit_id] == [other_object.node_object,
                                                    other_object.remote_node_object, other_object.name,
                                                    other_object.capacity, other_object.circuit_id]

    def __ne__(self, other_object):
        return [self.node_object, self.remote_node_object, self.name,
                self.capacity, self.circuit_id] != [other_object.node_object,
                                                    other_object.remote_node_object, other_object.name,
                                                    other_object.capacity, other_object.circuit_id]

    def __hash__(self):
        # return hash(tuple(sorted(self.__dict__.items())))
        return hash(self.name+self.node_object.name)

    def __repr__(self):
        return '%s(name = %r, cost = %s, capacity = %s, node_object = %r, \
remote_node_object = %r, circuit_id = %r)' % (self.__class__.__name__,
                                              self.name,
                                              self.cost,
                                              self.capacity,
                                              self.node_object,
                                              self.remote_node_object,
                                              self.circuit_id)

    @property
    def reservable_bandwidth(self):
        """
        Amount of bandwidth available for rsvp lsp reservation.  If interface is
        not rsvp_enabled, then reservable_bandwidth is set to -1
        """

        if self.rsvp_enabled is True:
            res_bw = (self.capacity * (self.percent_reservable_bandwidth / 100)) - self.reserved_bandwidth
            return round(res_bw, 1)
        else:
            return -1.0

    @property
    def reserved_bandwidth(self):
        """
        Amount of interface capacity reserved by RSVP LSPs
        """
        return round(self._reserved_bandwidth, 1)

    @reserved_bandwidth.setter
    def reserved_bandwidth(self, value):
        """
        Puts logical guardrails on what reserved_bandwidth value can be

        :param value: value of reserved_bandwidth
        :return: None
        """
        if isinstance(value, float) or isinstance(value, int):
            self._reserved_bandwidth = value
        else:
            raise ModelException("Interface reserved_bandwidth must be a float or integer")

    @property
    def failed(self):
        """
        Is interface failed?  Boolean.  It is NOT recommended to directly
        modify this property.  Rather, use Interface.fail or Interface.unfail.

        :return: Boolean - is Interface failed?
        """
        return self._failed

    @failed.setter
    def failed(self, status):
        """
        Puts logical guardrails on conditions of interface failure status

        :param status: boolean; input by user
        :return: self._failed; boolean
        """
        if not (isinstance(status, bool)):
            raise ModelException('must be boolean value')

        # Check for membership in any failed SRLGs
        if status is False:
            # Check for membership in any failed SRLGs
            failed_srlgs = set([srlg for srlg in self.srlgs if srlg.failed is True])

            if len(failed_srlgs) > 0:
                self._failed = True
                self.reserved_bandwidth = 0
                raise ModelException("Interface must be failed since it is a member "
                                     "of one or more SRLGs that are failed")

            # Check to see if both nodes are failed = False
            if self.node_object.failed is False and self.remote_node_object.failed is False:
                self._failed = False

            else:
                self._failed = True
                self.reserved_bandwidth = 0

        else:
            self._failed = True
            self.reserved_bandwidth = 0

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, cost):
        if cost < 1:
            raise ModelException("Interface cost cannot be less than 1")
        if not isinstance(cost, int):
            raise ModelException("Interface cost must be integer")
        self._cost = cost

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        if not(capacity > 0):
            raise ModelException("Interface capacity must be greater than 0")
        self._capacity = capacity

    def fail_interface(self, model):
        """
        Updates the specified interface and the remote interface
        with failed==True

        :param model: model object containing self
        """

        # find the remote interface
        remote_interface = Interface.get_remote_interface(self, model)

        # set the 2 interfaces to failed = True
        self.failed = True
        remote_interface.failed = True

    def unfail_interface(self, model):
        """
        Updates the specified interface and the remote interface
        with failed==False

        :param model: model object containing self
        """

        # find the remote interface
        remote_interface = Interface.get_remote_interface(self, model)  # TODO - use self instead of Interface?

        # check to see if the local and remote node are failed
        if self.node_object.failed is False and self.remote_node_object.failed is False:
            # Set the 2 interfaces to failed = False
            self.failed = False
            remote_interface.failed = False
        else:
            message = "Local and/or remote node are failed; cannot have unfailed interface on failed node"
            raise ModelException(message)

    def get_remote_interface(self, model):
        """
        Returns Interface on other side of the Circuit containing self

        :param model: model object holding self
        :return: Interface object on remote side of Circuit containing self
        """

        for interface in (interface for interface in model.interface_objects):
            if interface.node_object.name == self.remote_node_object.name and interface.circuit_id == self.circuit_id:
                remote_interface = interface
                break

        # Sanity check
        if remote_interface.remote_node_object.interfaces(model) == self.node_object.interfaces(model):
            return remote_interface
        else:  # pragma: no cover
            print("Interface validation debug info follows:")
            print(remote_interface.remote_node_object.interfaces(model))
            print(self.node_object.interfaces(model))
            message = ('Internal Validation Error {} and {} fail validation checks; did you '
                       'forget to run update_simulation() on the model after making a change or '
                       'loading a model file?'.format(remote_interface, self))
            raise ModelException(message)

    def get_circuit_object(self, model):
        """
        Returns the circuit object from the model that an
        interface is associated with.

        :param model: model object containing self
        :return: Circuit object containing self
        """
        ckt = model.get_circuit_object_from_interface(self.name,
                                                      self.node_object.name)
        return ckt

    def demands(self, model):
        """
        Returns list of demands that egress the interface

        :param model: model object containing self
        :return: list of Demand objects egressing self
        """
        dmd_set = set()
        routed_demands = (demand for demand in model.demand_objects if demand.path != 'Unrouted')
        for demand in routed_demands:

            for dmd_path in demand.path:
                # If dmd_path is an RSVP LSP and self is in dmd_path.path['interfaces'] ,
                # look at the LSP path and get demands on the LSP and add them to dmd_set
                from .rsvp import RSVP_LSP
                if isinstance(dmd_path, RSVP_LSP):
                    if self in dmd_path.path['interfaces']:
                        dmd_set.add(demand)

                # If path is not an LSP, then it's a list of Interface
                # objects; look for self in dmd_path

                elif self in dmd_path:
                    # num_paths += 1
                    dmd_set.add(demand)

        dmd_list = list(dmd_set)

        # TODO - add % of each demand that is on the interface next to the demand
        return dmd_list

    def lsps(self, model):
        """
        Returns a list of RSVP LSPs that egress the interface

        :param model: Model object
        :return: list of RSVP LSPs that egress the interface
        """

        lsp_set = set()

        for lsp in (lsp for lsp in model.rsvp_lsp_objects if 'Unrouted' not in lsp.path):
            if self in lsp.path['interfaces']:
                lsp_set.add(lsp)

        lsp_list = list(lsp_set)
        return lsp_list

    @property
    def utilization(self):
        """Returns utilization percent = (self.traffic/self.capacity)*100 """
        if self.traffic == 'Down':
            return 'Int is down'
        else:
            util = (self.traffic / self.capacity)*100
            return float('%.2f' % util)

    @property
    def srlgs(self):
        return self._srlgs

    def add_to_srlg(self, srlg_name, model, create_if_not_present=False):
        """
        Adds self to an SRLG with name=srlg_name in model.  Also finds the
        remote Interface object and adds that to the SRLG.

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

                # Add remote interface
                remote_int = self.get_remote_interface(model)
                remote_int._srlgs.add(new_srlg)
            else:
                msg = "An SRLG with name {} does not exist in the Model".format(srlg_name)
                raise ModelException(msg)
        else:
            # SRLG does exist in model; add self to that SRLG
            get_srlg.interface_objects.add(self)
            self._srlgs.add(get_srlg)

            # Add remote interface
            remote_int = self.get_remote_interface(model)
            get_srlg.interface_objects.add(remote_int)
            remote_int._srlgs.add(get_srlg)

    def remove_from_srlg(self, srlg_name, model):
        """
        Removes self and remote interface object from SRLG with srlg_name in model.

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
            get_srlg.interface_objects.remove(self)
            self._srlgs.remove(get_srlg)

            # Remove remote interface from SRLG
            remote_int = self.get_remote_interface(model)
            get_srlg.interface_objects.remove(remote_int)
            remote_int._srlgs.remove(get_srlg)

        self.failed = False
