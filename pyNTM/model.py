"""A class that defines the network being modeled and that contains all
modeled objects in the network such as Nodes, Interfaces, Circuits,
and Demands."""

from pprint import pprint

import networkx as nx

from .circuit import Circuit
from .demand import Demand
from .interface import Interface
from .exceptions import ModelException
from .utilities import find_end_index
from .node import Node
from .rsvp import RSVP_LSP


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

        - RSVP LSP objects: RSVP LSPs

    """

    def __init__(self, interface_objects=set(), node_objects=set(),
                 demand_objects=set(), rsvp_lsp_objects=set()):
        self.interface_objects = interface_objects
        self.node_objects = node_objects
        self.demand_objects = demand_objects
        self.circuit_objects = set([])
        self.rsvp_lsp_objects = rsvp_lsp_objects

    def __repr__(self):
        return 'Model(Interfaces: %s, Nodes: %s, Demands: %s, RSVP_LSPs: %s)' % (len(self.interface_objects),
                                                                                 len(self.node_objects),
                                                                                 len(self.demand_objects),
                                                                                 len(self.rsvp_lsp_objects))

    def add_network_interfaces_from_list(self, network_interfaces):
        """
        A tool that reads network interface info and updates an *existing* model.
        Intended to be used from CLI/interactive environment
        Interface info must be a list of dicts and in format like below example:

        network_interfaces = [
        {'name':'A-to-B', 'cost':4,'capacity':100, 'node':'A',
         'remote_node': 'B', 'address': 1, 'failed': False},
        {'name':'A-to-Bv2', 'cost':40,'capacity':150, 'node':'A',
         'remote_node': 'B', 'address': 2, 'failed': False},
        {'name':'A-to-C', 'cost':1,'capacity':200, 'node':'A',
         'remote_node': 'C', 'address': 3, 'failed': False},]
        """
        # TODO - look at removing requirement that address be specified
        new_interface_objects, new_node_objects = \
            self._make_network_interfaces(network_interfaces)
        self.node_objects = self.node_objects.union(new_node_objects)
        self.interface_objects = \
            self.interface_objects.union(new_interface_objects)
        self.validate_model()

    def validate_model(self):
        """
        Validates that data fed into the model creates a valid network model
        """

        # create circuits table, flags ints that are not part of a circuit
        circuits = self._make_circuits(return_exception=True)

        error_data = []  # list of all errored checks

        int_res_bw_too_high = set([])
        int_res_bw_sum_error = set([])

        for interface in (interface for interface in self.interface_objects):
            if interface.reserved_bandwidth > interface.capacity:
                int_res_bw_too_high.add(interface)
            if (round(interface.reserved_bandwidth, 1) !=
                    round(sum([lsp.reserved_bandwidth for lsp in interface.lsps(self)]), 1)):
                int_res_bw_sum_error.add((interface, interface.reserved_bandwidth, tuple(interface.lsps(self))))

        # If creation of circuits returns a dict, there are problems
        if isinstance(circuits, dict):
            error_data.append({'ints_w_no_remote_int': circuits['data']})

        # Append any failed checks to error_data
        if len(int_res_bw_too_high) > 0:
            error_data.append({'int_res_bw_too_high': int_res_bw_too_high})

        if len(int_res_bw_sum_error) > 0:
            error_data.append({'int_res_bw_sum_error': int_res_bw_sum_error})

        # Validate there are no duplicate interfaces
        unique_interfaces_per_node = self._unique_interface_per_node()

        # Log any duplicate interfaces on a node
        if not unique_interfaces_per_node:
            error_data.append(unique_interfaces_per_node)

        # Make validate_model() check for matching failed statuses
        # on the interfaces and matching interface capacity
        circuits_with_mismatched_interface_capacity = []
        for ckt in (ckt for ckt in self.circuit_objects):
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
            int_status_error_dict = {
                'circuits_with_mismatched_interface_capacity':
                circuits_with_mismatched_interface_capacity
            }
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
            pprint(message)
            pprint(error_data)
            raise ModelException((message, error_data))
        else:
            return self

    def _demand_traffic_per_int(self, demand):
        """
        Given a Demand object, return key, value pairs for how much traffic each
        interface gets from the routing of the traffic load over Model interfaces.

        : demand: Demand object
        : return: dict of ('source_node_name-dest_node_name': <traffic from demand> ) k, v pairs

        Example: The interface from node G to node D below has 2.5 units of traffic from 'demand';
                 the interface from A to B has 10.0, etc.
        {'G-D': 2.5, 'A-B': 10.0, 'B-D': 2.5, 'A-D': 5.0, 'D-F': 10.0, 'B-G': 2.5}

        """

        # Find node names
        source_node_name = demand.source_node_object.name
        dest_node_name = demand.dest_node_object.name

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph(include_failed_circuits=False)

        # Get networkx shortest paths from source_node to dest_node
        shortest_paths = nx.all_shortest_paths(G, source_node_name,
                                               dest_node_name, weight='cost')

        # Create shortest path list showing node to node connections
        shortest_path_list = []
        for path in shortest_paths:
            int_path = []
            for x in range(0, len(path) - 1):
                int_path.append(path[x] + '-' + path[x + 1])
            shortest_path_list.append(int_path)

        # All interfaces in shortest_path_list
        shortest_path_int_list = []
        for path in shortest_path_list:
            shortest_path_int_list += path

        # Unique interfaces across all shortest paths
        shortest_path_int_set = set(shortest_path_int_list)

        # Dict to store how many unique next hops each node has in the shortest paths
        unique_next_hops = {}
        for interface in shortest_path_int_set:
            unique_next_hops[interface[0]] = [intf for intf in shortest_path_int_set if
                                              intf[0] == interface[0]]

        # shortest_path_info will be a dict with the following info for each path:
        # - an ordered list of interfaces in the path
        # - a dict of cumulative splits for each interface at that point in the path
        # - the amount of traffic on the path
        # Example:
        # shortest_path_info =
        # {'path_0': {'interfaces': ['E-A', 'A-D', 'D-F'],
        #            'path_traffic': 20.0,
        #            'splits': {'A-D': 2, 'D-F': 2, 'E-A': 1}},
        # 'path_1': {'interfaces': ['E-A', 'A-B', 'B-D', 'D-F'],
        #            'path_traffic': 10.0,
        #            'splits': {'A-B': 2, 'B-D': 4, 'D-F': 4, 'E-A': 1}},
        # 'path_2': {'interfaces': ['E-A', 'A-B', 'B-G', 'G-D', 'D-F'],
        #            'path_traffic': 10.0,
        #            'splits': {'A-B': 2, 'B-G': 4, 'D-F': 4, 'E-A': 1, 'G-D': 4}}}

        shortest_path_info = {}
        path_counter = 0
        for path in shortest_path_list:
            traffic_splits_per_interface = {}  # Dict of cumulative splits per interface

            path_key = 'path_' + str(path_counter)

            shortest_path_info[path_key] = {}

            # Create interfaces list
            interfaces_list = path

            # Create cumulative path splits for each interface
            total_splits = 1
            for interface in path:
                total_splits = total_splits * len(unique_next_hops[interface[0]])
                traffic_splits_per_interface[interface] = total_splits

            # Find path traffic
            max_split = max([split for split in traffic_splits_per_interface.values()])
            path_traffic = float(demand.traffic) / float(max_split)

            shortest_path_info[path_key]['interfaces'] = interfaces_list
            shortest_path_info[path_key]['splits'] = traffic_splits_per_interface
            shortest_path_info[path_key]['path_traffic'] = path_traffic
            path_counter += 1

        # For each path, determine which interfaces it transits and add
        # that path's traffic to the interface

        # Create dict to hold cumulative traffic for each interface for demand
        traff_per_int = dict.fromkeys(shortest_path_int_set, 0)
        for path, info in shortest_path_info.items():
            for interface in info['interfaces']:
                traff_per_int[interface] += info['path_traffic']

        return traff_per_int

    def _update_interface_utilization(self):  #
        """Updates each interface's utilization; returns Model object with
        updated interface utilization."""

        # In the model, in an interface is failed, set the traffic attribute
        # to 'Down', otherwise, initialize the traffic to zero
        for interface_object in self.interface_objects:
            if interface_object.failed:
                interface_object.traffic = 'Down'
            else:
                interface_object.traffic = 0.0

        routed_demand_object_generator = (demand_object for demand_object in self.demand_objects if
                                          'Unrouted' not in demand_object.path)

        # For each demand that is not Unrouted, add its traffic value to each
        # interface object in the path
        for demand_object in routed_demand_object_generator:
            # This model only allows demands to take RSVP LSPs if
            # the demand's source/dest nodes match the LSP's source/dest nodes.

            # Expand each LSP into its interfaces and add that the traffic per LSP
            # to the LSP's path interfaces.

            # Can demand take LSP?

            routed_lsp_generator = (lsp for lsp in self.rsvp_lsp_objects if 'Unrouted' not in lsp.path)
            lsps_for_demand = []
            for lsp in routed_lsp_generator:
                if (lsp.source_node_object == demand_object.source_node_object and
                        lsp.dest_node_object == demand_object.dest_node_object):
                    lsps_for_demand.append(lsp)

            if lsps_for_demand != []:
                # Find each demands path list, determine the ECMP split across the
                # routed LSPs, and find the traffic per path (LSP)
                num_routed_lsps_for_demand = len(lsps_for_demand)

                traffic_per_demand_path = demand_object.traffic / num_routed_lsps_for_demand

                # Get the interfaces for each LSP in the demand's path
                for lsp in lsps_for_demand:

                    lsp_path_interfaces = lsp.path['interfaces']

                    # Now that all interfaces are known,
                    # update traffic on interfaces demand touches
                    for interface in lsp_path_interfaces:
                        # Get the interface's existing traffic and add the
                        # portion of the demand's traffic
                        interface.traffic += traffic_per_demand_path

            # If demand_object is not taking LSPs, IGP route it, using hop by hop ECMP
            else:
                # demand_traffic_per_int will be dict of
                # ('source_node_name-dest_node_name': <traffic from demand>) k,v pairs
                #
                # Example: The interface from node G to node D has 2.5 units of traffic from 'demand'
                # {'G-D': 2.5, 'A-B': 10.0, 'B-D': 2.5, 'A-D': 5.0, 'D-F': 10.0, 'B-G': 2.5}
                demand_traffic_per_int = self._demand_traffic_per_int(demand_object)

                # Get the interface objects and update them with the traffic
                for interface, traffic_from_demand in demand_traffic_per_int.items():
                    from_node = interface.split('-')[0]
                    to_node = interface.split('-')[1]
                    interface_to_update = self.get_interface_object_from_nodes(from_node, to_node)
                    interface_to_update.traffic += traffic_from_demand

        return self

    def _route_demands(self, demands, input_model):
        """
        Routes demands through input_model Model object
        :param demands: iterable of Demand objects to be routed
        :param input_model:  Model object in which to route the demands
        :return:
        """
        for demand_object in demands:
            demand_object = demand_object._add_demand_path(input_model)

        return self._update_interface_utilization()

    def _route_lsps(self, input_model):
        """Route the LSPs in the model
        1.  Get LSPs into groups with matching source/dest

        2.  Find all the demands that take the LSP group

        3.  Route the LSP group, one at a time

        :param input_model: Model object; this may have different parameters than 'self'
        :return: self, with updated LSP paths
        """

        # Find parallel LSP groups
        parallel_lsp_groups = self.parallel_lsp_groups()

        # Find all the parallel demand groups
        parallel_demand_groups = self.parallel_demand_groups()

        # Find the amount of bandwidth each LSP in each parallel group will carry
        counter = 1
        for group, lsps in parallel_lsp_groups.items():
            print("Routing {} LSPs in parallel LSP group {}; {}/{}".format(len(lsps), group, counter,
                                                                           len(parallel_lsp_groups)))
            # Traffic each LSP in a parallel LSP group will carry; initialize
            traff_on_each_group_lsp = 0

            try:
                # Get all demands that would ride the parallel LSP group
                dmds_on_lsp_group = parallel_demand_groups[group]

                traffic_in_demand_group = sum([dmd.traffic for dmd in dmds_on_lsp_group])
                if traffic_in_demand_group > 0:
                    traff_on_each_group_lsp = traffic_in_demand_group / len(lsps)
            except KeyError:
                # LSPs with no demands will cause a KeyError in parallel_demand_groups[group]
                # since parallel_demand_group will have no entry for 'group'
                pass

            # Now route each LSP in the group (first routing iteration)
            for lsp in lsps:
                # Route each LSP one at a time
                lsp.route_lsp(input_model, traff_on_each_group_lsp)

            routed_lsps_in_group = [lsp for lsp in lsps if lsp.path != 'Unrouted']

            # ##### Optimize the LSP group reserved bandwidth #####
            # If not all the LSPs in the group can route at the lowest (initial)
            # setup bandwidth, determine which LSPs can signal and for how much traffic
            if len(routed_lsps_in_group) != len(lsps) and len(routed_lsps_in_group) > 0:
                self._optimize_parallel_lsp_group_res_bw(input_model, routed_lsps_in_group, traffic_in_demand_group)

            counter += 1

        return self

    def _optimize_parallel_lsp_group_res_bw(self, input_model, routed_lsps_in_group, traffic_in_demand_group):
        """
        If not all LSPs in a parallel LSP group can route, some of the LSPs that did
        route may be able to signal for their setup_bandwidth.

        :param input_model: Model object containing the parallel LSP group
        :param routed_lsps_in_group: LSPs in parallel LSP group with a path
        :param traffic_in_demand_group: aggregate traffic for all demands with
               the same source node and destination node as the parallel LSP group
        :return:
        """
        # This value would be the optimal setup bandwidth for each LSP
        # as it would allow the LSP to reserve bandwidth for the amount
        # of traffic it carries
        setup_bandwidth_optimized = traffic_in_demand_group / len(routed_lsps_in_group)
        # Determine if any of the LSPs can signal for the amount of
        # traffic they would carry (setup_bandwidth_optimized)
        for lsp in routed_lsps_in_group:
            # traffic_in_demand_group will ECMP split over routed_lsps_in_group
            # For each lsp in routed_lsp_group, see if it can signal for
            # a setup_bandwidth_optimized setup_bandwidth

            lsp_path_interfaces_before = lsp.path['interfaces']
            lsp_res_bw_before = lsp.reserved_bandwidth

            # See if LSP can resignal for setup_bandwidth_optimized
            lsp = lsp.find_rsvp_path_w_bw(setup_bandwidth_optimized, input_model)

            # If the LSP reserved_bandwidth changes, restore the old
            # reserved_bandwidth value to the interfaces in its
            # prior path['interfaces'] list
            if lsp_res_bw_before != lsp.reserved_bandwidth:
                for interface in lsp_path_interfaces_before:
                    interface.reserved_bandwidth -= lsp_res_bw_before
                # . . . and then remove the new reserved bandwidth from the
                # new path interfaces
                for interface in lsp.path['interfaces']:
                    interface.reserved_bandwidth += lsp.reserved_bandwidth

    def parallel_lsp_groups(self):
        """
        Determine LSPs with same source and dest nodes
        :return: dict with entries where key is 'source_node_name-dest_node_name' and value is a list of LSPs
                 with matching source/dest nodes
        """

        src_node_names = set([lsp.source_node_object.name for lsp in self.rsvp_lsp_objects])
        dest_node_names = set([lsp.dest_node_object.name for lsp in self.rsvp_lsp_objects])

        parallel_lsp_groups = {}

        for src_node_name in src_node_names:
            for dest_node_name in dest_node_names:
                key = '{}-{}'.format(src_node_name, dest_node_name)
                parallel_lsp_groups[key] = []
                for lsp in self.rsvp_lsp_objects:
                    if (lsp.source_node_object.name == src_node_name and
                            lsp.dest_node_object.name == dest_node_name):
                        parallel_lsp_groups[key].append(lsp)

                if parallel_lsp_groups[key] == []:
                    del parallel_lsp_groups[key]

        return parallel_lsp_groups

    def parallel_demand_groups(self):
        """
        Determine demands with same source and dest nodes
        :return: dict with entries where key is 'source_node_name-dest_node_name' and value is a list of demands
                 with matching source/dest nodes
        """

        src_node_names = set([dmd.source_node_object.name for dmd in self.demand_objects])
        dest_node_names = set([dmd.dest_node_object.name for dmd in self.demand_objects])

        parallel_demand_groups = {}

        for src_node_name in src_node_names:
            for dest_node_name in dest_node_names:
                key = '{}-{}'.format(src_node_name, dest_node_name)
                parallel_demand_groups[key] = []
                for dmd in self.demand_objects:
                    if (dmd.source_node_object.name == src_node_name and
                            dmd.dest_node_object.name == dest_node_name):
                        parallel_demand_groups[key].append(dmd)

                if parallel_demand_groups[key] == []:
                    del parallel_demand_groups[key]

        return parallel_demand_groups

    def update_simulation(self):
        """
        Updates the simulation state; this needs to be run any time there is
        a change to the state of the Model, such as failing an interface, adding
        a Demand, adding/removing and LSP, etc.

        This call does not carry forward any state from the previous simulation
        results.
        """

        # This set of interfaces can be used to route traffic
        non_failed_interfaces = set()
        # This set of nodes can be used to route traffic
        available_nodes = set()

        # Find all the non-failed interfaces in the model and
        # add them to non_failed_interfaces.
        # If the interface is not failed, then by definition, the nodes are
        # not failed
        for interface_object in (interface_object for interface_object in self.interface_objects
                                 if interface_object.failed is not True):
            non_failed_interfaces.add(interface_object)
            available_nodes.add(interface_object.node_object)
            available_nodes.add(interface_object.remote_node_object)

        # Create a model consisting only of the non-failed interfaces and
        # corresponding non-failed (available) nodes
        non_failed_interfaces_model = Model(non_failed_interfaces,
                                            available_nodes, self.demand_objects,
                                            self.rsvp_lsp_objects)

        # Reset the reserved_bandwidth, traffic on each interface
        for interface in (interface for interface in self.interface_objects):
            interface.reserved_bandwidth = 0
            interface.traffic = 0

        for lsp in (lsp for lsp in self.rsvp_lsp_objects):
            lsp.path = 'Unrouted'

        for demand in (demand for demand in self.demand_objects):
            demand.path = 'Unrouted'

        print("Routing the LSPs . . . ")
        # Route the RSVP LSPs
        self = self._route_lsps(non_failed_interfaces_model)
        print("LSPs routed; routing demands now . . .")
        # Route the demands
        self = self._route_demands(self.demand_objects,
                                   non_failed_interfaces_model)
        print("Demands routed; validating model . . . ")

        self.validate_model()

    def _unique_interface_per_node(self):
        """
        Checks that the interface names on each node are unique; returns
        a message if a duplicate interface name is found on the same node
        """

        exception_interfaces = set()  # duplicate interfaces

        for node in (node for node in self.node_objects):
            node_int_list = [interface.name for interface in node.interfaces(self)]
            node_int_set = set(node_int_list)

            if len(node_int_list) > len(node_int_set):
                # Find which ints are duplicate
                for item in node_int_set:
                    node_int_list.remove(item)
                # Add the remaining node and interface name to exception_interfaces
                for item in node_int_list:
                    exception_interfaces.add((node, item))

        if len(exception_interfaces) > 0:
            message = ("Interface names must be unique per node.  The following"
                       " nodes have duplicate interface names {}".format(exception_interfaces))
            raise ModelException(message)
        else:
            return True

    def _make_circuits(self, return_exception=True,
                       include_failed_circuits=True):
        """
        Matches interface objects into circuits and returns the circuits list
        :param return_exception: Should an exception be returned if not all the
                                 interfaces can be matched into a circuit?
        :param include_failed_circuits:  Should circuits that will be in a
                                         failed state be created?

        :return: a set of Circuit objects in the Model, each Circuit
                 comprised of two Interface objects
        """

        G = self._make_weighted_network_graph(include_failed_circuits=include_failed_circuits)

        # Determine which interfaces pair up into good circuits in G
        paired_interfaces = ((local_node_name, remote_node_name, data) for
                             (local_node_name, remote_node_name, data) in
                             G.edges(data=True) if G.has_edge(remote_node_name,
                                                              local_node_name))

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

            if int1.in_ckt is False and int2.in_ckt is False:
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
        exception_ints_not_in_ckt = [(local_node_name, remote_node_name, data)
                                     for (local_node_name, remote_node_name, data) in
                                     G.edges(data=True) if not (G.has_edge(remote_node_name, local_node_name))]

        if len(exception_ints_not_in_ckt) > 0:
            exception_msg = ('WARNING: These interfaces were not matched '
                             'into a circuit {}'.format(exception_ints_not_in_ckt))
            if return_exception:
                raise ModelException(exception_msg)
            else:
                return {'data': exception_ints_not_in_ckt}

        self.circuit_objects = circuits

    def get_interface_object_from_nodes(self, local_node_name, remote_node_name):
        """Returns an Interface object with the specified local and
        remote node names """
        for interface in (interface for interface in self.interface_objects):
            if interface.node_object.name == local_node_name and \
                    interface.remote_node_object.name == remote_node_name:
                return interface

    @property
    def all_interface_addresses(self):
        """
        Returns all interface addresses
        """
        return set(interface.address for interface in self.interface_objects)

    def add_circuit(self, node_a_object, node_b_object, node_a_interface_name,
                    node_b_interface_name, cost_intf_a=1, cost_intf_b=1,
                    capacity=1000, failed=False, address=None):
        """
        Creates component Interface objects for a new Circuit in the Model.
        The Circuit object will then be created during the validate_model() call.

        :param node_a_object: Node object
        :param node_b_object: Node object
        :param node_a_interface_name: name of component Interface on node_a
        :param node_b_interface_name: name of component Interface on node_b
        :param cost_intf_a: metric/cost of node_a_interface component Interface
        :param cost_intf_b: metric/cost of node_b_interface component Interface
        :param capacity: Circuit's capacity
        :param failed: Should the Circuit be created in a Failed state?
        :param address: Optional.  Will be auto-assigned unless specified
        :return: Model with new Circuit comprised of 2 new Interfaces
        """

        if address is None:
            addresses = self.all_interface_addresses
            if len(addresses) == 0:
                address = 1
            else:
                address = max(addresses) + 1

        int_a = Interface(node_a_interface_name, cost_intf_a, capacity,
                          node_a_object, node_b_object, address)
        int_b = Interface(node_b_interface_name, cost_intf_b, capacity,
                          node_b_object, node_a_object, address)

        existing_int_keys = set([interface._key for interface in self.interface_objects])
        if int_a._key in existing_int_keys:
            raise ModelException("interface {} on node {} already exists in model".format(int_a, node_a_object))
        if int_b._key in existing_int_keys:
            raise ModelException("interface {} on node {} already exists in model".format(int_b, node_b_object))

        self.interface_objects.add(int_a)
        self.interface_objects.add(int_b)

        self.validate_model()

    def is_node_an_orphan(self, node_object):
        """Determines if a node is in orphan_nodes"""
        if node_object in self.get_orphan_node_objects():
            return True
        else:
            return False

    def get_orphan_node_objects(self):
        """
        Returns list of Nodes that have no interfaces
        """
        orphan_nodes = [node for node in self.node_objects if len(node.interfaces(self)) == 0]

        return orphan_nodes

    def add_node(self, node_object):
        """
        Adds a node object to the model object
        """

        if node_object.name in (node.name for node in self.node_objects):
            message = "A node with name {} already exists in the model".format(node_object.name)
            raise ModelException(message)
        else:
            self.node_objects.add(node_object)

        self.validate_model()

    def get_node_object(self, node_name):
        """
        Returns a Node object, given a node's name
        """
        matching_node = [node for node in self.node_objects if node.name == node_name]

        if len(matching_node) > 0:
            return matching_node[0]
        else:
            message = "No node with name %s exists in the model" % node_name
            raise ModelException(message)

    def _make_network_interfaces(self, interface_info_list):
        """
        Returns set of Interface objects and a set of Node objects for Nodes
        that are not already in the Model.

        :param interface_info_list: list of dicts with interface specs;
        :return: Set of Interface objects and set of Node objects for the
                 new Interfaces for Nodes that are not already in the model
        """
        network_interface_objects = set([])
        network_node_objects = set([])

        # Create the Interface objects
        for interface in interface_info_list:
            intf = Interface(interface['name'], interface['cost'],
                             interface['capacity'], Node(interface['node']),
                             Node(interface['remote_node']),
                             interface['address'])
            network_interface_objects.add(intf)

            # Check to see if the Interface's Node already exists, if not, add it
            node_names = ([node.name for node in self.node_objects])
            if interface['node'] not in node_names:
                network_node_objects.add(Node(interface['node']))
            if interface['remote_node'] not in node_names:
                network_node_objects.add(Node(interface['remote_node']))

        return (network_interface_objects, network_node_objects)

    def add_demand(self, source_node_name, dest_node_name, traffic=0,
                   name='none'):
        """
        Adds a traffic load (Demand) from point A to point B in the
        model and validates model.
        :param source_node_name: name of Demand's source Node
        :param dest_node_name: name of Demand's destination Node
        :param traffic: amount of traffic (magnitude) of the Demand
        :param name: Demand name
        :return: A validated Model object with the new demand
        """
        source_node_object = self.get_node_object(source_node_name)
        dest_node_object = self.get_node_object(dest_node_name)
        added_demand = Demand(source_node_object, dest_node_object,
                              traffic, name)
        if added_demand._key in set([demand._key for demand in self.demand_objects]):
            message = '{} already exists in demand_objects'.format(added_demand)
            raise ModelException(message)
        self.demand_objects.add(added_demand)

        self.validate_model()

    def add_rsvp_lsp(self, source_node_name, dest_node_name, name):
        """
        Adds an RSVP LSP with name from the source node to the
        dest node and validates model.
        :param source_node_name: LSP source Node name
        :param dest_node_name: LSP destination Node name
        :param name: name of LSP
        :return: A validated Model with the new RSVP_LSP object
        """
        source_node_object = self.get_node_object(source_node_name)
        dest_node_object = self.get_node_object(dest_node_name)
        added_lsp = RSVP_LSP(source_node_object, dest_node_object, name)

        if added_lsp._key in set([lsp._key for lsp in self.rsvp_lsp_objects]):
            message = '{} already exists in rsvp_lsp_objects'.format(added_lsp)
            raise ModelException(message)
        self.rsvp_lsp_objects.add(added_lsp)

        self.validate_model()

    def get_demand_object(self, source_node_name, dest_node_name, demand_name='none'):
        """
        Returns demand specified by the source_node_name, dest_node_name, name;
        throws exception if demand not found
        """
        model_demand_iterator = (demand for demand in self.demand_objects)

        demand_to_return = None

        for demand in model_demand_iterator:
            if demand.source_node_object.name == source_node_name and \
                    demand.dest_node_object.name == dest_node_name and \
                    demand.name == demand_name:
                demand_to_return = demand
                return demand_to_return

        if demand_to_return is None:
            raise ModelException('no matching demand')

    def get_rsvp_lsp(self, source_node_name, dest_node_name, lsp_name='none'):
        """Returns the RSVP LSP from the model with the specified source node
        name, dest node name, and LSP name."""

        needed_key = (source_node_name, dest_node_name, lsp_name)

        if needed_key not in (lsp._key for lsp in self.rsvp_lsp_objects):
            msg = ("LSP with source node %s, dest node %s, and name %s "
                   "does not exist in model" % (source_node_name, dest_node_name, lsp_name))
            raise ModelException(msg)
        else:
            for lsp in (lsp for lsp in self.rsvp_lsp_objects):
                if lsp._key == needed_key:
                    return lsp

    # Interface calls
    def get_interface_object(self, interface_name, node_name):
        """Returns an interface object for specified node name and interface name"""

        self._does_interface_exist(interface_name, node_name)

        node_object = self.get_node_object(node_name)

        int_object = [interface for interface in node_object.interfaces(self) if interface.name == interface_name]
        return int_object[0]

    def _does_interface_exist(self, interface_name, node_object_name):
        int_key = (interface_name, node_object_name)
        interface_key_iterator = (interface._key for interface in
                                  self.interface_objects)

        if int_key not in (interface_key_iterator):
            raise ModelException('specified interface does not exist')

    def get_circuit_object_from_interface(self, interface_name, node_name):
        """
        Returns a Circuit object, given a Node name and Interface name
        """

        # Does interface exist?
        self._does_interface_exist(interface_name, node_name)

        interface = self.get_interface_object(interface_name, node_name)

        ckts = [ckt for ckt in self.circuit_objects if interface in (ckt.interface_a, ckt.interface_b)]

        return ckts[0]

    # Convenience calls #####
    def get_failed_interface_objects(self):
        """
        Returns a list of all failed interfaces in the Model
        """
        failed_interfaces = []

        for interface in (interface for interface in self.interface_objects):
            if interface.failed:
                failed_interfaces.append(interface)

        return failed_interfaces

    def get_unfailed_interface_objects(self):
        """
        Returns a list of all non-failed interfaces in the Model
        """

        unfailed_interface_objects = set()

        interface_iter = (interface for interface in self.interface_objects)

        for interface in interface_iter:
            if not interface.failed:
                unfailed_interface_objects.add(interface)

        return unfailed_interface_objects

    def get_unrouted_demand_objects(self):
        """
        Returns list of demand objects that cannot be routed
        """
        unrouted_demands = []
        for demand in (demand for demand in self.demand_objects):
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
        """Fails the Interface object for the interface_name/node_name pair"""

        # Get the interface object
        interface_object = self.get_interface_object(interface_name, node_name)

        # Does interface exist?
        if interface_object not in self.interface_objects:
            ModelException('specified interface does not exist')

        # find the remote interface
        remote_interface_object = interface_object.get_remote_interface(self)

        remote_interface_object.failed = True
        interface_object.failed = True

    def unfail_interface(self, interface_name, node_name, raise_exception=False):
        """
        Unfails the Interface object for the interface_name, node_name pair.

        :param interface_name:
        :param node_name:
        :param raise_exception: If raise_excecption=True, an exception
                                will be raised if the interface cannot be unfailed.
                                An example of this would be if you tried to unfail
                                the interface when the parent node or remote node
                                was in a failed state
        :return: Interface object from Model that is not failed
        """

        if not (isinstance(raise_exception, bool)):
            message = "raise_exception must be boolean value"
            raise ModelException(message)

        # Get the interface object
        interface_object = self.get_interface_object(interface_name, node_name)

        # Does interface exist?
        if interface_object not in set(self.interface_objects):
            ModelException('specified interface does not exist')

        # Find the remote interface
        remote_interface = interface_object.get_remote_interface(self)

        # Ensure local and remote nodes are failed == False and set reservable
        # bandwidth on each interface to interface.capacity
        if self.get_node_object(interface_object.node_object.name).failed is False and \
                self.get_node_object(remote_interface.node_object.name).failed is False:

            remote_interface.failed = False
            remote_interface.reserved_bandwidth = 0
            interface_object.failed = False
            interface_object.reserved_bandwidth = 0
            self.validate_model()
        else:
            if raise_exception:
                message = ("Local and/or remote node are failed; cannot have "
                           "unfailed interface on failed node.")
                raise ModelException(message)

    def get_all_paths_reservable_bw(self, source_node_name, dest_node_name, include_failed_circuits=True,
                                    cutoff=10, needed_bw=0):
        """
        For a source and dest node name pair, find all simple path(s) with at
        least needed_bw reservable bandwidth available less than or equal to
        cutoff hops long.

        The amount of simple paths (paths that don't have repeating nodes) can
        be very large for larger topologies and so this call can be very expensive.
        Use the cutoff argument to limit the path length to consider to cut down on
        the time it takes to run this call.

        :param source_node_name: name of source node in path
        :param dest_node_name: name of destination node in path
        :param include_failed_circuits: include failed circuits in the topology
        :param needed_bw: the amount of reservable bandwidth required on the path
        :param cutoff: max amount of path hops
        :return: Return the shortest path in dictionary form:
                 shortest_path = {'path': [list of shortest path routes],
                                  'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph(include_failed_circuits=include_failed_circuits, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = dict()
        converted_path['path'] = []

        # Find the simple paths in G between source and dest
        digraph_shortest_paths = nx.all_simple_paths(G, source_node_name, dest_node_name, cutoff=cutoff)

        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path)
                converted_path['path'].append(model_path)

            return converted_path
        except BaseException:
            return converted_path

    def get_shortest_path(self, source_node_name, dest_node_name, needed_bw=0):
        """
        For a source and dest node name pair, find the shortest path(s) with at
        least needed_bw available.

        :param source_node_name: name of source node in path
        :param dest_node_name: name of destination node in path
        :param needed_bw: the amount of reservable bandwidth required on the path
        :return: Return the shortest path in dictionary form:
                 shortest_path = {'path': [list of shortest path routes],
                                  'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph(include_failed_circuits=False, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = dict()
        converted_path['path'] = []
        converted_path['cost'] = None

        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(G, source_node_name,
                                                       dest_node_name,
                                                       weight='cost')

        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path)
                converted_path['path'].append(model_path)
                converted_path['cost'] = nx.shortest_path_length(G, source_node_name,
                                                                 dest_node_name, weight='cost')
            return converted_path
        except BaseException:
            return converted_path

    def get_shortest_path_for_routed_lsp(self, source_node_name, dest_node_name, lsp, needed_bw):
        """
        For a source and dest node name pair, find the shortest path(s) with at
        least needed_bw available for an LSP that is already routed.
        Return the shortest path in dictionary form:
        shortest_path = {'path': [list of shortest path routes],
                            'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph_routed_lsp(lsp, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = dict()
        converted_path['path'] = []
        converted_path['cost'] = None

        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(G, source_node_name,
                                                       dest_node_name,
                                                       weight='cost')
        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path)
                converted_path['path'].append(model_path)
                converted_path['cost'] = nx.shortest_path_length(G, source_node_name,
                                                                 dest_node_name, weight='cost')
            return converted_path
        except BaseException:
            return converted_path

    def _convert_nx_path_to_model_path(self, nx_graph_path):
        """Given a path from an networkx DiGraph, converts that
        path to a Model style path and returns that Model style path

        A networkx path is a list of nodes in order of transit.
        ex: ['A', 'B', 'G', 'D', 'F']

        The corresponding model style path would be:
        [Interface(name = 'A-to-B', cost = 20, capacity = 125, node_object = Node('A'),
            remote_node_object = Node('B'), address = 9),
        Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
            remote_node_object = Node('G'), address = 6),
        Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
            remote_node_object = Node('D'), address = 2),
        Interface(name = 'D-to-F', cost = 10, capacity = 300, node_object = Node('D'),
            remote_node_object = Node('F'), address = 1)]
        """

        # Define a model-style path to build
        model_path = []
        # look at each hop in the path
        for hop in nx_graph_path:
            current_hop_index = nx_graph_path.index(hop)
            next_hop_index = current_hop_index + 1
            if next_hop_index < len(nx_graph_path):
                next_hop = nx_graph_path[next_hop_index]
                interface = self.get_interface_object_from_nodes(hop, next_hop)
                model_path.append(interface)

        return model_path

    # NODE CALLS ######
    def get_node_interfaces(self, node_name):
        """Returns list of interfaces on specified node name"""
        return Node(node_name).interfaces(self)

    def fail_node(self, node_name):
        """Fails specified node"""

        # Find node's interfaces and fail them
        ints_to_fail_iterator = (interface for interface in
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
        ints_to_unfail_iterator = (interface for interface in
                                   self.get_node_interfaces(node_name))

        # Find node's interfaces and unfail them
        ints_to_unfail_iterator = (interface for interface in self.get_node_interfaces(node_name))

        for interface in ints_to_unfail_iterator:

            # Unfail the interfaces if the remote node is not failed
            if not interface.remote_node_object.failed:
                # Unfail the specific interface
                self.unfail_interface(interface.name, node_name, False)

                # Unfail the remote interface
                remote_int = interface.get_remote_interface(self)
                self.unfail_interface(remote_int.name,
                                      remote_int.node_object.name, False)

    def get_failed_node_objects(self):
        """
        Returns a list of all failed nodes
        """
        failed_nodes = []

        for node in (node for node in self.node_objects):
            if node.failed:
                node_object = self.get_node_object(node.name)
                failed_nodes.append(node_object)

        return failed_nodes

    def get_non_failed_node_objects(self):
        """Returns a list of all failed nodes"""
        non_failed_nodes = []

        for node in (node for node in self.node_objects):
            if not node.failed:
                node_object = self.get_node_object(node.name)
                non_failed_nodes.append(node_object)

        return non_failed_nodes

    # Display calls #########
    def display_interface_status(self):
        """Returns failed = True/False for each interface"""

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12), end=' ')
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
        """
        A human-readable(-ish) display of interfaces and traffic on each
        """

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12), 'Traffic'.ljust(12))

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12),
              'Traffic'.ljust(12))

        interface_iterator = (interface for interface in self.interface_objects)

        for interface in interface_iterator:
            print(interface.node_object.name.ljust(12), interface.name.ljust(12), end=' ')
            print(interface.remote_node_object.name.ljust(12), end=' ')
            print(repr(interface.traffic).ljust(12))

    def display_demand_paths(self):
        """
        Displays each demand and its path(s) across the network
        """

        demand_iter = (demand for demand in self.demand_objects)

        for demand in demand_iter:
            print('demand._key is', demand._key)
            print('Demand has %s paths:' % (len(demand.path)))
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

    def _make_weighted_network_graph(self, include_failed_circuits=True, needed_bw=0):
        """Returns a networkx weighted network directional graph from
        the input Model object"""
        G = nx.DiGraph()

        if not include_failed_circuits:
            # Get non-failed edge names
            edge_names = ((interface.node_object.name,
                           interface.remote_node_object.name, interface.cost)
                          for interface in self.interface_objects
                          if (interface.failed is False and
                              interface.reservable_bandwidth >= needed_bw))
        elif include_failed_circuits:
            # Get all edge names
            edge_names = ((interface.node_object.name,
                           interface.remote_node_object.name, interface.cost)
                          for interface in self.interface_objects if interface.reservable_bandwidth >= needed_bw)

        # Add edges to networkx DiGraph
        G.add_weighted_edges_from(edge_names, weight='cost')

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

        return G

    def _make_weighted_network_graph_routed_lsp(self, lsp, needed_bw=0):
        """
        Returns a networkx weighted network directional graph from the input Model object.
        Considers edges with needed_bw of reservable_bandwidth and also takes into account
        reserved_bandwidth by the lsp on Interfaces in the existing LSP path
        :param self:
        :param include_failed_circuits:
        :param lsp:
        :param needed_bw:
        :return:
        """
        G = nx.DiGraph()

        # The Interfaces that the lsp is routed over currently
        lsp_path_interfaces = lsp.path['interfaces']

        eligible_interface_generator = (interface for interface in self.interface_objects if
                                        interface.failed is False)

        eligible_interfaces = set()

        # Find only the interfaces that are not failed and that have
        # enough reservable_bandwidth
        for interface in eligible_interface_generator:
            # Add back the lsp's reserved bandwidth to Interfaces already in its path
            if interface in lsp_path_interfaces:
                effective_reservable_bw = interface.reservable_bandwidth + lsp.reserved_bandwidth
            else:
                effective_reservable_bw = interface.reservable_bandwidth

            if effective_reservable_bw >= needed_bw:
                eligible_interfaces.add(interface)

        # Get edge names in eligible_interfaces
        edge_names = ((interface.node_object.name,
                       interface.remote_node_object.name, interface.cost)
                      for interface in eligible_interfaces)

        # Add edges to networkx DiGraph
        G.add_weighted_edges_from(edge_names, weight='cost')

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

        return G

    @classmethod
    def load_model_file(cls, data_file):
        """
        Opens a network_modeling data file and returns a model containing
        the info in the data file.  The data file must be of the appropriate
        format to produce a valid model.  This cannot be used to open
        multiple models in a single python instance - there may be
        unpredictable results in the info in the models.
        """

        interface_set = set()
        node_set = set()
        demand_set = set()
        lsp_set = set()

        # Open the file with the data, read it, and split it into lines
        with open(data_file, 'r') as f:
            data = f.read()

        lines = data.splitlines()

        # Define the interfaces info
        int_info_begin_index = 2
        int_info_end_index = find_end_index(int_info_begin_index, lines)
        interface_lines = lines[int_info_begin_index:int_info_end_index]

        # Add the Interfaces to a set
        for interface_line in interface_lines:
            # Read interface characteristics
            if len(interface_line.split()) == 5:
                node_name, remote_node_name, name, cost, capacity = interface_line.split()
            else:
                msg = ("node_name, remote_node_name, name, cost, and capacity "
                       "must be defined for line {}, line index {}".format(interface_line,
                                                                           lines.index(interface_line)))
                raise ModelException(msg)

            new_interface = Interface(name, int(cost), int(capacity), Node(node_name), Node(remote_node_name))

            if new_interface._key not in set([interface._key for interface in interface_set]):
                interface_set.add(new_interface)
            else:
                print("{} already exists in model; disregarding line {}".format(new_interface,
                                                                                lines.index(interface_line)))

            # Derive Nodes from the Interface data
            if node_name not in set([node.name for node in node_set]):
                node_set.add(new_interface.node_object)
            if remote_node_name not in set([node.name for node in node_set]):
                node_set.add(new_interface.remote_node_object)

        # Define the explicit nodes info from the file
        nodes_info_begin_index = int_info_end_index + 3
        nodes_info_end_index = find_end_index(nodes_info_begin_index, lines)
        node_lines = lines[nodes_info_begin_index:nodes_info_end_index]
        for node_line in node_lines:
            node_info = node_line.split()
            node_name = node_info[0]
            try:
                node_lat = int(node_info[2])
            except (ValueError, IndexError):
                node_lat = 0
            try:
                node_lon = int(node_info[1])
            except (ValueError, IndexError):
                node_lon = 0

            new_node = Node(node_name)
            if new_node.name not in set([node.name for node in node_set]):  # Pick up orphan nodes
                node_set.add(new_node)
                new_node.lat = node_lat
                new_node.lon = node_lon
            else:
                print("{} on line {} already exists in model, "
                      "updating lat/lon values if they are specified".format(new_node,
                                                                             lines.index(node_line)))
                existing_node = cls(interface_set, node_set, demand_set, lsp_set).get_node_object(node_name=node_name)
                existing_node.lat = node_lat
                existing_node.lon = node_lon

        # Define the demands info
        demands_info_begin_index = nodes_info_end_index + 3
        demands_info_end_index = find_end_index(demands_info_begin_index, lines)
        # There may or may not be LSPs in the model, so if there are not,
        # set the demands_info_end_index as the last line in the file
        if not demands_info_end_index:
            demands_info_end_index = len(lines)

        demands_lines = lines[demands_info_begin_index:demands_info_end_index]

        for demand_line in demands_lines:
            demand_info = demand_line.split()
            source = demand_info[0]
            source_node = [node for node in node_set if node.name == source][0]
            dest = demand_info[1]
            dest_node = [node for node in node_set if node.name == dest][0]
            traffic = int(demand_info[2])
            name = demand_info[3]
            if name == '':
                demand_name = 'none'
            else:
                demand_name = name

            new_demand = Demand(source_node, dest_node, traffic, demand_name)

            if new_demand._key not in set([dmd._key for dmd in demand_set]):
                demand_set.add(new_demand)
            else:
                print("{} already exists in model; disregarding line {}".format(new_demand,
                                                                                lines.index(demand_line)))

        # Define the LSP info

        # If the demands_info_end_index is the same as the length of the
        # lines list, then there is no LSP section
        if demands_info_end_index != len(lines):
            lsp_info_begin_index = demands_info_end_index + 3
            lsp_lines = lines[lsp_info_begin_index:]

            for lsp_line in lsp_lines:
                lsp_info = lsp_line.split()
                source = lsp_info[0]
                source_node = [node for node in node_set if node.name == source][0]
                dest = lsp_info[1]
                dest_node = [node for node in node_set if node.name == dest][0]
                name = lsp_info[2]
                try:
                    configured_setup_bw = lsp_info[3]
                except IndexError:
                    configured_setup_bw = None
                new_lsp = RSVP_LSP(source_node, dest_node, name, configured_setup_bandwidth=configured_setup_bw)

                if new_lsp._key not in set([lsp._key for lsp in lsp_set]):
                    lsp_set.add(new_lsp)
                else:
                    print("{} already exists in model; disregarding line {}".format(new_lsp,
                                                                                    lines.index(lsp_line)))

        return cls(interface_set, node_set, demand_set, lsp_set)

    def get_demand_objects_source_node(self, source_node_name):
        """
        Returns list of demand objects originating at the source node
        """

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
