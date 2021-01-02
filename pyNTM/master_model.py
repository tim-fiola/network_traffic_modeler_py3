"""
Parent Class for FlexModel and PerformanceModel objects.

A class that defines the network being modeled and that contains all
modeled objects in the network such as Nodes, Interfaces, Circuits,
and Demands.

This cannot be used to instantiate a functioning model directly.  Use a subclass
FlexModel or PerformanceModel
"""

from .demand import Demand
from .exceptions import ModelException
from .interface import Interface
from .node import Node
from .rsvp import RSVP_LSP
from .srlg import SRLG

from pprint import pprint


class _MasterModel(object):
    """
    Parent class for Model and Parallel_Link_Model subclasses; holds common defs.
    This cannot be used to instantiate a functioning model directly.  Use a subclass
    FlexModel or PerformanceModel
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

    def simulation_diagnostics(self):
        """
        Analyzes simulation results and looks for the following:

        - Number of routed LSPs carrying Demands
        - Number of routed LSPs with no Demands
        - Number of Demands riding LSPs
        - Number of Demands not riding LSPs
        - Number of unrouted LSPs
        - Number of unrouted Demands

        :return: dict with the above as keys and the quantity of each for values and generators for routed LSPs with no Demands, routed LSPs carrying Demands, Demands riding LSPs  # noqa E501

        This is not cached currently and my be expensive to (re)run on a very large model.  Current best
        practice is to assign the output of this to a variable:

        Example::

            sim_diag1 = model1.simulation_diagnostics()

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
        for dmd in iter(self.demand_objects):
            for path in dmd.path:
                for object in path:
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
        dmds_riding_lsps_gen = iter(dmds_riding_lsps)
        lsps_routed_no_demands_gen = iter(lsps_routed_no_demands)
        lsps_routed_with_demands_gen = iter(lsps_routed_with_demands)

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

    def _route_lsps(self):
        """Route the LSPs in the model
        1.  Get LSPs into groups with matching source/dest
        2.  Find all the demands that take the LSP group
        3.  Route the LSP group, one at a time

        :return: self, with updated LSP paths
        """

        for interface in self.interface_objects:
            interface.reserved_bandwidth = 0

        # Find parallel LSP groups
        parallel_lsp_groups = self.parallel_lsp_groups()

        # Find all the parallel demand groups
        parallel_demand_groups = self.parallel_demand_groups()

        # Route the LSPs by parallel group
        self._route_parallel_lsp_groups(parallel_demand_groups, parallel_lsp_groups)

        return self

    def _route_parallel_lsp_groups(self, parallel_demand_groups, parallel_lsp_groups):
        """
        Routes LSPs with same source, dest (parallel LSPs) based on the demands that would
        take those LSPs.  For each LSP, determine a 'path' attribute.

        :param parallel_demand_groups: dict with keys = source_node-dest_node and values being a
        list of all demands with the common corresponding source and dest nodes
        :param parallel_lsp_groups: dict with keys = source_node-dest_node and values being a
        list of all LSPs with the common corresponding source and dest nodes
        :return: None; assigns path to each LSP
        """
        # Counter for LSP groups
        counter = 1

        # Route LSPs by source, dest (parallel) groups
        for group, lsps in parallel_lsp_groups.items():

            num_lsps_in_group = len(lsps)

            print("Routing {} LSPs in parallel LSP group {}; {}/{}".format(num_lsps_in_group, group, counter,
                                                                           len(parallel_lsp_groups)))
            # Traffic each LSP in a parallel LSP group will carry; initialize
            traffic_in_demand_group = 0
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

            # Determine LSP's specific path and reserved bandwidth; also consume
            # reserved bandwidth on transited Interfaces
            self._determine_lsp_state_info(lsps, traff_on_each_group_lsp)

            routed_lsps_in_group = [lsp for lsp in lsps if lsp.path != 'Unrouted']

            # ##### Optimize the LSP group reserved bandwidth #####
            # If not all the LSPs in the group can route at the lowest (initial)
            # setup bandwidth, determine which LSPs can signal and for how much traffic
            if len(routed_lsps_in_group) != len(lsps) and len(routed_lsps_in_group) > 0:
                self._optimize_parallel_lsp_group_res_bw(self, routed_lsps_in_group, traffic_in_demand_group)

            counter += 1

    def _add_lsp_path_data(self, lsp, path):
        """
        Adds data about an LSP's path: cost of path and reservable bandwidth
        on the path at the time the LSP was signaled.  Sets the lsp.path
        attribute to the path data

        :param lsp: RSVP LSP object
        :param path: List of Interface objects along the path
        :return: None
        """
        path_cost = sum(interface.cost for interface in path)
        baseline_path_reservable_bw = min(
            interface.reservable_bandwidth for interface in path
        )

        lsp.path = {'interfaces': path,
                    'path_cost': path_cost,
                    'baseline_path_reservable_bw': baseline_path_reservable_bw}

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

        :return: None
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

        :return: dict with entries where key is 'source_node_name-dest_node_name' and value is a list of LSPs with matching source/dest nodes  # noqa E501

        Example::

            {'A-F': [RSVP_LSP(source = A, dest = F, lsp_name = 'lsp_a_f')],
            'A-D': [RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_1'),
            RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_2'),
            RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_4'),
            RSVP_LSP(source = A, dest = D, lsp_name = 'lsp_a_d_3')],
            'B-C': [RSVP_LSP(source = B, dest = C, lsp_name = 'lsp_b_c_1')],
            'F-E': [RSVP_LSP(source = F, dest = E, lsp_name = 'lsp_f_e_1')]}

        """

        if self._parallel_lsp_groups != {}:
            return self._parallel_lsp_groups
        src_node_names = {lsp.source_node_object.name for lsp in self.rsvp_lsp_objects}
        dest_node_names = {lsp.dest_node_object.name for lsp in self.rsvp_lsp_objects}

        parallel_lsp_groups = {}

        for src_node_name in src_node_names:
            for dest_node_name in dest_node_names:
                key = '{}-{}'.format(src_node_name, dest_node_name)
                parallel_lsp_groups[key] = []
                for lsp in self.rsvp_lsp_objects:
                    if (lsp.source_node_object.name == src_node_name and
                            lsp.dest_node_object.name == dest_node_name):
                        parallel_lsp_groups[key].append(lsp)

                if not parallel_lsp_groups[key]:
                    del parallel_lsp_groups[key]

        self._parallel_lsp_groups = parallel_lsp_groups
        return parallel_lsp_groups

    def parallel_demand_groups(self):
        """
        Determine demands with same source and dest nodes

        :return: dict with entries where key is 'source_node_name-dest_node_name' and value is a list of demands with matching source/dest nodes   # noqa E501

        Example::

            {'A-F': [Demand(source = A, dest = F, traffic = 40, name = 'dmd_a_f_1')],
            'A-D': [Demand(source = A, dest = D, traffic = 80, name = 'dmd_a_d_1'),
            Demand(source = A, dest = D, traffic = 70, name = 'dmd_a_d_2'),
            Demand(source = A, dest = D, traffic = 100, name = 'dmd_a_to_d_3')],
            'F-E': [Demand(source = F, dest = E, traffic = 400, name = 'dmd_f_e_1')]}
        """

        src_node_names = {dmd.source_node_object.name for dmd in self.demand_objects}
        dest_node_names = {dmd.dest_node_object.name for dmd in self.demand_objects}

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

        for node in iter(self.node_objects):
            node_int_list = [interface.name for interface in node.interfaces(self)]
            node_int_set = set(node_int_list)

            if len(node_int_list) > len(node_int_set):
                # Find which ints are duplicate
                for item in node_int_set:
                    node_int_list.remove(item)
                # Add the remaining node and interface name to exception_interfaces
                for item in node_int_list:
                    exception_interfaces.add((node, item))

        if exception_interfaces:
            # raise ModelException(message)
            return (
                "Interface names must be unique per node.  The following"
                " nodes have duplicate interface names {}".format(
                    exception_interfaces
                )
            )

        else:
            return True

    @property
    def all_interface_circuit_ids(self):
        """
        Returns all interface circuit_ids
        """
        return {interface.circuit_id for interface in self.interface_objects}

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
        if added_demand._key in {demand._key for demand in self.demand_objects}:
            message = '{} already exists in demand_objects'.format(added_demand)
            raise ModelException(message)
        self.demand_objects.add(added_demand)

        self.validate_model()

    @classmethod
    def _add_lsp_from_data(cls, lsp_info_begin_index, lines, lsp_set, node_set):
        """
        Adds LSP data from info in a data file to Class

        :param demands_info_end_index: line index where demand info ends
        :param lines: input lines from data file
        :param lsp_set: set of RSVP_LSP objects
        :param node_set: set of Node objects

        """

        lsp_lines = lines[lsp_info_begin_index:]
        for lsp_line in lsp_lines:
            lsp_info = lsp_line.split('\t')
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
                configured_setup_bw = float(lsp_info[3])
            except (IndexError, ModelException, ValueError):
                configured_setup_bw = None
            try:
                manual_metric = int(lsp_info[4])
            except (IndexError, ModelException, ValueError):
                manual_metric = None

            new_lsp = RSVP_LSP(source_node, dest_node, name, configured_setup_bandwidth=configured_setup_bw,
                               configured_manual_metric=manual_metric)

            if new_lsp._key not in {lsp._key for lsp in lsp_set}:
                lsp_set.add(new_lsp)
            else:
                print("{} already exists in model; disregarding line {}".format(new_lsp, lines.index(lsp_line)))

    @classmethod
    def _add_demand_from_data(cls, demand_line, demand_set, lines, node_set):
        """
        Adds Demand from line of data

        :param demand_line: line of data for demand
        :param demand_set: set of Demands in model
        :param lines: lines of data from input file
        :param node_set: set of Nodes from model

        """
        demand_info = demand_line.split('\t')
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
        demand_name = 'none' if name == '' else name
        new_demand = Demand(source_node, dest_node, traffic, demand_name)
        if new_demand._key not in {dmd._key for dmd in demand_set}:
            demand_set.add(new_demand)
        else:
            print("{} already exists in model; disregarding line {}".format(new_demand,
                                                                            lines.index(demand_line)))

    @classmethod
    def _add_node_from_data(cls, demand_set, interface_set, lsp_set, node_line, node_set):
        node_info = node_line.split('\t')
        node_name = node_info[0]
        # Set latitude
        try:
            node_lat = int(node_info[2])
        except (ValueError, IndexError):
            node_lat = 0
        # Set longitude
        try:
            node_lon = int(node_info[1])
        except (ValueError, IndexError):
            node_lon = 0

        new_node = Node(node_name)
        # Set igp_shortcuts_enabled; only used in FlexModel, ignored in PerformanceModel
        try:
            igp_shortcuts_enabled_value = new_node.igp_shortcuts_enabled = node_info[3]
        except IndexError:
            igp_shortcuts_enabled_value = False
        if node_name not in {node.name for node in node_set}:  # Pick up orphan nodes
            node_set.add(new_node)
            new_node.lat = node_lat
            new_node.lon = node_lon
            new_node.igp_shortcuts_enabled = igp_shortcuts_enabled_value
        else:
            existing_node = cls(interface_set, node_set, demand_set, lsp_set).get_node_object(node_name=node_name)
            existing_node.lat = node_lat
            existing_node.lon = node_lon
            existing_node.igp_shortcuts_enabled = igp_shortcuts_enabled_value

        return node_set

    def _does_interface_exist(self, interface_name, node_object_name):
        """
        Does specified Interface exist in self?  Raises exception if it
        does not.

        :param interface_name: Interface name
        :param node_object_name: Node name
        """
        int_key = (interface_name, node_object_name)
        interface_key_iterator = (interface._key for interface in self.interface_objects)

        if int_key not in (interface_key_iterator):
            raise ModelException('specified interface does not exist')

    def get_circuit_object_from_interface(self, interface_name, node_name):
        """
        Returns a Circuit object, given a Node name and Interface name

        :param interface_name: Interface object on one side of Circuit
        :param node_name: Node name where Interface resides
        :return: Circuit object from self that contains Interface with interface_name and node_name
        """

        # Does interface exist?
        self._does_interface_exist(interface_name, node_name)

        interface = self.get_interface_object(interface_name, node_name)

        ckts = [ckt for ckt in self.circuit_objects if interface in (ckt.interface_a, ckt.interface_b)]

        return ckts[0]

    def get_failed_interface_objects(self):
        """
        Returns a list of all failed interfaces in self
        """
        return [
            interface
            for interface in iter(self.interface_objects)
            if interface.failed
        ]

    def get_unfailed_interface_objects(self):
        """
        Returns a list of all non-failed interfaces in the self
        """

        interface_iter = iter(self.interface_objects)

        return {interface for interface in interface_iter if not interface.failed}

    def get_unrouted_demand_objects(self):
        """
        Returns list of demand objects that cannot be routed in self
        """
        return [
            demand
            for demand in iter(self.demand_objects)
            if demand.path == "Unrouted"
        ]

    def change_interface_name(self, node_name, current_interface_name, new_interface_name):
        """
        Changes interface name

        :param node_name: name of Node holding Interface
        :param current_interface_name: current Interface name
        :param new_interface_name: new Interface name
        :return: Interface with new name
        """
        interface_to_edit = self.get_interface_object(current_interface_name, node_name)
        interface_to_edit.name = new_interface_name

        return interface_to_edit

    def fail_interface(self, interface_name, node_name):
        """
        Fails the Interface in self object for the interface_name/node_name pair

        :param interface_name: name of Interface object
        :param node_name: Name of Node holding Interface

        """

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

        :param interface_name: name of interface
        :param node_name: node name
        :param raise_exception: If raise_exception=True, an exception
                                will be raised if the interface cannot be unfailed.
                                An example of this would be if you tried to unfail
                                the interface when the parent node or remote node
                                was in a failed state
        :return: Interface object from Model with 'failed' attribute set to False
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

    def get_interface_object(self, interface_name, node_name):
        """
        Returns an interface object for specified node name and interface name

        :param interface_name: name of Interface
        :param node_name: name of Node
        :return: Specified Interface object from self
        """

        self._does_interface_exist(interface_name, node_name)

        node_object = self.get_node_object(node_name)

        int_object = [interface for interface in node_object.interfaces(self) if interface.name == interface_name]
        return int_object[0]

    # NODE CALLS ######
    def get_node_interfaces(self, node_name):
        """Returns list of interfaces on specified node name"""
        return Node(node_name).interfaces(self)

    def fail_node(self, node_name):
        """Fails specified Node with name node_name"""

        # Find node's interfaces and fail them
        ints_to_fail_iterator = iter(self.get_node_interfaces(node_name))

        for interface in ints_to_fail_iterator:
            self.fail_interface(interface.name, node_name)

        # Change the failed property on the specified node
        self.get_node_object(node_name).failed = True

    def unfail_node(self, node_name):
        """Unfails the Node with name=node_name"""

        # Change the failed property on the specified node;
        self.get_node_object(node_name).failed = False

        # Find node's interfaces and unfail them
        ints_to_unfail_iterator = iter(self.get_node_interfaces(node_name))

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
        Returns a list of all failed Nodes in self
        """
        failed_nodes = []

        for node in iter(self.node_objects):
            if node.failed:
                node_object = self.get_node_object(node.name)
                failed_nodes.append(node_object)

        return failed_nodes

    def get_non_failed_node_objects(self):
        """Returns a list of all failed nodes"""
        non_failed_nodes = []

        for node in iter(self.node_objects):
            if not node.failed:
                node_object = self.get_node_object(node.name)
                non_failed_nodes.append(node_object)

        return non_failed_nodes

    # Display calls #########
    def display_interface_status(self):    # pragma: no cover
        """Returns failed = True/False for each interface"""

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12), end=' ')
        print('Failed'.ljust(12))

        interface_iterator = iter(self.interface_objects)

        for interface in interface_iterator:
            print(interface.node_object.name.ljust(12), interface.name.ljust(12), end=' ')
            print(interface.remote_node_object.name.ljust(12), end=' ')
            print(str(interface.failed).ljust(12))

    def display_node_status(self):    # pragma: no cover
        """Returns failed = True/False for each node"""

        print('Node'.ljust(12), 'Failed'.ljust(12))

        node_iterator = iter(self.node_objects)

        for node in node_iterator:
            print(node.name.ljust(12), str(node.failed).ljust(12))

    def display_interfaces_traffic(self):    # pragma: no cover
        """
        A human-readable(-ish) display of interfaces and traffic on each
        """

        print('Node'.ljust(12), 'Interface'.ljust(12), 'Remote Node'.ljust(12), 'Traffic'.ljust(12))

        interface_iterator = iter(self.interface_objects)

        for interface in interface_iterator:
            print(interface.node_object.name.ljust(12), interface.name.ljust(12), end=' ')
            print(interface.remote_node_object.name.ljust(12), end=' ')
            print(repr(interface.traffic).ljust(12))

    def display_demand_paths(self):    # pragma: no cover
        """
        Displays each demand and its path(s) across the network
        """

        demand_iter = iter(self.demand_objects)

        for demand in demand_iter:
            print('demand._key is', demand._key)
            print('Demand has %s paths:' % (len(demand.path)))
            for path in demand.path:
                pprint(path)
                print()
            print()
            print()

    def display_interface_objects(self):  # pragma: no cover
        """Displays interface objects in a more human readable manner"""

        for interface in self.interface_objects:
            pprint(interface)
            print()

    def get_demand_objects_source_node(self, source_node_name):
        """
        Returns list of demand objects originating at the node with name
        source_node_name

        :param source_node_name: name of source node for Demands
        :return: list of Demands originating at node
        """

        return [
            demand
            for demand in iter(self.demand_objects)
            if demand.source_node_object.name == source_node_name
        ]

    def get_demand_objects_dest_node(self, dest_node_name):
        """
        Returns list of demands objects originating at the
        destination node

        :param dest_node_name: name of destination node for Demands
        :return: list of Demands terminating on destination node
        """
        return [
            demand
            for demand in iter(self.demand_objects)
            if demand.dest_node_object.name == dest_node_name
        ]

    # ### SRLG Calls ### #
    def get_srlg_object(self, srlg_name, raise_exception=True):
        """
        Returns SRLG in self with srlg_name

        :param srlg_name: name of SRLG
        :param raise_exception: raise an exception if SRLG with name=srlg_name does not exist in self
        :return: None
        """

        srlg_already_in_model = [srlg for srlg in self.srlg_objects if srlg.name == srlg_name]

        if len(srlg_already_in_model) == 1:
            return srlg_already_in_model[0]  # There will only be one SRLG with srlg_name
        else:
            if raise_exception:
                msg = "No SRLG with name {} exists in Model".format(srlg_name)
                raise ModelException(msg)
            else:
                return None

    def fail_srlg(self, srlg_name):
        """
        Sets SRLG with name srlg_name to failed = True

        :param srlg_name: name of SRLG to fail
        :return: none
        """

        srlg_to_fail = self.get_srlg_object(srlg_name)

        # Find SRLG's Nodes to fail
        nodes_to_fail_iterator = (node for node in self.node_objects if node in srlg_to_fail.node_objects)

        for node in nodes_to_fail_iterator:
            self.fail_node(node.name)

        # Find SRLG's Interfaces to fail
        interfaces_to_fail_iterator = (interface for interface in self.interface_objects if
                                       interface in srlg_to_fail.interface_objects)

        for interface in interfaces_to_fail_iterator:
            self.fail_interface(interface.name, interface.node_object.name)

        # Change the failed property on the specified srlg
        srlg_to_fail.failed = True

    def unfail_srlg(self, srlg_name):
        """
        Sets SRLG with srlg_name to failed = False
        :param srlg_name: name of SRLG to unfail
        :return: none
        """

        srlg_to_unfail = self.get_srlg_object(srlg_name)

        # Change the failed property on the specified srlg
        srlg_to_unfail.failed = False

        # Find SRLG's Nodes to unfail
        nodes_to_unfail_iterator = (node for node in self.node_objects if node in srlg_to_unfail.node_objects)

        # Node will stay failed if it's part of another SRLG that is still failed;
        # in that case, the unfail_node will create an exception; ignore that exception
        for node in nodes_to_unfail_iterator:
            try:
                self.unfail_node(node.name)
            except ModelException:
                pass

        # Find SRLG's Interfaces to unfail
        interfaces_to_unfail_iterator = (interface for interface in self.interface_objects if
                                         interface in srlg_to_unfail.interface_objects)

        # Interface will stay failed if it's part of another SRLG that is still failed or
        # if the local/remote Node is failed;  in that case, the unfail_interface
        # will create an exception; ignore that exception
        for interface in interfaces_to_unfail_iterator:
            try:
                self.unfail_interface(interface.name, interface.node_object.name)
            except ModelException:
                pass

    def add_srlg(self, srlg_name):
        """
        Adds SRLG object to Model

        :param srlg_name: name of SRLG to add to self

        """

        if srlg_name in {srlg.name for srlg in self.srlg_objects}:
            raise ModelException("SRLG with name {} already exists in Model".format(srlg_name))
        else:
            srlg = SRLG(srlg_name, self)
            self.srlg_objects.add(srlg)

    def is_node_an_orphan(self, node_object):
        """
        Determines if a node is in orphan_nodes.  A node in
        orphan_nodes is a Node with no Interface objects

        :param node_object: Node object
        :return: Boolean indicating if Node is orphan (True) or not (False)
        """
        return node_object in self.get_orphan_node_objects()

    def get_orphan_node_objects(self):
        """
        Returns list of Nodes that have no interfaces
        """
        return [node for node in self.node_objects if len(node.interfaces(self)) == 0]

    def add_node(self, node_object):
        """
        Adds a node object to the model object and validates self

        :param node_object: Node object to add to self
        """

        if node_object.name in (node.name for node in self.node_objects):
            message = "A node with name {} already exists in the model".format(node_object.name)
            raise ModelException(message)
        else:
            self.node_objects.add(node_object)

        self.validate_model()

    def get_node_object(self, node_name):
        """
        Returns a Node object from self, given a Node's name

        :param node_name: name of Node object in self
        :return: Node object with node_name
        """
        matching_node = [node for node in self.node_objects if node.name == node_name]

        if matching_node:
            return matching_node[0]
        else:
            message = "No node with name %s exists in the model" % node_name
            raise ModelException(message)

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

        if added_lsp._key in {lsp._key for lsp in self.rsvp_lsp_objects}:
            message = '{} already exists in rsvp_lsp_objects'.format(added_lsp)
            raise ModelException(message)
        self.rsvp_lsp_objects.add(added_lsp)

        self.validate_model()

    def get_demand_object(self, source_node_name, dest_node_name, demand_name='none'):
        """
        Returns demand specified by the source_node_name, dest_node_name, name;
        throws exception if demand not found

        :param source_node_name: name of Node where desired Demand originates (source)
        :param dest_node_name: name of Node where desired Demand terminates (destination)
        :param demand_name: name of Demand object
        :return: desired Demand object that matches parameters above
        """
        model_demand_iterator = iter(self.demand_objects)

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
        """
        Returns the RSVP LSP from the model with the specified source node
        name, dest node name, and LSP name.

        :param source_node_name: name of source node for LSP
        :param dest_node_name: name of destination node for LSP
        :param lsp_name: name of LSP
        :return: RSVP_LSP object
        """

        needed_key = (source_node_name, dest_node_name, lsp_name)

        if needed_key not in (lsp._key for lsp in self.rsvp_lsp_objects):
            msg = ("LSP with source node %s, dest node %s, and name %s "
                   "does not exist in model" % (source_node_name, dest_node_name, lsp_name))
            raise ModelException(msg)
        else:
            for lsp in iter(self.rsvp_lsp_objects):
                if lsp._key == needed_key:
                    return lsp

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
                             interface['circuit_id'])
            network_interface_objects.add(intf)

            # Check to see if the Interface's Node already exists, if not, add it
            node_names = ([node.name for node in self.node_objects])
            if interface['node'] not in node_names:
                network_node_objects.add(Node(interface['node']))
            if interface['remote_node'] not in node_names:
                network_node_objects.add(Node(interface['remote_node']))

        return (network_interface_objects, network_node_objects)
