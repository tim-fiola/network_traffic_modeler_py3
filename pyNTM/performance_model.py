"""
A class that defines the network being modeled and that contains all
modeled objects in the network such as Nodes, Interfaces, Circuits,
and Demands.

Allows a single connection (Circuit) between layer3 Nodes.  If multiple
Circuits between Nodes is needed, use FlexModel class.

This PerformanceModel class will generally perform better than FlexModel due
to the latter's requirement to check for multiple Circuits between Nodes and
deal with more diverse possible topology features.

This is the high-performance model class: it will converge
about 20-30% faster than the FlexModel object.  However, the
PerformanceModel class has the following restriction:
    - THIS CLASS DOES ONLY SUPPORTS A SINGLE CIRCUIT (EDGE) BETWEEN LAYER 3 NODES

In general, this class will support less topology features than the
FlexModel class.  For simpler networks without complex topology features,
this may be the class to use if fast model convergence is important.

If you are not sure whether to use the PerformanceModel or FlexModel object,
it's best to use the FlexModel class.

This PerformanceModel class is the same as the legacy (version 1.6 and earlier) Model class.

"""

from datetime import datetime
from pprint import pprint

import networkx as nx
import random

from .circuit import Circuit
from .interface import Interface
from .exceptions import ModelException
from .master_model import _MasterModel
from .utilities import find_end_index
from .node import Node

# TODO - call to analyze model for Unrouted LSPs and LSPs not on shortest path
# TODO - add simulation summary output with # failed nodes, interfaces, srlgs, unrouted lsp/demands,
#  routed lsp/demands in dict form
# TODO - add support for SRLGs in load_model_file
# TODO - add attribute for Node/Interface whereby an object can be failed by itself
#  and not unfail when a parent SRLG unfails


class PerformanceModel(_MasterModel):
    """
    A network model object consisting of the following base components:
        - Interface objects (set): layer 3 Node interfaces.  Interfaces have a
          'capacity' attribute that determines how much traffic it can carry.
          Note: Interfaces are matched into Circuit objects based on the
          interface circuit_ids --> A pair of Interfaces with the same circuit_id
          value get matched into a Circuit
        - Node objects (set): vertices on the network (aka 'layer 3 devices')
          that contain Interface objects.  Nodes are connected to each other
          via a pair of matched Interfaces (Circuits)
        - Demand objects (set): traffic loads on the network.  Each demand starts
          from a source node and transits the network to a destination node.
          A demand also has a magnitude, representing how much traffic it
          is carrying.  The demand's magnitude will apply against each
          interface's available capacity
        - RSVP LSP objects (set): RSVP LSPs in the Model
        - Circuit objects are created by matching Interface objects
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

        super().__init__(interface_objects, node_objects, demand_objects, rsvp_lsp_objects)

    def __repr__(self):
        return 'PerformanceModel(Interfaces: %s, Nodes: %s, Demands: %s, ' \
               'RSVP_LSPs: %s)' % (len(self.interface_objects), len(self.node_objects),
                                   len(self.demand_objects), len(self.rsvp_lsp_objects))

    def add_network_interfaces_from_list(self, network_interfaces):
        """
        A tool that reads network interface info and updates an *existing* model.
        Intended to be used from CLI/interactive environment
        Interface info must be a list of dicts and in format like below example.

        Example::

            network_interfaces = [
            {'name':'A-to-B', 'cost':4,'capacity':100, 'node':'A',
            'remote_node': 'B', 'circuit_id': 1, 'failed': False},
            {'name':'A-to-Bv2', 'cost':40,'capacity':150, 'node':'A',
            'remote_node': 'B', 'circuit_id': 2, 'failed': False},
            {'name':'A-to-C', 'cost':1,'capacity':200, 'node':'A',
            'remote_node': 'C', 'circuit_id': 3, 'failed': False},]

        :param network_interfaces: python list of attributes for Interface objects
        :return: self with new Interface objects
        """

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

        # Make dict to hold interface data, each entry has the following
        # format:
        # {'lsps': [], 'reserved_bandwidth': 0}
        int_info = self._make_int_info_dict()

        # Interface reserved bandwidth error sets
        int_res_bw_too_high = set([])
        int_res_bw_sum_error = set([])

        error_data = []  # list of all errored checks

        for interface in iter(self.interface_objects):  # pragma: no cover
            self._reserved_bw_error_checks(int_info, int_res_bw_sum_error, int_res_bw_too_high, interface)

        # If creation of circuits returns a dict, there are problems
        if isinstance(circuits, dict):  # pragma: no cover
            error_data.append({'ints_w_no_remote_int': circuits['data']})

        # Append any failed checks to error_data
        if int_res_bw_too_high:  # pragma: no cover
            error_data.append({'int_res_bw_too_high': int_res_bw_too_high})

        if int_res_bw_sum_error:  # pragma: no cover
            error_data.append({'int_res_bw_sum_error': int_res_bw_sum_error})

        # Validate there are no duplicate interfaces
        unique_interfaces_per_node = self._unique_interface_per_node()

        # Log any duplicate interfaces on a node
        if not unique_interfaces_per_node:  # pragma: no cover
            error_data.append(unique_interfaces_per_node)

        # Log any Nodes with IGP shortcuts enabled
        igp_shortcut_nodes = [node for node in self.node_objects if node.igp_shortcuts_enabled is True]
        if igp_shortcut_nodes:
            igp_shortcut_key = 'igp_shortcuts_enabled not allowed in PerformanceModel, but present on these Nodes'
            error_data.append({igp_shortcut_key: igp_shortcut_nodes})

        # Make validate_model() check for matching failed statuses
        # on the interfaces and matching interface capacity
        circuits_with_mismatched_interface_capacity = []
        for ckt in iter(self.circuit_objects):
            self._validate_circuit_interface_capacity(circuits_with_mismatched_interface_capacity, ckt)

        if circuits_with_mismatched_interface_capacity:
            int_status_error_dict = {
                'circuits_with_mismatched_interface_capacity':
                circuits_with_mismatched_interface_capacity
            }
            error_data.append(int_status_error_dict)

        # Look for multiple links between nodes (not allowed in Model)
        if len(self.multiple_links_between_nodes()) > 0:
            multiple_links_between_nodes = {
                'multiple links between nodes detected; not allowed in Model object'
                '(use Parallel_Link_Model)': self.multiple_links_between_nodes()
            }

            error_data.append(multiple_links_between_nodes)

        srlg_errors = self.validate_srlg_nodes()

        if len(srlg_errors) > 0:
            error_data.append(srlg_errors)

        # Verify no duplicate nodes
        node_names = {node.name for node in self.node_objects}
        if (len(self.node_objects)) != (len(node_names)):  # pragma: no cover
            node_dict = {'len_node_objects': len(self.node_objects),
                         'len_node_names': len(node_names)}
            error_data.append(node_dict)

        # Read error_data
        if error_data:
            message = 'network interface validation failed, see returned data'
            pprint(message)
            pprint(error_data)
            raise ModelException((message, error_data))
        else:
            return self

    def validate_srlg_nodes(self):
        """
        Validate that Nodes in each SRLG have the SRLG in their srlgs set.
        srlg_errors is a dict of node names as keys and a list of SRLGs that node is
        a member of in the model but that the SRLG is not in node.srlgs
        :return: dict where keys are Node names and values are lists of SRLG names;
        each value will be a single list of SRLG names missing that Node in the
        SRLG node set
        """

        srlg_errors = {}
        for srlg in self.srlg_objects:  # pragma: no cover  # noqa  # TODO - perhaps cover this later in unit testing
            nodes_in_srlg_but_srlg_not_in_node_srlgs = [node for node in srlg.node_objects if srlg not in node.srlgs]
            for node in nodes_in_srlg_but_srlg_not_in_node_srlgs:
                try:
                    srlg_errors[node.name].append(srlg.name)
                except KeyError:
                    srlg_errors[node.name] = []
        return srlg_errors

    def update_simulation(self):
        """
        Updates the simulation state; this needs to be run any time there is
        a change to the state of the Model, such as failing an interface, adding
        a Demand, adding/removing and LSP, etc.
        This call does not carry forward any state from the previous simulation
        results.
        """

        self._parallel_lsp_groups = {}  # Reset the attribute

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
        non_failed_interfaces_model = PerformanceModel(non_failed_interfaces,
                                                       available_nodes, self.demand_objects,
                                                       self.rsvp_lsp_objects)

        # Reset the reserved_bandwidth, traffic on each interface
        for interface in iter(self.interface_objects):
            interface.reserved_bandwidth = 0
            interface.traffic = 0

        for lsp in iter(self.rsvp_lsp_objects):
            lsp.path = 'Unrouted'

        for demand in iter(self.demand_objects):
            demand.path = 'Unrouted'

        time_before_lsp_load = datetime.now()
        print("Routing the LSPs . . . ")
        # Route the RSVP LSPs
        self = self._route_lsps()
        lsp_load_time = datetime.now() - time_before_lsp_load
        print("LSPs routed (if present) in {}; routing demands now . . .".format(lsp_load_time))
        # Route the demands
        demand_load_start_time = datetime.now()
        self = self._route_demands(non_failed_interfaces_model)
        demand_load_time = datetime.now() - demand_load_start_time
        print("Demands routed in {}; validating model . . . ".format(demand_load_time))

        self.validate_model()

    def _route_demands(self, model):
        """
        Routes demands in input 'model'

        :param model: input 'model' parameter object (may be different from self)
        :return: model with routed demands
        """

        G = self._make_weighted_network_graph(include_failed_circuits=False)

        for demand in model.demand_objects:
            demand.path = []

            # Find all LSPs that can carry the demand from source to dest:
            key = "{}-{}".format(demand.source_node_object.name, demand.dest_node_object.name)
            try:
                lsp_list = [lsp for lsp in self.parallel_lsp_groups()[key] if 'Unrouted' not in lsp.path]
            except KeyError:
                lsp_list = []

            # Check for manually assigned metrics
            if lsp_list:
                min_lsp_metric = min(lsp.effective_metric(self) for lsp in lsp_list)
                for lsp in lsp_list:
                    if lsp.effective_metric(self) == min_lsp_metric:
                        demand.path.append(lsp)

            if demand.path == []:
                src = demand.source_node_object.name
                dest = demand.dest_node_object.name

                # Shortest path in networkx multidigraph
                try:
                    nx_sp = list(nx.all_shortest_paths(G, src, dest, weight='cost'))
                except nx.exception.NetworkXNoPath:
                    # There is no path, demand.path = 'Unrouted'
                    demand.path = 'Unrouted'
                    continue

                # all_paths is list of paths from source to destination
                all_paths = self.convert_graph_path_to_model_path(nx_sp)

                demand.path = all_paths

        self._update_interface_utilization()

        return self

    def _determine_lsp_state_info(self, lsps, traff_on_each_group_lsp):
        """
        Determine LSP's specific path and reserved bandwidth; also consume
        reserved bandwidth on transited Interfaces

        :param lsps: List of parallel LSPs (LSPs with common source/dest nodes)
        :param traff_on_each_group_lsp: How much traffic each LSP should attempt
        to carry
        :return: None; determines path and reserved bandwidth for each LSP in lsps
        and also consumes reservable bandwidth on each Interface each LSP transits
        """

        for lsp in lsps:
            # Check to see if configured_setup_bandwidth is set; if so,
            # set reserved_bandwidth and setup_bandwidth equal to
            # configured_setup_bandwidth value
            if lsp.configured_setup_bandwidth is None:
                lsp.reserved_bandwidth = traff_on_each_group_lsp
                lsp.setup_bandwidth = traff_on_each_group_lsp
            else:
                lsp.reserved_bandwidth = lsp.configured_setup_bandwidth
                lsp.setup_bandwidth = lsp.configured_setup_bandwidth

            G = self._make_weighted_network_graph(include_failed_circuits=False, rsvp_required=True,
                                                  needed_bw=lsp.setup_bandwidth)

            lsp.path = {}

            # Get shortest paths in networkx multidigraph; for DiGraph, only edge names will be
            # in returned paths (the rest of the edge data will not)
            try:
                nx_sp = list(nx.all_shortest_paths(G, lsp.source_node_object.name, lsp.dest_node_object.name,
                                                   weight='cost'))
            except nx.exception.NetworkXNoPath:
                # There is no path; path = 'Unrouted'
                lsp.path = 'Unrouted'
                lsp.reserved_bandwidth = 'Unrouted'
                continue

            # Convert node hop by hop paths from G into Interface-based paths
            all_paths = self.convert_graph_path_to_model_path(nx_sp)

            # # all_paths may have hops between nodes that can take different Interfaces;
            # # normalize those hops that could transit any of multiple Interfaces into
            # # distinct, unique possible paths
            # candidate_path_info = self._normalize_multigraph_paths(all_paths)

            # Candidate paths with enough reservable bandwidth
            candidate_path_info_w_reservable_bw = []

            # Determine which candidate paths have enough reservable bandwidth
            for path in all_paths:
                if min([interface.reservable_bandwidth for interface in path]) >= lsp.setup_bandwidth:
                    candidate_path_info_w_reservable_bw.append(path)

            # If multiple lowest_metric_paths, find those with fewest hops
            if len(candidate_path_info_w_reservable_bw) == 0:
                lsp.path = 'Unrouted'
                lsp.reserved_bandwidth = 'Unrouted'
                continue

            elif len(candidate_path_info_w_reservable_bw) > 1:
                fewest_hops = min([len(path) for path in candidate_path_info_w_reservable_bw])
                lowest_hop_count_paths = [path for path in candidate_path_info_w_reservable_bw
                                          if len(path) == fewest_hops]
                if len(lowest_hop_count_paths) > 1:
                    new_path = random.choice(lowest_hop_count_paths)
                else:
                    new_path = lowest_hop_count_paths[0]
            else:
                new_path = candidate_path_info_w_reservable_bw[0]

            # Change LSP path into more verbose form and set LSP's path
            self._add_lsp_path_data(lsp, new_path)

            for interface in [interface for interface in lsp.path['interfaces'] if lsp.path != 'Unrouted']:
                interface.reserved_bandwidth += lsp.reserved_bandwidth

    def convert_graph_path_to_model_path(self, nx_sp):
        """
        Converts list of Node names on path to list of Interfaces in Model on path.  This
        can only be used on MultiGraph paths because MultiGraphs only support a single edge
        (Circuit) between Node objects.

        :param nx_sp: List of Node name hops on path
        Example::

            [['A', 'B', 'D'], ['A', 'B', 'G', 'D']]

        :return: List of Interface objects on path

        Example::

            For the ['A', 'B', 'D'] path above, the converted path would be

                [Interface(name = 'A-to-B', cost = 20, capacity = 125.0, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = None),
                Interface(name = 'B-to-D', cost = 20, capacity = 125.0, node_object = Node('B'),
                remote_node_object = Node('D'), circuit_id = None)]

        """
        all_paths = []
        for nx_graph_path in nx_sp:
            model_path = []
            for hop in nx_graph_path:
                current_hop_index = nx_graph_path.index(hop)
                next_hop_index = current_hop_index + 1
                if next_hop_index < len(nx_graph_path):
                    next_hop = nx_graph_path[next_hop_index]
                    interface = self.get_interface_object_from_nodes(hop, next_hop)
                    model_path.append(interface)
            all_paths.append(model_path)
        return all_paths

    def _make_weighted_network_graph(self, include_failed_circuits=True, needed_bw=0, rsvp_required=False):
        """
        Returns a networkx weighted networkx multidigraph object from
        the input Model object

        :param include_failed_circuits: include interfaces from currently failed
        circuits in the graph?
        :param needed_bw: how much reservable_bandwidth is required?
        :param rsvp_required: True|False; only consider rsvp_enabled interfaces?

        :return: networkx multidigraph with edges that conform to the needed_bw and
        rsvp_required parameters
        """

        G = nx.DiGraph()

        # Get all the edges that meet 'failed' and 'reservable_bw' criteria
        if include_failed_circuits is False:
            considered_interfaces = (interface for interface in self.interface_objects
                                     if (interface.failed is False and
                                         interface.reservable_bandwidth >= needed_bw))
        elif include_failed_circuits is True:
            considered_interfaces = (interface for interface in self.interface_objects
                                     if interface.reservable_bandwidth >= needed_bw)

        if rsvp_required is True:
            edge_names = ((interface.node_object.name,
                           interface.remote_node_object.name,
                           {'cost': interface.cost, 'interface': interface, 'circuit_id': interface.circuit_id})
                          for interface in considered_interfaces
                          if interface.rsvp_enabled is True)
        else:
            edge_names = ((interface.node_object.name,
                           interface.remote_node_object.name,
                           {'cost': interface.cost, 'interface': interface, 'circuit_id': interface.circuit_id})
                          for interface in considered_interfaces)

        # Add edges to networkx DiGraph
        G.add_edges_from(edge_names)

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

        return G

    def _make_circuits(self, return_exception=True, include_failed_circuits=True):
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

        # Set interface object in_ckt = False and baseline the circuit_id
        for interface in iter(self.interface_objects):
            interface.in_ckt = False
        circuit_id_number = 1
        circuits = set([])

        # Using the paired interfaces (source_node, dest_node) pairs from G,
        # get the corresponding interface objects from the model to create
        # the circuit object
        for interface in iter(paired_interfaces):
            # Get each interface from model for each
            int1 = self.get_interface_object_from_nodes(interface[0],
                                                        interface[1])
            int2 = self.get_interface_object_from_nodes(interface[1],
                                                        interface[0])

            if int1.in_ckt is False and int2.in_ckt is False:
                # Mark interface objects as in_ckt = True
                int1.in_ckt = True
                int2.in_ckt = True

                # Add circuit_id to interface objects
                int1.circuit_id = circuit_id_number
                int2.circuit_id = circuit_id_number
                circuit_id_number += 1

                ckt = Circuit(int1, int2)
                circuits.add(ckt)

        # Find any interfaces that don't have counterpart
        exception_ints_not_in_ckt = [(local_node_name, remote_node_name, data)
                                     for (local_node_name, remote_node_name, data) in
                                     G.edges(data=True) if not (G.has_edge(remote_node_name, local_node_name))]

        if exception_ints_not_in_ckt:
            exception_msg = ('WARNING: These interfaces were not matched '
                             'into a circuit {}'.format(exception_ints_not_in_ckt))
            if return_exception:
                raise ModelException(exception_msg)
            else:
                return {'data': exception_ints_not_in_ckt}

        self.circuit_objects = circuits

    def get_interface_object_from_nodes(self, local_node_name, remote_node_name):
        """
        Returns a list of Interface objects with the specified
        local and remote node names.

        :param local_node_name:
        :param remote_node_name:
        :return: Interface object with specified local node and remote node names
        """
        for interface in iter(self.interface_objects):
            if interface.node_object.name == local_node_name and \
                    interface.remote_node_object.name == remote_node_name:
                return interface

    def add_circuit(self, node_a_object, node_b_object, node_a_interface_name,
                    node_b_interface_name, cost_intf_a=1, cost_intf_b=1,
                    capacity=1000, failed=False, circuit_id=None):
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
        :param circuit_id: Optional.  Will be auto-assigned unless specified
        :return: Model with new Circuit comprised of 2 new Interfaces
        """

        if circuit_id is None:
            circuit_ids = self.all_interface_circuit_ids
            circuit_id = 1 if len(circuit_ids) == 0 else max(circuit_ids) + 1
        int_a = Interface(node_a_interface_name, cost_intf_a, capacity,
                          node_a_object, node_b_object, circuit_id)
        int_b = Interface(node_b_interface_name, cost_intf_b, capacity,
                          node_b_object, node_a_object, circuit_id)

        existing_int_keys = {interface._key for interface in self.interface_objects}

        if int_a._key in existing_int_keys:
            raise ModelException("interface {} on node {} already exists in model".format(int_a, node_a_object))
        elif int_b._key in existing_int_keys:
            raise ModelException("interface {} on node {} already exists in model".format(int_b, node_b_object))

        self.interface_objects.add(int_a)
        self.interface_objects.add(int_b)

        self.validate_model()

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
        :return: Return the path(s) in dictionary form:
        Example::

            >>> model.get_all_paths_reservable_bw('A', 'B', False, 5, 10)
            {'path': [
            [Interface(name = 'A-to-D', cost = 40, capacity = 20.0,
            node_object = Node('A'), remote_node_object = Node('D'), circuit_id = 2),
            Interface(name = 'D-to-B', cost = 20, capacity = 125.0, node_object = Node('D'),
            remote_node_object = Node('B'), circuit_id = 7)],
            [Interface(name = 'A-to-D', cost = 40, capacity = 20.0, node_object = Node('A'),
            remote_node_object = Node('D'), circuit_id = 2),
            Interface(name = 'D-to-G', cost = 10, capacity = 100.0, node_object = Node('D'),
            remote_node_object = Node('G'), circuit_id = 8),
            Interface(name = 'G-to-B', cost = 10, capacity = 100.0, node_object = Node('G'),
            remote_node_object = Node('B'), circuit_id = 9)]
            ]}

        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph(include_failed_circuits=include_failed_circuits, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = {'path': []}
        # Find the simple paths in G between source and dest
        digraph_all_paths = nx.all_simple_paths(G, source_node_name, dest_node_name, cutoff=cutoff)

        try:
            for path in digraph_all_paths:
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
        :return: Return the shortest path in dictionary form

            Example:
                 shortest_path = {'path': [list of shortest path routes], 'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph(include_failed_circuits=False, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = {'path': [], 'cost': None}
        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(G, source_node_name,
                                                       dest_node_name,
                                                       weight='cost')

        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path)
                converted_path['path'].append(model_path)
                converted_path['cost'] = nx.shortest_path_length(G, source_node_name, dest_node_name, weight='cost')

            return converted_path
        except BaseException:
            return converted_path

    def get_shortest_path_for_routed_lsp(self, source_node_name, dest_node_name, lsp, needed_bw):
        """
        For a source and dest node name pair, find the shortest path(s) with at
        least needed_bw available for an LSP that is already routed.  This takes into account
        reserved bandwidth on the Interfaces the LSP already transits, allowing the bandwidth
        reserved by the LSP to be considered for reservation on any new path for the input LSP
        Return the shortest path in dictionary form:
        shortest_path = {'path': [list of shortest path routes], 'cost': path_cost}

        :param source_node_name: name of source node
        :param dest_node_name: name of destination node
        :param lsp: LSP object
        :param needed_bw: reserved bandwidth for LSPs
        :return: dict {'path': [list of lists, each list a shortest path route], 'cost': path_cost}

        Example::
            >>> lsp
            RSVP_LSP(source = B, dest = C, lsp_name = 'lsp_b_c_1')
            >>> path = model.get_shortest_path_for_routed_lsp('A', 'D', lsp, 10)
            >>> path
            {'path': [[Interface(name = 'A-to-D', cost = 40, capacity = 20.0, node_object = Node('A'),
            remote_node_object = Node('D'), circuit_id = 3)]], 'cost': 40}


        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph_routed_lsp(lsp, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = {'path': [], 'cost': None}
        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(G, source_node_name, dest_node_name, weight='cost')
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
        The corresponding model style path would be

        Example::

            [Interface(name = 'A-to-B', cost = 20, capacity = 125, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 9),
            Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 6),
            Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                remote_node_object = Node('D'), circuit_id = 2),
            Interface(name = 'D-to-F', cost = 10, capacity = 300, node_object = Node('D'),
                remote_node_object = Node('F'), circuit_id = 1)]

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

    def _make_weighted_network_graph_routed_lsp(self, lsp, needed_bw=0):
        """
        Looks for a new path with needed_bw reservable bandwidth for an RSVP LSP
        that is currently routed.
        Returns a networkx weighted network directional graph from the input Model object.
        Considers edges with needed_bw of reservable_bandwidth and also takes into account
        reserved_bandwidth by the lsp on Interfaces in the existing LSP path

        :param lsp: RSVP LSP that is currently routed
        :param needed_bw: how much bandwidth is needed for the RSVP LSP's new path
        :return: networkx DiGraph with eligible edges
        """
        G = nx.DiGraph()

        # The Interfaces that the lsp is routed over currently
        lsp_path_interfaces = lsp.path['interfaces']

        # Since this is for a routed LSP, rsvp_enabled must be True and interface must
        # not be failed
        eligible_interface_generator = (interface for interface in self.interface_objects if
                                        interface.failed is False and interface.rsvp_enabled is True)

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
    def load_model_file(cls, data_file):    # TODO - make sure doc strings for this come out well in docs dir
        """
        Opens a network_modeling data file and returns a model containing
        the info in the data file.  The data file must be of the appropriate
        format to produce a valid model.  This cannot be used to open
        multiple models in a single python instance - there may be
        unpredictable results in the info in the models.
        The format for the file must be a tab separated value file.
        This docstring you are reading may not display the table info
        explanations/examples below correctly on https://pyntm.readthedocs.io/en/latest/api.html.
        Recommend either using help(Model.load_model_file) at the python3 cli or
        looking at one of the sample model data_files in github:
        https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples/sample_network_model_file.csv
        https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples/lsp_model_test_file.csv
        The following headers must exist, with the following tab-column
        names beneath:

        INTERFACES_TABLE
        - node_object_name - name of node	where interface resides
        - remote_node_object_name	- name of remote node
        - name - interface name
        - cost - IGP cost/metric for interface
        - capacity - capacity
        - rsvp_enabled (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
        - percent_reservable_bandwidth (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this
        value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100

        Note - The existence of Nodes will be inferred from the INTERFACES_TABLE.
        So a Node created from an Interface does not have to appear in the
        NODES_TABLE unless you want to add additional attributes for the Node
        such as latitude/longitude

        NODES_TABLE -
        - name - name of node
        - lon	- longitude (or y-coordinate) (optional)
        - lat - latitude (or x-coordinate) (optional)

        Note - The NODES_TABLE is present for 2 reasons:
        - to add a Node that has no interfaces
        - and/or to add additional attributes for a Node inferred from
        the INTERFACES_TABLE

        DEMANDS_TABLE
        - source - source node name
        - dest - destination node name
        - traffic	- amount of traffic on demand
        - name - name of demand

        RSVP_LSP_TABLE
        - source - LSP's source node
        - dest - LSP's destination node
        - name - name of LSP
        - configured_setup_bw (optional) - if LSP has a fixed, static configured setup bandwidth, place that static value here,
        if LSP is auto-bandwidth, then leave this blank for the LSP
        - manual_metric (optional) - manually assigned metric for LSP, if not using default metric from topology
        shortest path


        Functional model files can be found in this directory in
        https://github.com/tim-fiola/network_traffic_modeler_py3/tree/master/examples
        Here is an example of a data file:

        Example::

            INTERFACES_TABLE
            node_object_name	remote_node_object_name	name	cost	capacity    rsvp_enabled    percent_reservable_bandwidth  # noqa E501
            A	B	A-to-B	4	100
            B	A	B-to-A	4	100

            NODES_TABLE
            name	lon	lat
            A	50	0
            B	0	-50

            DEMANDS_TABLE
            source	dest	traffic	name
            A	B	80	dmd_a_b_1

            RSVP_LSP_TABLE
            source	dest	name    configured_setup_bw manual_metric
            A	B	lsp_a_b_1   10  15
            A	B	lsp_a_b_2       10

        :param data_file: file with model info
        :return: Model object
        """
        # TODO - allow user to add user-defined columns in NODES_TABLE and add that as an attribute to the Node
        # TODO - add support for SRLGs

        interface_set = set()
        node_set = set()
        demand_set = set()
        lsp_set = set()

        # Open the file with the data, read it, and split it into lines
        with open(data_file, 'r', encoding='utf-8-sig') as f:
            data = f.read()

        lines = data.splitlines()

        # Define the Interfaces from the data and extract the presence of
        # Nodes from the Interface data
        int_info_begin_index = lines.index('INTERFACES_TABLE') + 2
        int_info_end_index = find_end_index(int_info_begin_index, lines)
        interface_set, node_set = cls._extract_interface_data_and_implied_nodes(int_info_begin_index,
                                                                                int_info_end_index, lines)

        # Define the explicit nodes info from the file
        nodes_info_begin_index = lines.index('NODES_TABLE') + 2
        nodes_info_end_index = find_end_index(nodes_info_begin_index, lines)
        node_lines = lines[nodes_info_begin_index:nodes_info_end_index]
        for node_line in node_lines:
            cls._add_node_from_data(demand_set, interface_set, lsp_set, node_line, node_set)

        # Define the demands info
        demands_info_begin_index = lines.index('DEMANDS_TABLE') + 2
        demands_info_end_index = find_end_index(demands_info_begin_index, lines)
        # There may or may not be LSPs in the model, so if there are not,
        # set the demands_info_end_index as the last line in the file
        if not demands_info_end_index:
            demands_info_end_index = len(lines)

        demands_lines = lines[demands_info_begin_index:demands_info_end_index]

        for demand_line in demands_lines:
            try:
                cls._add_demand_from_data(demand_line, demand_set, lines, node_set)
            except ModelException as e:
                err_msg = e.args[0]
                raise ModelException(err_msg)

        # Define the LSP info (if present)
        try:
            lsp_info_begin_index = lines.index('RSVP_LSP_TABLE') + 2
            cls._add_lsp_from_data(lsp_info_begin_index, lines, lsp_set, node_set)
        except ValueError:
            print("RSVP_LSP_TABLE not in file; no LSPs added to model")
        except ModelException as e:
            err_msg = e.args[0]
            raise ModelException(err_msg)

        return cls(interface_set, node_set, demand_set, lsp_set)

    @classmethod
    def _extract_interface_data_and_implied_nodes(cls, int_info_begin_index, int_info_end_index, lines):
        """
        Extracts interface data from lines and adds Interface objects to a set.
        Also extracts the implied Nodes from the Interfaces and adds those Nodes to a set.

        :param int_info_begin_index: Index position in lines where interface info begins
        :param int_info_end_index:  Index position in lines where interface info ends
        :param lines: lines of data describing a Model objects
        :return: set of Interface objects, set of Node objects created from lines
        """

        interface_set = set()
        node_set = set()
        interface_lines = lines[int_info_begin_index:int_info_end_index]
        # Add the Interfaces to a set
        for interface_line in interface_lines:
            # Read interface characteristics
            if len(interface_line.split('\t')) == 5:
                node_name, remote_node_name, name, cost, capacity = interface_line.split('\t')
                rsvp_enabled_bool = True
                percent_reservable_bandwidth = 100
            elif len(interface_line.split('\t')) == 6:
                node_name, remote_node_name, name, cost, capacity, rsvp_enabled = interface_line.split('\t')
                if rsvp_enabled in [True, 'T', 'True', 'true']:
                    rsvp_enabled_bool = True
                else:
                    rsvp_enabled_bool = False
                percent_reservable_bandwidth = 100
            elif len(interface_line.split('\t')) >= 7:
                node_name, remote_node_name, name, cost, capacity, \
                    rsvp_enabled, percent_reservable_bandwidth = interface_line.split('\t')
                if rsvp_enabled in [True, 'T', 'True', 'true']:
                    rsvp_enabled_bool = True
                else:
                    rsvp_enabled_bool = False
            else:
                msg = ("node_name, remote_node_name, name, cost, and capacity "
                       "must be defined for line {}, line index {}".format(interface_line,
                                                                           lines.index(interface_line)))
                raise ModelException(msg)

            new_interface = Interface(name, int(cost), float(capacity), Node(node_name), Node(remote_node_name),
                                      None, rsvp_enabled_bool, float(percent_reservable_bandwidth))

            if new_interface._key not in {
                interface._key for interface in interface_set
            }:
                interface_set.add(new_interface)
            else:
                print("{} already exists in model; disregarding line {}".format(new_interface,
                                                                                lines.index(interface_line)))

            # Derive Nodes from the Interface data
            if node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.node_object)
            if remote_node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.remote_node_object)

        return interface_set, node_set

    def _update_interface_utilization(self):
        """Updates each interface's utilization; returns Model object with
        updated interface utilization."""

        # In the model, in an interface is failed, set the traffic attribute
        # to 'Down', otherwise, initialize the traffic to zero
        for interface_object in self.interface_objects:
            interface_object.traffic = 'Down' if interface_object.failed else 0.0
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
            # Is there a parallel_lsp_group that matches the source and dest for the demand_object?
            key = '{}-{}'.format(demand_object.source_node_object.name, demand_object.dest_node_object.name)

            # Find the routed LSPs that can carry the demand
            try:
                candidate_lsps_for_demand = self.parallel_lsp_groups()[key]
                min_metric = min(
                    lsp.effective_metric(self)
                    for lsp in candidate_lsps_for_demand
                    if 'Unrouted' not in lsp.path)
                lsps_for_demand = [lsp for lsp in candidate_lsps_for_demand if
                                   lsp.effective_metric(self) == min_metric and 'Unrouted' not in lsp.path]
            except (KeyError, ValueError):
                # If there is no LSP group that matches the demand source/dest (KeyError) or there are no routed
                # LSPs for the demand (ValueError), then set lsps_for_demand to empty list
                lsps_for_demand = []

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

            # If demand_object is not taking LSPs end to end, IGP route it, using hop by hop ECMP
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

    def _demand_traffic_per_int(self, demand):
        """
        Given a Demand object, return the (key, value) pairs for how much traffic each
        Interface gets from the routing of the traffic load over Model Interfaces.

        : demand: Demand object
        : return: dict of (Interface: <traffic from demand> ) k, v pairs

        Example::

            The interface from node B to E (name='B-to-E') below has 8.0 units of
            traffic from 'demand'; the interface from A to B has 12.0, etc.

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

    def multiple_links_between_nodes(self):
        """
        Ensures there is no more than a single interface facing a
        given remote node (that there are no parallel interfaces
        between nodes)

        :return: a list of parallel interfaces; if
        there are no parallel interfaces, the list is empty
        """

        connected_nodes_list = [(interface.node_object.name + '-' + interface.remote_node_object.name) for interface
                                in self.interface_objects]

        connected_nodes_set = set(connected_nodes_list)

        # If there are parallel links between nodes, create a list of the
        # parallel links, sort it, and return the list
        if len(connected_nodes_list) != len(connected_nodes_set):
            parallel_links = [connection for connection in connected_nodes_list if
                              connected_nodes_list.count(connection) > 1]
            parallel_links.sort()

            return parallel_links

        else:
            return []


class Model(PerformanceModel):
    """
    This is the legacy Model class, now a subclass of the more aptly named
    PerformanceModel class.

    This has been added to attempt to keep any legacy code, written in pyNTM 1.6
    or earlier, from breaking.
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

        super().__init__(interface_objects, node_objects, demand_objects, rsvp_lsp_objects)
