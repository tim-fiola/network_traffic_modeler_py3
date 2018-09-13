"""A class that defines the network being modeled and that contains all modeled objects
in the network such as Nodes, Interfaces, Circuits, and Demands.
"""

import copy
import networkx as nx
import pdb
from pprint import pprint

from .circuit import Circuit
from .demand import Demand
from .interface import Interface
from .model_exception import ModelException
from .node import Node

class Model(object):
    """A network model object consisting of the following base components:
        - Interface objects: network node interfaces.  Interfaces have a
          'capacity' attribute that determines how much traffic it can carry.
          Note: Interfaces are matched into Circuit objects based on the
          interface addresses 
        
        - Node objects: vertices on the network (aka 'layer 3 devices')
          that contain Interface objects.  Nodes are connected to each other
          via a pair of matched Interfaces (Circuits)
        
        - Demand objects: traffic loads on the network.  Each demand starts
          from a source node and transits the network to a destination node.
          A demand also has a magnitude, representing how much traffic it
          is carrying.  The demand's magnitude will apply against each
          interface's available capacity
          
        
    """

    def __init__(self, interface_objects = set([]), node_objects = set([]),
                 demand_objects = set([])):
        self.interface_objects = interface_objects
        self.node_objects = node_objects
        self.demand_objects = demand_objects
        self._orphan_nodes = set([])
        self.circuit_objects = set([])

    def __repr__(self):
        return 'Model(Interfaces: %s, Nodes: %s, Demands: %s)'%(len(self.interface_objects),
                                len(self.node_objects),
                                len(self.demand_objects))

    @classmethod
    def create_network_model(cls, network_interfaces):
        """
        A tool that reads network interface info and returns a new model.
        Interface info must be in format like below example:

        network_interfaces = [
        {'name':'A-to-B', 'cost':4,'capacity':100, 'node':'A',
         'remote_node': 'B', 'address': 1, 'failed': False},
        {'name':'A-to-Bv2', 'cost':40,'capacity':150, 'node':'A',
         'remote_node': 'B', 'address': 2, 'failed': False},
        {'name':'A-to-C', 'cost':1,'capacity':200, 'node':'A',
         'remote_node': 'C', 'address': 3, 'failed': False},]
        """

        interface_objects, node_objects = \
                           Model._make_network_interfaces(network_interfaces)
        
        model = Model(interface_objects, node_objects) 
        
        self._make_circuits()
        
        validated_network_model = model.validate_model()

        return validated_network_model

    def add_network_interfaces_from_list(self, network_interfaces):
        """
        A tool that reads network interface info and updates an existing model.
        Interface info must be in format like below example:

        network_interfaces = [
        {'name':'A-to-B', 'cost':4,'capacity':100, 'node':'A',
         'remote_node': 'B', 'address': 1, 'failed': False},
        {'name':'A-to-Bv2', 'cost':40,'capacity':150, 'node':'A',
         'remote_node': 'B', 'address': 2, 'failed': False},
        {'name':'A-to-C', 'cost':1,'capacity':200, 'node':'A',
         'remote_node': 'C', 'address': 3, 'failed': False},]
        """        
        new_interface_objects, new_node_objects = \
                           self._make_network_interfaces(network_interfaces)
#        print("new_node_objects =", new_node_objects)
        self.node_objects = self.node_objects.union(new_node_objects)
        self.interface_objects = \
                        self.interface_objects.union(new_interface_objects)

        #print("validating model") # Debug
        
        self.validate_model()        

    def validate_model(self):
        """
        Validates that data fed into the model creates a valid network model
        """
        
        # create circuits table, flags ints that are not part of a circuit
        circuits = self._make_circuits(return_exception = False)

        # Find objects in interface_objects that are not Interface objects
        non_interface_objects = set()
        non_bool_failed = set() # ints with non-boolean failed attribute
        metrics_not_ints = set() # ints with non-integer cost value
        capacity_not_number = set() # ints with non-numerical capacity value

        error_data = [] # list of all errored checks

        # Validate the individual interface entries
        for interface in (interface for interface in self.interface_objects):

            # Make sure is instance Interface
            if not (isinstance(interface, Interface)):
                non_interface_objects.add(interface)

            # Make sure 'failed' values are either True or False
            if isinstance(interface.failed, bool) == False:
                non_bool_failed.add(interface)

            # Make sure 'metric' values are integers
            if isinstance(interface.cost, int) == False:
                metrics_not_ints.add(interface)
                #print("metric not integer for interface", interface) # Debug

            # Make sure 'capacity' values are numbers
            if isinstance(interface.capacity, (float, int)) == False:
                capacity_not_number.add(interface)

        # If creation of circuits returns a dict, there are problems        
        if isinstance(circuits, dict):
            error_data.append({'ints_w_no_remote_int': circuits['data']})

        # Append any failed checks to error_data
        if len(non_interface_objects) > 0:
            error_data.append(non_interface_objects)

        if len(non_bool_failed) > 0:
            error_data.append({'non_boolean_failed': non_bool_failed})

        if len(metrics_not_ints) > 0:
            error_data.append({'non_integer_metrics': metrics_not_ints})

        if len(capacity_not_number) > 0:
            error_data.append({'invalid_capacity': capacity_not_number})

        # Validate there are no duplicate interfaces              
        unique_interfaces_per_node = self._unique_interface_per_node()

        if unique_interfaces_per_node != True:
            error_data.append(unique_interfaces_per_node)            

        # Make validate_model() check for matching failed statuses
        # on the interfaces and matching interface capacity
        circuits_with_mismatched_interface_capacity = []
        for ckt in (ckt for ckt in self.get_circuit_objects()):
            int1 = ckt.get_circuit_interfaces(self)[0]
            int2 = ckt.get_circuit_interfaces(self)[1]

            # Match the failed status to True if they are different
            if int1.failed != int2.failed:
                int1.failed = True
                int2.failed = True

            # Make sure the interface capacities in the circuit match
            if int1.capacity != int2.capacity:
                circuits_with_mismatched_interface_capacity.append(ckt)                

        if len(circuits_with_mismatched_interface_capacity) > 0:
            int_status_error_dict = {\
                'circuits_with_mismatched_interface_capacity':\
                circuits_with_mismatched_interface_capacity}
            error_data.append(int_status_error_dict)

        # Verify no duplicate nodes
        node_names = set([node.name for node in self.node_objects])
        if (len(self.node_objects)) != (len(node_names)):
            node_dict = {'len_node_objects': len(self.node_objects),
                         'len_node_names': len(node_names)}
            error_data.append(node_dict)

        # Read error_data
        if len(error_data) > 0:
            message = 'network interface validation failed, see returned data'
            raise ModelException(message, error_data)
        else:
            return self

    def get_circuit_objects(self):
        """Returns a set of circuit objects in the Model"""
        return self.circuit_objects

    def update_simulation(self):
        """Returns model with updated interface traffic.
        Must be called to update the model whenever there is a topology change.
        """

        # This list of interfaces can be used to route traffic
        non_failed_interfaces = set()
        available_nodes = set()

        # Find all the non-failed interfaces in the model and
        # add them to non_failed_interfaces; also find all the nodes
        # associated with the non-failed interfaces       
        for interface_object in self.interface_objects:
            if interface_object.failed == False:
                non_failed_interfaces.add(interface_object)
                available_nodes.add(interface_object.node_object)
                available_nodes.add(interface_object.remote_node_object)

        # Create a model consisting only of the non-failed interfaces and
        # corresponding nodes
        non_failed_interfaces_model = Model(non_failed_interfaces, 
                                            available_nodes)
 
        # Find paths for each demand in the non_failed_interfaces_model
        for demand_object in self.demand_objects:
            demand_object = demand_object._add_demand_path(non_failed_interfaces_model)

        # In the model, in an interface is failed, set the traffic attribute to 'Down',
        # otherwise, initialize the traffic to zero
        for interface_object in self.interface_objects:
            if interface_object.failed == True:
                interface_object.traffic = 'Down'
            else:
                interface_object.traffic = 0.0


        # For each demand that is not Unrouted, add its traffic value to each
        # interface object in the path
        for demand_object in self.demand_objects:
            traffic = demand_object.traffic
            
            if demand_object.path != 'Unrouted':

                # Find each demands path list, determine the ECMP split, and find
                # the traffic per path
                demand_object_paths = demand_object.path
                num_demand_paths = float(len(demand_object_paths))
                ecmp_split = 1/num_demand_paths
                traffic_per_demand_path = traffic * ecmp_split

                # Add the traffic per path to each interface the demand touches.
                # Not sure if there's a way to optimize this since
                # we have to do a lookup to modify the traffic attribute
                for demand_object_path in demand_object_paths:
                    for demand_path_interface in demand_object_path:
                        # Get the interface's existing traffic and add the portion
                        # of the demand's traffic
                        existing_traffic = demand_path_interface.traffic
                        existing_traffic = existing_traffic + traffic_per_demand_path
                        demand_path_interface.traffic = existing_traffic

    def _unique_interface_per_node(self):
        """Checks that the interface names on each node are unique; returns
        an message if a duplicate interface name is found on the same node
        """

        checked_interfaces = set() # interfaces that have been checked
        exception_interfaces = set() # duplicate interfaces

        iterator = (interface_obj for interface_obj in self.interface_objects)
        for interface in iterator:
            if interface in checked_interfaces:
                exception_interfaces.add(interface)
            else:
                checked_interfaces.add(interface)

        if len(exception_interfaces)>0:
            message = "Interface names must be unique per node.  The following \
nodes have duplicate interface names %s"%exception_interfaces
            return message
        else:
            return True

    def _make_circuits(self, return_exception = True):
        """Matches interface objects into circuits and returns the circuits list"""
 
        G = self._make_weighted_network_graph()
        
        # Determine which interfaces pair up into good circuits in G
        paired_interfaces = ((local_node_name, remote_node_name, data) for \
        (local_node_name, remote_node_name, data)  in \
        G.edges(data=True) if G.has_edge(remote_node_name, local_node_name))
        
        # Set interface object in_ckt = False and baseline the address
        for interface in (interface for interface in self.interface_objects):
             interface.in_ckt = False        
        address_number = 1
        circuits = set([])
        
        # Using the paired interfaces (source_node, dest_node) pairs from G,
        # get the corresponding interface objects from the model to create
        # the circuit object
        for interface in (interface for interface in paired_interfaces):
            # Get each interface from model for each 
            int1 = self.get_interface_object_from_nodes(interface[0], 
                                                        interface[1])
            int2 = self.get_interface_object_from_nodes(interface[1],
                                                        interface[0])
            
            if (int1.in_ckt == False and int2.in_ckt == False):
                # Mark interface objects as in_ckt = True
                int1.in_ckt = True
                int2.in_ckt = True
                
                # Add address to interface objects
                int1.address = address_number
                int2.address = address_number
                address_number = address_number + 1
            
                ckt = Circuit(int1, int2)
                circuits.add(ckt)

        # Find any interfaces that don't have counterpart
        exception_ints_not_in_ckt = [(local_node_name, remote_node_name, data) \
            for (local_node_name, remote_node_name, data) in \
                G.edges(data=True) if not(G.has_edge(remote_node_name, local_node_name))]
                
        if len(exception_ints_not_in_ckt) > 0:             
            exception_msg = 'WARNING: These interfaces were not matched into a \
            circuit', exception_ints_not_in_ckt
            if return_exception == True:
                raise ModelException(exception_msg)
            else:
                return {'data': exception_ints_not_in_ckt}

        self.circuit_objects = circuits
      
        
    def get_interface_object_from_nodes(self, local_node_name, remote_node_name):
        """Returns an interface object with the specified local and 
        remote node names """
        for interface in (interface for interface in self.interface_objects):
            if interface.node_object.name == local_node_name and \
                interface.remote_node_object.name == remote_node_name:
                return interface
                break

    @property
    def all_interface_addresses(self):
        """Returns all interface addresses"""
        return set(interface.address for interface in self.interface_objects)

    def add_circuit(self, node_a_object, node_b_object, node_a_interface_name,
                    node_b_interface_name, cost_intf_a = 1, cost_intf_b = 1,
                    capacity = 1000, failed = False, address = None):
        """Adds a circuit object to the model object"""

        if address == None:
            addresses = self.all_interface_addresses
            if len(addresses) == 0:
                address = 1
            else:
                address = max(addresses) + 1
        
        int_a = Interface(node_a_interface_name, cost_intf_a, capacity,
                          node_a_object, node_b_object, address)
        int_b = Interface(node_b_interface_name, cost_intf_b, capacity,
                          node_b_object, node_a_object, address)

        self.interface_objects.add(int_a)
        self.interface_objects.add(int_b)

        self.validate_model()

    def is_node_an_orphan(self, node_object):
        """Determines if a node is in orphan_nodes"""
        if node_object in self.orphan_nodes:
            return True
        else:
            return False

    def get_orphan_node_objects(self):
        """Returns Nodes that have no interfaces"""
        for node in self.node_objects:
            if len(node.interfaces(self)) == 0:
                self._orphan_nodes.add(node)
        return self._orphan_nodes

    def add_node(self, node_object):
        """Adds a node object to the model object"""

        if node_object.name in [node.name for node in self.node_objects]:
            message = "A node with name %s already exists in the model"\
                      %node_object.name
            raise ModelException(message)
        else:
            self.node_objects.add(node_object)

        self.validate_model()
  
    def get_node_object(self, node_name):
        """Returns a node object, given a node's name"""

        # TODO - It seems like this part could be optimized
        node_object_list = [node for node in self.node_objects]
        node_names = [node.name for node in node_object_list]
        
#        pdb.set_trace()
        
        if node_name in node_names:
            node_index = node_names.index(node_name)
            node_object = node_object_list[node_index]
            return node_object
        else:
            message = "No node with name %s exists in the model"%node_name
            raise ModelException(message)

    def _make_network_interfaces(self, interface_info_list):
        """Returns Interface objects"""
        network_interface_objects = set([])
        network_node_objects = set([])
        for interface in interface_info_list:
            intf = Interface(interface['name'], interface['cost'],
                             interface['capacity'], Node(interface['node']),
                             Node(interface['remote_node']),
                             interface['address'])
            network_interface_objects.add(intf)

            # Check to see if the node already exists, if not, add it
            node_names = ([node.name for node in self.node_objects])
            if interface['node'] not in node_names:
                network_node_objects.add(Node(interface['node']))
            if interface['remote_node'] not in node_names:
                network_node_objects.add(Node(interface['remote_node']))

                   
        return (network_interface_objects, network_node_objects)

    def add_demand(self, source_node_name, dest_node_name, traffic = 0, name = 'none'):
        """Adds a traffic load from point A to point B in the model"""
        source_node_object = self.get_node_object(source_node_name)
        dest_node_object = self.get_node_object(dest_node_name)
        added_demand = Demand(source_node_object, dest_node_object, 
                                traffic, name)
        if added_demand in self.demand_objects:
            message = added_demand,' already exists in demand_objects'
            raise ModelException()
        self.demand_objects.add(added_demand)

        self.validate_model()
        

    def get_demand_object(self, source_node_name, dest_node_name, demand_name='none'):
        """Returns demand specified by the source_node_name, dest_node_name, name;
        throws exception if demand not found
        """
        source_node_object = self.get_node_object(source_node_name) 
        dest_node_object = self.get_node_object(dest_node_name)
        demand_key = (source_node_object.name, dest_node_object.name, demand_name)
        
        model_demand_keys = (demand_object._key for demand_object in \
                            self.demand_objects)
       
        model_demand_iterator = (demand for demand in self.demand_objects)
        
        demand_to_return = None
        
        for demand in model_demand_iterator:
            if demand.source_node_object.name == source_node_name and \
                demand.dest_node_object.name == dest_node_name and \
                demand.name == demand_name:
                    demand_to_return = demand
                    return demand_to_return
                    break
        
        if demand_to_return == None:
            raise ModelException('no matching demand')
   
    # Interface calls
    def get_interface_object(self, interface_name, node_name):
        """Returns an interface object for specified node name and interface name"""       

        self._does_interface_exist(interface_name, node_name)
        
        node_object = self.get_node_object(node_name)

        interface_name_list = [interface.name for
                              interface in node_object.interfaces(self)]

        if interface_name in interface_name_list:
            index = interface_name_list.index(interface_name)
            needed_interface = node_object.interfaces(self)[index]
            return needed_interface
        else:
            
            msg = "Interface(%s, %s, NA) does not exist"%(interface_name,
                                                          node_name)
            raise ModelException(msg)
            
    def _does_interface_exist(self, interface_name, node_object_name):
        int_key = (interface_name, node_object_name)
        interface_key_iterator = (interface._key for interface in \
                                  self.interface_objects)
        if int_key not in (interface_key_iterator):
            raise ModelException('specified interface does not exist')

    def get_circuit_object_from_interface(self, interface_name, node_name):
        """Returns a circuit object, given a node and interface name"""

        # Does interface exist?
        self._does_interface_exist(interface_name, node_name)
        
        interface = self.get_interface_object(interface_name, node_name, self)
        remote_interface = interface.get_circuit(self)

        interface_object_iterator = (interface_object for interface_object in \
                                     self.interface_objects)
        
        for interface in interface_object_iterator:
            if interface.node_object == node_object and \
               interface.name == interface_name:

                remote_interface = interface.get_remote_interface(self)

                circuit = Circuit(interface, remote_interface)
                break

        return circuit


    ##### Convenience calls #####
    def get_failed_interface_objects(self):
        """Returns a list of all failed interfaces"""
        failed_interfaces = []

        for interface in self.interface_objects:
            if interface.failed == True:
                failed_interfaces.append(interface)

        return failed_interfaces

    def get_non_failed_interface_objects(self):
        """Returns a list of all operational interfaces"""
        non_failed_interfaces = []

        for interface in (interface for interface in self.interface_objects):
            if interface.failed == False:
                int_object = self.get_interface_object(interface.name,
                                                interface.node_object.name)
                non_failed_interfaces.append(int_object)

        return non_failed_interfaces        

    def get_unfailed_interface_objects(self):
        unfailed_interface_objects = set()

        interface_iter = (interface for interface in self.interface_objects)

        for interface in interface_iter:
            if interface.failed == False:
                unfailed_interface_objects.add(interface)

        return unfailed_interface_objects

    def get_unrouted_demand_objects(self):
        """
        Returns list of demand objects that cannot be routed
        """
        unrouted_demands = []
        for demand in self.demand_objects:
            if demand.path == "Unrouted":
                unrouted_demands.append(demand)

        return unrouted_demands
        
    def change_interface_name(self, node_name,
                              current_interface_name,
                              new_interface_name):
        """Changes interface name"""
        interface_to_edit = self.get_interface_object(current_interface_name, node_name)
        interface_to_edit.name = new_interface_name

        return interface_to_edit
    
    def fail_interface(self, interface_name, node_name):
        """Fails the interface object for the node_name/interface_name pair"""

        # Get the interface object
        interface_object = self.get_interface_object(interface_name, node_name)

        # Does interface exist?
        if interface_object not in set(self.interface_objects):
            ModelException('specified interface does not exist')

        
        # find the remote interface
        remote_interface_object = interface_object.get_remote_interface(self)

        remote_interface_object.failed = True
        interface_object.failed = True
        self.validate_model()

    def unfail_interface(self, interface_name, node_name, raise_exception=False):
        """Fails the interface object for the interface_name, node_object,
        remote_node_object tuple.
        
        If raise_excecption=True, an exception
        will be raised if the interface cannot be unfailed.
        An example of this would be if you tried to unfail the interface
        when the parent node or remote node was in a failed state"""

        if not(isinstance(raise_exception, bool)):
            message = "raise_exception must be boolean value"
            raise ModelException(message)

        # Get the interface object
        interface_object = self.get_interface_object(interface_name, node_name)

        # Does interface exist?
        if interface_object not in set(self.interface_objects):
            ModelException('specified interface does not exist')
        
        # Find the remote interface
        remote_interface = interface_object.get_remote_interface(self)

        # Ensure local and remote nodes are failed = False
        if self.get_node_object(interface_object.node_object.name).failed == False and \
           self.get_node_object(remote_interface.node_object.name).failed == False:

            remote_interface.failed = False
            interface_object.failed = False
            self.validate_model()
        else:

            if raise_exception == True:
                message = "Local and/or remote node are failed; cannot have \
    unfailed interface on failed node"
                raise ModelException(message)
    
    # Path-related calls
    def _get_initial_candidate_paths(self, source_node_object, dest_node_object):
        """Returns a dict containing adjacencies of the source node
        (initial_candidate_paths) and any first order feasible paths (those
        paths where the dest node a direct adjacency to the source node)
        """
        # Get all non-failed interfaces on the source node
        initial_candidate_paths = [interface for interface in \
                                  source_node_object.interfaces(self) \
                                  if interface.failed==False]

        initial_candidate_path_list = []

        # A list of complete paths from source to dest
        feasible_paths_in_def = []

        for interface in initial_candidate_paths:
            if interface.failed == False:
                if interface.remote_node_object.name == dest_node_object.name:
                    feasible_paths_in_def.append([interface])
                else:
                    initial_candidate_path_list.append([interface])

        return {'initial_candidate_paths': initial_candidate_path_list,
                'feasible_paths': feasible_paths_in_def}

    def _examine_candidate_paths(self, source, dest, candidate_paths,
                                feasible_paths):
        """Returns feasible (loop free) paths between source and dest"""

        for path in candidate_paths:
            node_path = [source.name]

            last_interface = path[-1]

            for interface_object in path:
                node_path.append(interface_object.remote_node_object.name)

            most_recent_node = node_path[-1]
            most_recent_node_interfaces = \
                    [interface for interface in \
                     Node(most_recent_node).interfaces(self) \
                     if interface.failed==False]

            for interface_object in most_recent_node_interfaces:
                if interface_object.failed == False: #this
                    remote_node = interface_object.remote_node_object.name
                    if remote_node in node_path:
                            continue # There's a loop, move on to next adjacency
                    elif remote_node == dest.name:
                            feasible_path = path[:]
                            feasible_path.append(interface_object)
                            feasible_paths.append(feasible_path)
                    elif remote_node not in node_path:
                            good_path = path[:]
                            good_path.append(interface_object)
                            candidate_paths.append(good_path)

        return  feasible_paths

    def get_feasible_paths_old(self, source_node_object, dest_node_object):
        """Returns a list of all feasible (loop free) paths from source node
        object to dest node object
        """

        data = self._get_initial_candidate_paths(source_node_object, 
                                            dest_node_object)

        initial_candidate_paths = data['initial_candidate_paths']
        feasible_paths = data['feasible_paths']

        feasible_paths = self._examine_candidate_paths(source_node_object, 
                                                dest_node_object,
                                                initial_candidate_paths,
                                                feasible_paths)
        return feasible_paths


    def get_feasible_paths(self, source_node_name, dest_node_name):
        """Returns a list of all feasible (loop free) paths from source node
        object to dest node object
        """
        
        source_node_object = self.get_node_object(source_node_name)
        dest_node_object = self.get_node_object(dest_node_name)
        
        # Convert model to networkx DiGraph
        G = self._make_weighted_network_graph()
        
        # Get the paths
        all_feasible_digraph_paths = nx.all_simple_paths(G, source_node_name,
                                                            dest_node_name,)

        # Convert each path to the Model format
        model_feasible_paths = []
        for digraph_path in all_feasible_digraph_paths:
            model_path = self._convert_nx_path_to_model_path(digraph_path)
            model_feasible_paths.append(model_path)
        
        # Return the paths
        return model_feasible_paths
        
    def get_shortest_path(self, source_node_name, dest_node_name):
        """For a source and dest node name pair, find the shortest path.
        Return the shortest path in dictionary form:
        shortest_path = {'path': [list of shortest path routes], 
                            'cost': path_cost}
        """
        
        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph()

        # Define the Model-style path to be built
        converted_path = {}
        converted_path['path'] = []
        converted_path['cost'] = None

        
        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(G, source_node_name,
                                                dest_node_name,
                                                weight = 'cost')
        #try:
            #next(digraph_shortest_paths)
        #except nx.NetworkXNoPath:
            #print("no paths!!!")

      



        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path)
                converted_path['path'].append(model_path)
                converted_path['cost'] = nx.shortest_path_length(G, source_node_name, 
                                                            dest_node_name, weight='cost')
            return converted_path
        except:
            return converted_path
      

    def _convert_nx_path_to_model_path(self, nx_graph_path):
        """Given a path from an networkx DiGraph, converts that 
        path to a Model style path and returns that Model style path"""
        
        # Define a model-style path to build
        model_path = []
        # look at each hop in the path
        for hop in nx_graph_path:
            current_hop_index = nx_graph_path.index(hop)
            next_hop_index = current_hop_index+1
            if current_hop_index + 1 < len(nx_graph_path):
                #current_node = model1.get_node_object(hop)
                next_hop = nx_graph_path[next_hop_index]
                #next_hop_node = model1.get_node_object(next_hop)
                interface = self.get_interface_object_from_nodes(hop,next_hop)
                model_path.append(interface)
        
        return model_path
        
    ###### NODE CALLS ######
    def get_node_interfaces(self, node_name):
        """Returns list of interfaces on specified node name"""
        return Node(node_name).interfaces(self)

    def fail_node(self, node_name):
        """Fails specified node"""

        # Find node's interfaces and fail them
        ints_to_fail_iterator = (interface for interface in \
                                 self.get_node_interfaces(node_name))
        
        for interface in ints_to_fail_iterator:
            self.fail_interface(interface.name, node_name)

        # Change the failed property on the specified node
        self.get_node_object(node_name).failed = True

    def unfail_node(self, node_name):
        """Unfails the specified node"""

        # Change the failed property on the specified node
        self.get_node_object(node_name)._failed = False 
        
        # Find node's interfaces and unfail them
        ints_to_unfail_iterator = (interface for interface in \
                                 self.get_node_interfaces(node_name))

        node_to_unfail = self.get_node_object(node_name)

        for interface in ints_to_unfail_iterator:

            # Unfail the interfaces if the remote node is not failed
            if interface.remote_node_object.failed == False:
                # Unfail the specific interface
                self.unfail_interface(interface.name, node_name, False)

                # Unfail the remote interface
                remote_int = interface.get_remote_interface(self)
                self.unfail_interface(remote_int.name,
                                     remote_int.node_object.name, False)

    def get_failed_node_objects(self):
        """Returns a list of all failed nodes"""
        failed_nodes = []

        for node in (node for node in self.node_objects):
            if node.failed == True:
                node_object = self.get_node_object(node.name)
                failed_nodes.append(node_object)
                
        return failed_nodes

    def get_non_failed_node_objects(self):
        """Returns a list of all failed nodes"""
        non_failed_nodes = []

        for node in (node for node in self.node_objects):
            if node.failed == False:
                node_object = self.get_node_object(node.name)
                non_failed_nodes.append(node_object)

        return non_failed_nodes

    ##### Display calls #########
    def display_interface_status(self):
        """Returns failed = True/False for each interface"""

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12),
              end=' ')
        print('Failed'.ljust(12))

        interface_iterator = (interface for interface in self.interface_objects)

        for interface in interface_iterator:
            print(interface.node_object.name.ljust(12), interface.name.ljust(12), end=' ')
            print(interface.remote_node_object.name.ljust(12), end=' ')
            print(str(interface.failed).ljust(12))

    def display_node_status(self):
        """Returns failed = True/False for each node"""

        print('Node'.ljust(12), 'Failed'.ljust(12))

        node_iterator = (node for node in self.node_objects)
        
        for node in node_iterator:
            print(node.name.ljust(12), str(node.failed).ljust(12))
            
    def display_interfaces_traffic(self):
        """A human-readable(-ish) display of interfaces and traffic on each"""

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12),\
              'Traffic'.ljust(12))
        
        interface_iterator = (interface for interface in self.interface_objects)

        for interface in interface_iterator:
            print(interface.node_object.name.ljust(12), interface.name.ljust(12), end=' ')
            print(interface.remote_node_object.name.ljust(12), end=' ')
            print(repr(interface.traffic).ljust(12))

    def display_demand_paths(self):
        """Displays each demand and its path(s) across the network"""

        demand_iter = (demand for demand in self.demand_objects)

        for demand in demand_iter:
            print('demand._key is', demand._key)
            print('Demand has %s paths:' %(len(demand.path)))
            for path in demand.path:
                pprint(path)
                print()
            print()
            print()

    def display_interface_objects(self):
        """Displays interface objects in a more human readable manner"""

        for interface in self.interface_objects:
            pprint(interface)
            print()

    def _make_weighted_network_graph(self):
        """Returns a networkx weighted network directional graph from 
        the input Model object"""
        G = nx.DiGraph()
        
        edge_names = ((interface.node_object.name, 
                        interface.remote_node_object.name, interface.cost) \
            for interface in self.interface_objects)
        # Add edges to networkx DiGraph
        G.add_weighted_edges_from(edge_names, weight = 'cost')
        
        return G

    
    def create_demand_objects_from_list(self, list_of_demand_properties):
        """Creates demand object from a list of demand properties and 
        adds it to the model.
        
        The demand properties list must have the following format:
        demand_properties = [   {'source': 'A', 'dest': 'B', 'traffic': 50, 'name': 'demand1'},
                                {'source': 'A', 'dest': 'F', 'traffic': 22},]
                                
        Note: if a demand name is not provided, the name will default to 'none'
        """
        
        demands = []
        for demand in list_of_demand_properties:
            if 'name' in demand.keys():
                demand_name = demand['name']
            else: 
                demand_name = 'none'
            self.add_demand(demand['source'], demand['dest'], 
                demand['traffic'], demand_name)

    @staticmethod
    def load_model_file(data_file):
        """Opens a network_modeling data file and returns a model containing
        the info in the data file.  The data file must be of the appropriate
        format to produce a valid model"""
        # Open the file with the data, read it, and split it into lines
        with open(data_file, 'r') as f:
            data = f.read()
    
        lines = data.splitlines()
    
        # Define the interfaces info 
        int_info_begin_index = 2
        int_info_end_index = lines.index("NODES_TABLE,,,,") - 1
        interface_lines = lines[int_info_begin_index:int_info_end_index]
        interface_set = set([]) 
        node_list = []
        for interface_line in interface_lines:
            node_name, remote_node_name, name, cost, capacity = \
                        interface_line.split(',')
            interface_set.add(Interface(name, int(cost), int(capacity), Node(node_name),
                                Node(remote_node_name)))
            node_list.append(Node(node_name))
            node_list.append(Node(remote_node_name))
        model = Model(interface_set, set(node_list))
        
        # Define the nodes info
        nodes_info_begin_index = int_info_end_index + 3
        nodes_info_end_index = lines.index("DEMANDS_TABLE,,,,") -1
        node_lines = lines[nodes_info_begin_index:nodes_info_end_index]
        node_names = set([node.name for node in node_list])
        for node_line in node_lines:
            node_info = node_line.split(',')
            node_name = node_info[0]
            try:
                node_lat = int(node_info[1])
            except ValueError:
                node_lat = 0
            try:
                node_lon = int(node_info[2])
            except ValueError:
                node_lon = 0        
            if node_name not in node_names: # Pick up orphan nodes
                new_node = Node(node_name)
                model.add_node(new_node)
                new_node.lat = node_lat
                new_node.lon = node_lon
            else:
                model.get_node_object(node_name).lat = node_lat
                model.get_node_object(node_name).lon = node_lon
        
        # Define the demands info
        demands_info_begin_index = nodes_info_end_index + 3
        demands_lines = lines[demands_info_begin_index:]
        for demand_line in demands_lines:
            demand_info = demand_line.split(',')
            source = demand_info[0]
            dest = demand_info[1]
            traffic = int(demand_info[2])
            name = demand_info[3] 
            if name == '':
                demand_name = 'none'
            else: 
                demand_name = name 
            model.add_demand(source, dest, traffic, demand_name)
            
        return model
    
    def get_demand_objects_source_node(self, source_node_name):
        """Returns list of demand objects originating at the source node"""
        demand_list = []
        for demand in (demand for demand in self.demand_objects):
            if demand.source_node_object.name == source_node_name:
                demand_list.append(demand)
        
        return demand_list

    def get_demand_objects_dest_node(self, dest_node_name):
        """Returns list of demands objects originating at the 
        destination node """
        demand_list = []
        for demand in (demand for demand in self.demand_objects):
            if demand.dest_node_object.name == dest_node_name:
                demand_list.append(demand)
        
        return demand_list        
