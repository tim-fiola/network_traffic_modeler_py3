"""
Parent Class for Model and Parallel_Link_Model objects.

A class that defines the network being modeled and that contains all
modeled objects in the network such as Nodes, Interfaces, Circuits,
and Demands.
"""

from .demand import Demand
from .exceptions import ModelException
from .node import Node
from .rsvp import RSVP_LSP


class MasterModel(object):
    """
    Parent class for Model and Parallel_Link_Model subclasses; holds common defs
    """

    def __init__(self, interface_objects=set(), node_objects=set(),
                 demand_objects=set(), rsvp_lsp_objects=set()):
        self.interface_objects = interface_objects
        self.node_objects = node_objects
        self.demand_objects = demand_objects
        self.circuit_objects = set()
        self.rsvp_lsp_objects = rsvp_lsp_objects
        self.srlg_objects = set()
        self._parallel_lsp_groups = {}

    def simulation_diagnostics(self):  # TODO - make unit test for this
        """
        Analyzes simulation results and looks for the following:
        - Number of routed LSPs carrying Demands
        - Number of routed LSPs with no Demands
        - Number of Demands riding LSPs
        - Number of Demands not riding LSPs
        - Number of unrouted LSPs
        - Number of unrouted Demands

        :return: dict with the above as keys and the quantity of each for values and generators for
        routed LSPs with no Demands, routed LSPs carrying Demands, Demands riding LSPs

        This is not cached currently and my be expensive to (re)run on a very large model.  Current best
        practice is to assign the output of this to a variable:

        ex: sim_diag1 = model1.simulation_diagnostics()

        """

        simulation_data = {'Number of routed LSPs carrying Demands': 'TBD',
                           'Number of routed LSPs with no Demands': 'TBD',
                           'Number of Demands riding LSPs': 'TBD',
                           'Number of Demands not riding LSPs': 'TBD',
                           'Number of unrouted LSPs': 'TBD',
                           'Number of unrouted Demands': 'TBD',
                           'routed LSPs with no demands generator': 'TBD',
                           'routed LSPs with demands generator': 'TBD',
                           'demands riding LSPs generator': 'TBD'}

        # Find LSPs with and without demands
        lsps_routed_no_demands = [lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                  lsp.demands_on_lsp(self) == []]

        lsps_routed_with_demands = [lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                    lsp.demands_on_lsp(self) != []]

        # Find demands riding LSPs
        dmds_riding_lsps = set()

        # Find unrouted LSPs
        for dmd in (dmd for dmd in self.demand_objects):
            for object in dmd.path:
                if isinstance(object, RSVP_LSP):
                    dmds_riding_lsps.add(dmd)
        unrouted_lsps = [lsp for lsp in self.rsvp_lsp_objects if lsp.path == 'Unrouted']

        # Update the quantities in simulation_data
        simulation_data['Number of routed LSPs carrying Demands'] = len(lsps_routed_with_demands)
        simulation_data['Number of routed LSPs with no Demands'] = len(lsps_routed_no_demands)
        simulation_data['Number of Demands riding LSPs'] = len(dmds_riding_lsps)
        simulation_data['Number of Demands not riding LSPs'] = len(self.demand_objects) - len(dmds_riding_lsps)
        simulation_data['Number of unrouted LSPs'] = len(unrouted_lsps)
        simulation_data['Number of unrouted Demands'] = len(self.get_unrouted_demand_objects())

        # Create generators to be returned
        dmds_riding_lsps_gen = (dmd for dmd in dmds_riding_lsps)
        lsps_routed_no_demands_gen = (lsp for lsp in lsps_routed_no_demands)
        lsps_routed_with_demands_gen = (lsp for lsp in lsps_routed_with_demands)

        # Update generators in simulation_data
        simulation_data['routed LSPs with no demands generator'] = lsps_routed_no_demands_gen
        simulation_data['routed LSPs with demands generator'] = lsps_routed_with_demands_gen
        simulation_data['demands riding LSPs generator'] = dmds_riding_lsps_gen

        return simulation_data

    def _make_int_info_dict(self):
        """
        Makes dict of information for each interface.  Most of this information
        is derived from the simulation.
        Returns dict object.  Keys are the _key for each Interface; values are
        dicts for each interface_ key that hold information about the Interface.
        :return: int_info
        """
        keys = (interface._key for interface in self.interface_objects)
        int_info = {key: {'lsps': [], 'reserved_bandwidth': 0} for key in keys}
        for lsp in (lsp for lsp in self.rsvp_lsp_objects if 'Unrouted' not in lsp.path):
            for interface in lsp.path['interfaces']:
                int_info[interface._key]['lsps'].append(lsp)
                int_info[interface._key]['reserved_bandwidth'] += round(lsp.reserved_bandwidth, 1)
        return int_info

    def _validate_circuit_interface_capacity(self, circuits_with_mismatched_interface_capacity, ckt):
        """
        Checks ckt's component Interfaces for matching capacity
        :param circuits_with_mismatched_interface_capacity: list that will store
        Circuits that have mismatched Interface capacity
        :param ckt: Circuit object to check
        :return: None
        """
        int1 = ckt.get_circuit_interfaces(self)[0]
        int2 = ckt.get_circuit_interfaces(self)[1]
        # Match the failed status to True if they are different
        if int1.failed != int2.failed:
            int1.failed = True  # pragma: no cover
            int2.failed = True  # pragma: no cover
        # Make sure the interface capacities in the circuit match
        if int1.capacity != int2.capacity:
            circuits_with_mismatched_interface_capacity.append(ckt)

    def _reserved_bw_error_checks(self, int_info, int_res_bw_sum_error, int_res_bw_too_high, interface):
        """
        Checks interface for the following:
        - Is reserved_bandwidth > capacity?
        - Does reserved_bandwidth for interface match the sum of the
        reserved_bandwidth for the LSPs egressing interface?
        :param int_info: dict that holds int_res_bw_sum_error and
        int_res_bw_too_high sets.  Has the following format for a given
        entry:
        int_info[interface._key] = {'lsps': [], 'reserved_bandwidth': 0}
        Where 'lsps' is a list of RSVP LSPs egressing the Interface and
        'reserved_bandwidth' is the reserved_bandwidth value generated
        by the simulation
        :param int_res_bw_sum_error: set that will hold Interface objects
        whose reserved_bandwidth does not match the sum of the
        reserved_bandwidth for the LSPs egressing interface
        :param int_res_bw_too_high: set that will hold Interface objects
        whose reserved_bandwidth is > the capacity of the Interface
        :param interface: Interface object to inspect
        :return: None
        """

        if interface.reserved_bandwidth > interface.capacity:
            int_res_bw_too_high.add(interface)
        if round(interface.reserved_bandwidth, 1) != round(int_info[interface._key][
            'reserved_bandwidth'], 1):  # pragma: no cover  # noqa
            int_res_bw_sum_error.add((interface, interface.reserved_bandwidth, tuple(interface.lsps(self))))

    def _demand_traffic_per_int(self, demand):  # common between model and parallel_link_model
        """
        Given a Demand object, return the (key, value) pairs for how much traffic each
        Interface gets from the routing of the traffic load over Model Interfaces.

        : demand: Demand object
        : return: dict of (Interface: <traffic from demand> ) k, v pairs

        Example: The interface from node G to node D below has 2.5 units of traffic from 'demand';
                 the interface from A to B has 10.0, etc.
        {Interface(name = 'A-to-B', cost = 4, capacity = 100, node_object = Node('A'),
        remote_node_object = Node('B'), circuit_id = '1'): 12.0,
         Interface(name = 'A-to-B_2', cost = 4, capacity = 50, node_object = Node('A'),
         remote_node_object = Node('B'), circuit_id = '2'): 12.0,
         Interface(name = 'B-to-E', cost = 3, capacity = 200, node_object = Node('B'),
         remote_node_object = Node('E'), circuit_id = '7'): 8.0,
         Interface(name = 'B-to-E_3', cost = 3, capacity = 200, node_object = Node('B'),
         remote_node_object = Node('E'), circuit_id = '27'): 8.0,
         Interface(name = 'B-to-E_2', cost = 3, capacity = 200, node_object = Node('B'),
         remote_node_object = Node('E'), circuit_id = '17'): 8.0}

        """

        shortest_path_int_list = []
        for path in demand.path:
            shortest_path_int_list += path

        # Unique interfaces across all shortest paths
        shortest_path_int_set = set(shortest_path_int_list)

        # Dict to store how many unique next hops each node has in the shortest paths
        unique_next_hops = {}

        # Iterate through all the interfaces
        for interface in shortest_path_int_set:
            # For a given Interface's node_object, determine how many
            # Interfaces on that Node are facing next hops
            unique_next_hops[interface.node_object.name] = [intf.node_object.name for intf in shortest_path_int_set
                                                            if intf.node_object.name == interface.node_object.name]

        # TODO - find shorter example here
        # shortest_path_info will be a dict with the following info for each path:
        # - an ordered list of interfaces in the path
        # - a dict of cumulative splits for each interface at that point in the path
        # - the amount of traffic on the path
        # Example:
        # shortest_path_info =
        # {'path_0': {'interfaces': [
        #     Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'), remote_node_object=Node('B'),
        #               circuit_id='2'),
        #     Interface(name='B-to-E_2', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #               circuit_id='17')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='2'): 2,
        #                        Interface(name='B-to-E_2', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='17'): 6}},
        #  'path_1': {'interfaces': [
        #      Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='2'),
        #      Interface(name='B-to-E', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #                circuit_id='7')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='2'): 2,
        #                        Interface(name='B-to-E', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='7'): 6}},
        #  'path_2': {'interfaces': [
        #      Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='2'),
        #      Interface(name='B-to-E_3', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #                circuit_id='27')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B_2', cost=4, capacity=50, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='2'): 2,
        #                        Interface(name='B-to-E_3', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='27'): 6}},
        #  'path_3': {'interfaces': [
        #      Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='1'),
        #      Interface(name='B-to-E_2', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #                circuit_id='17')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='1'): 2,
        #                        Interface(name='B-to-E_2', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='17'): 6}},
        #  'path_4': {'interfaces': [
        #      Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='1'),
        #      Interface(name='B-to-E', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #                circuit_id='7')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='1'): 2,
        #                        Interface(name='B-to-E', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='7'): 6}},
        #  'path_5': {'interfaces': [
        #      Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'), remote_node_object=Node('B'),
        #                circuit_id='1'),
        #      Interface(name='B-to-E_3', cost=3, capacity=200, node_object=Node('B'), remote_node_object=Node('E'),
        #                circuit_id='27')],
        #             'path_traffic': 4.0,
        #             'splits': {Interface(name='A-to-B', cost=4, capacity=100, node_object=Node('A'),
        #                                  remote_node_object=Node('B'), circuit_id='1'): 2,
        #                        Interface(name='B-to-E_3', cost=3, capacity=200, node_object=Node('B'),
        #                                  remote_node_object=Node('E'), circuit_id='27'): 6}}}
        shortest_path_info = {}
        path_counter = 0

        # Iterate thru each path for the demand
        for path in demand.path:
            # Dict of cumulative splits per interface
            traffic_splits_per_interface = {}

            path_key = 'path_' + str(path_counter)

            shortest_path_info[path_key] = {}

            # Create cumulative path splits for each interface
            total_splits = 1
            for interface in path:
                total_splits = total_splits * len(unique_next_hops[interface.node_object.name])
                traffic_splits_per_interface[interface] = total_splits

            # Find path traffic
            max_split = max([split for split in traffic_splits_per_interface.values()])
            path_traffic = float(demand.traffic) / float(max_split)

            shortest_path_info[path_key]['interfaces'] = path
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

        # Round all traffic values to 1 decimal place
        traff_per_int = {interface: round(traffic, 1) for interface, traffic in traff_per_int.items()}

        return traff_per_int

    def _update_interface_utilization(self):  # common between model and parallel_link_model
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
                    interface.traffic += traffic_from_demand

        return self

    def _route_demands(self, demands, input_model):  # common between model and parallel_link_model
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
        parallel_lsp_groups = self.parallel_lsp_groups()  # TODO - can this be optimized?

        # Find all the parallel demand groups
        parallel_demand_groups = self.parallel_demand_groups()  # TODO - can this be optimized?

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
            for lsp in lsps:  # TODO - can this be optimized?
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
        route may be able to signal for a new, optimal setup_bandwidth, one based
        on more than one parallel LSP not routing.  This new path would natively
        have enough bandwidth to signal the new LSP setup bandwidth, regardless of
        how much setup bandwidth an LSP was already consuming on a common interface

        :param input_model: Model object containing the parallel LSP group; typically
        this Model will consist only of non-failed interfaces from self.
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
            # a 'setup_bandwidth_optimized' amount of setup_bandwidth

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

        if self._parallel_lsp_groups == {}:
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

            self._parallel_lsp_groups = parallel_lsp_groups
            return parallel_lsp_groups

        else:
            return self._parallel_lsp_groups

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

    @property
    def all_interface_circuit_ids(self):
        """
        Returns all interface circuit_ids
        """
        return set(interface.circuit_id for interface in self.interface_objects)

    def add_demand(self, source_node_name, dest_node_name, traffic=0, name='none'):
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
        added_demand = Demand(source_node_object, dest_node_object, traffic, name)
        if added_demand._key in set([demand._key for demand in self.demand_objects]):
            message = '{} already exists in demand_objects'.format(added_demand)
            raise ModelException(message)
        self.demand_objects.add(added_demand)

        self.validate_model()

    @classmethod
    def _add_lsp_from_data(cls, demands_info_end_index, lines, lsp_set, node_set):  # TODO - same as model
        lsp_info_begin_index = demands_info_end_index + 3
        lsp_lines = lines[lsp_info_begin_index:]
        for lsp_line in lsp_lines:
            lsp_info = lsp_line.split()
            source = lsp_info[0]
            try:
                source_node = [node for node in node_set if node.name == source][0]
            except IndexError:
                err_msg = "No Node with name {} in Model; {}".format(source, lsp_info)
                raise ModelException(err_msg)
            dest = lsp_info[1]
            try:
                dest_node = [node for node in node_set if node.name == dest][0]
            except IndexError:
                err_msg = "No Node with name {} in Model; {}".format(dest, lsp_info)
                raise ModelException(err_msg)
            name = lsp_info[2]
            try:
                configured_setup_bw = lsp_info[3]
            except IndexError:
                configured_setup_bw = None
            new_lsp = RSVP_LSP(source_node, dest_node, name, configured_setup_bandwidth=configured_setup_bw)

            if new_lsp._key not in set([lsp._key for lsp in lsp_set]):
                lsp_set.add(new_lsp)
            else:
                print("{} already exists in model; disregarding line {}".format(new_lsp, lines.index(lsp_line)))

    @classmethod
    def _add_demand_from_data(cls, demand_line, demand_set, lines, node_set):  # same as Model call
        demand_info = demand_line.split()
        source = demand_info[0]
        try:
            source_node = [node for node in node_set if node.name == source][0]
        except IndexError:
            err_msg = "No Node with name {} in Model; {}".format(source, demand_info)
            raise ModelException(err_msg)
        dest = demand_info[1]
        try:
            dest_node = [node for node in node_set if node.name == dest][0]
        except IndexError:
            err_msg = "No Node with name {} in Model; {}".format(dest, demand_info)
            raise ModelException(err_msg)

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

    @classmethod
    def _add_node_from_data(cls, demand_set, interface_set, lines, lsp_set, node_line, node_set):
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
            existing_node = cls(interface_set, node_set, demand_set, lsp_set).get_node_object(node_name=node_name)
            existing_node.lat = node_lat
            existing_node.lon = node_lon
