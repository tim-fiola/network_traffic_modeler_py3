"""An object representing a Node interface"""

from .circuit import Circuit

class Interface(object):
    """An object representing a Node interface"""

    def __init__(self, name, cost, capacity, node_object, remote_node_object,
                 address = 0):
        self.name = name
        self.cost = cost
        self.capacity = capacity
        self.node_object = node_object
        self.remote_node_object = remote_node_object
        self.address = address
        self.traffic = 0.0

        self._failed = False

        validation_info = []
        
        # Validate cost and capacity values
        if not(isinstance(cost, (int, float))):
            raise ValueError('Cost must be positive integer or float')
        if not(isinstance(capacity, (int, float))):
            raise ValueError('Capacity must be positive integer or float')        

    @property
    def _key(self):
        """Unique ID for interface object"""
        return (self.name, self.node_object.name)

    # Modify the __hash__ and __eq__ methods to make comparisons easier
    def __eq__(self, other_object):
        if not isinstance(other_object, Interface):
            return NotImplemented

        return self.__dict__ == other_object.__dict__
    
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


    def __repr__(self):
        return '%s(name = %r, cost = %s, capacity = %s, node_object = %r, \
remote_node_object = %r, address = %r)'%(self.__class__.__name__,
                                           self.name,
                                            self.cost,
                                            self.capacity,
                                            self.node_object,
                                            self.remote_node_object,
                                            self.address)

    ###### TODO - is this call necessary?! ####
    @staticmethod
    def get_interface(interface_name, node_name, model):
        """Returns an interface object for specified node name and interface name"""

        for interface in (interface for interface in model.interface_objects):
            if interface.node_object.name == node_name and \
               interface.name == interface_name:
                needed_interface = interface
                break

        return needed_interface
        
    @property
    def failed(self):
#        print 'called getter'
        return self._failed

    @failed.setter
    def failed(self, status):
#        print 'called setter: failed =', status
        if not(isinstance(status, bool)):
            raise ModelException('must be boolean value')

        if status == False:

            #Check to see if both nodes are failed = False
            if self.node_object.failed == False and \
               self.remote_node_object.failed == False:
                self._failed = False

            else:
                self._failed = True
            
        else:
            self._failed = True

    def fail_interface(self, model):
        """Returns an updated model with the specified
        interface and the remote interface with failed==True 
        """

        # find the remote interface
        remote_interface = Interface.get_remote_interface(self, model)

        # set the 2 interfaces to failed = True
        self.failed = True
        remote_interface.failed = True
    
    def unfail_interface(self, model):
        """Returns an updated network_interfaces table with the specified
        interface and the remote interface in the 'failed': False state
        """

        # find the remote interface
        remote_interface = Interface.get_remote_interface(self, model)

        # check to see if the local and remote node are failed
        if self.node_object.failed == False and \
           self.remote_node_object.failed == False:

            # set the 2 interfaces to failed = False
            self.failed = False
            remote_interface.failed = False
        else:
            message = "Local and/or remote node are failed; cannot have \
unfailed interface on failed node"
            raise ModelException(message)

    def get_remote_interface(self, model):
        """Searches the model and returns the remote interface"""
        
        for interface in (interface for interface in model.interface_objects):
            if interface.node_object.name == self.remote_node_object.name and \
               interface.address == self.address:
                remote_interface = interface
                break

        # sanity check
        if remote_interface.remote_node_object.interfaces(model) == \
           self.node_object.interfaces(model):
            return remote_interface
        else:
            message = 'Internal Validation Error', remote_interface, \
                      'and', self, 'fail validation checks'
            raise ModelException(message)

    def get_circuit(self, model):
        """Returns the circuit that an interface is associated with"""
        unknown_interface_node_object = self.remote_node_object
        address = self.address

        circuit_found = False

        for candidate_interface in model.interface_objects:
            if candidate_interface.node_object == unknown_interface_node_object \
               and candidate_interface.address == address:
                unknown_interface = candidate_interface
                circuit_found = True
                break
      
        else:
            message = self, 'has no corresponding interface in the \
network_interfaces table'
            raise ModelException(message)

        if circuit_found == True:
            # double check
            if not(unknown_interface.remote_node_object == self.node_object):
                message = 'Internal Validation Error:', self ,' and', \
                unknown_interface, ' do not match up in the network_interfaces \
        table for the (node, remote_node, address):', \
        unknown_interface.remote_node_object, self.node_object, \
        unknown_interface.remote_node_object == self.node_object
                raise ModelException(message)

            # Create the circuit
            interface_a_key = self._key
            interface_b_key = unknown_interface._key

            return Circuit(interface_a_key, interface_b_key)

        else:
            message = self, 'has no corresponding interface in the \
network_interfaces table'
            raise ModelException(message)

    def demands(self, model):
        """Returns list of demands that egress the interface"""
        dmd_list = []
        demands = model.demand_objects
        for demand in demands:
            for demand_path in demand.path:
                if self in demand_path:
                    dmd_list.append(demand)

        return dmd_list

    @property
    def utilization(self):
        """Returns utilization = (self.traffic/self.capacity)*100% """
        if self.traffic == 'Down':
            return 'Int is down'
        else:
            return self.traffic/self.capacity
        
    
