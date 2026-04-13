"""
Unified network model class for pyNTM.

This is the single model class that supports all pyNTM features:
  - Multiple Circuits (parallel links) between layer 3 Nodes
  - RSVP LSPs with bandwidth reservation and resignaling
  - IGP shortcuts for RSVP LSPs
  - SRLG (Shared Risk Link Group) support

The former FlexModel and PerformanceModel classes are now aliases for this class.
Both legacy class names are available as aliases for backward compatibility.
"""

from datetime import datetime
from pprint import pprint

import itertools
import networkx as nx
import random

from .circuit import Circuit
from .interface import Interface
from .exceptions import ModelException
from .rsvp import RSVP_LSP
from .utilities import find_end_index
from .node import Node
from collections import defaultdict
from .srlg import SRLG
from .demand import Demand


# TODO - call to analyze model for Unrouted LSPs and LSPs not on shortest path
# TODO - add support for SRLGs in load_model_file
# TODO - add attribute for Node/Interface whereby an object can be failed by itself
#  and not unfail when a parent SRLG unfails


class Model(object):
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

        - Circuit objects are created by matching Interface objects using common circuit_id

    """

    def __init__(
        self,
        interface_objects=set(),
        node_objects=set(),
        demand_objects=set(),
        rsvp_lsp_objects=set(),
    ):
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

        simulation_data = {
            "Number of routed LSPs carrying Demands": "TBD",
            "Number of routed LSPs with no Demands": "TBD",
            "Number of Demands riding LSPs": "TBD",
            "Number of Demands not riding LSPs": "TBD",
            "Number of unrouted LSPs": "TBD",
            "Number of unrouted Demands": "TBD",
            "routed LSPs with no demands generator": "TBD",
            "routed LSPs with demands generator": "TBD",
            "demands riding LSPs generator": "TBD",
        }

        # Find LSPs with and without demands
        lsps_routed_no_demands = [
            lsp
            for lsp in self.rsvp_lsp_objects
            if lsp.path != "Unrouted" and lsp.demands_on_lsp(self) == []
        ]

        lsps_routed_with_demands = [
            lsp
            for lsp in self.rsvp_lsp_objects
            if lsp.path != "Unrouted" and lsp.demands_on_lsp(self) != []
        ]

        # Find demands riding LSPs
        dmds_riding_lsps = set()

        # Find unrouted LSPs
        for dmd in iter(self.demand_objects):
            for path in dmd.path:
                for object in path:
                    if isinstance(object, RSVP_LSP):
                        dmds_riding_lsps.add(dmd)
        unrouted_lsps = [lsp for lsp in self.rsvp_lsp_objects if lsp.path == "Unrouted"]

        # Update the quantities in simulation_data
        simulation_data["Number of routed LSPs carrying Demands"] = len(
            lsps_routed_with_demands
        )
        simulation_data["Number of routed LSPs with no Demands"] = len(
            lsps_routed_no_demands
        )
        simulation_data["Number of Demands riding LSPs"] = len(dmds_riding_lsps)
        simulation_data["Number of Demands not riding LSPs"] = len(
            self.demand_objects
        ) - len(dmds_riding_lsps)
        simulation_data["Number of unrouted LSPs"] = len(unrouted_lsps)
        simulation_data["Number of unrouted Demands"] = len(
            self.get_unrouted_demand_objects()
        )

        # Create generators to be returned
        dmds_riding_lsps_gen = iter(dmds_riding_lsps)
        lsps_routed_no_demands_gen = iter(lsps_routed_no_demands)
        lsps_routed_with_demands_gen = iter(lsps_routed_with_demands)

        # Update generators in simulation_data
        simulation_data["routed LSPs with no demands generator"] = (
            lsps_routed_no_demands_gen
        )
        simulation_data["routed LSPs with demands generator"] = (
            lsps_routed_with_demands_gen
        )
        simulation_data["demands riding LSPs generator"] = dmds_riding_lsps_gen

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
        int_info = {key: {"lsps": [], "reserved_bandwidth": 0} for key in keys}
        for lsp in (lsp for lsp in self.rsvp_lsp_objects if "Unrouted" not in lsp.path):
            for interface in lsp.path["interfaces"]:
                int_info[interface._key]["lsps"].append(lsp)
                int_info[interface._key]["reserved_bandwidth"] += round(
                    lsp.reserved_bandwidth, 1
                )
        return int_info

    def _validate_circuit_interface_capacity(
        self, circuits_with_mismatched_interface_capacity, ckt
    ):
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

    def _reserved_bw_error_checks(
        self, int_info, int_res_bw_sum_error, int_res_bw_too_high, interface
    ):
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
        if round(interface.reserved_bandwidth, 1) != round(
            int_info[interface._key]["reserved_bandwidth"], 1
        ):  # pragma: no cover  # noqa
            int_res_bw_sum_error.add(
                (interface, interface.reserved_bandwidth, tuple(interface.lsps(self)))
            )

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

            print(
                "Routing {} LSPs in parallel LSP group {}; {}/{}".format(
                    num_lsps_in_group, group, counter, len(parallel_lsp_groups)
                )
            )
            # Traffic each LSP in a parallel LSP group will carry; initialize
            traffic_in_demand_group = 0
            traff_on_each_group_lsp = 0

            try:
                # Get all demands that would ride the parallel LSP group
                dmds_on_lsp_group = parallel_demand_groups[group]

                traffic_in_demand_group = sum(
                    [dmd.traffic for dmd in dmds_on_lsp_group]
                )
                if traffic_in_demand_group > 0:
                    traff_on_each_group_lsp = traffic_in_demand_group / len(lsps)
            except KeyError:
                # LSPs with no demands will cause a KeyError in parallel_demand_groups[group]
                # since parallel_demand_group will have no entry for 'group'
                pass

            # Determine LSP's specific path and reserved bandwidth; also consume
            # reserved bandwidth on transited Interfaces
            self._determine_lsp_state_info(lsps, traff_on_each_group_lsp)

            routed_lsps_in_group = [lsp for lsp in lsps if lsp.path != "Unrouted"]

            # ##### Optimize the LSP group reserved bandwidth #####
            # If not all the LSPs in the group can route at the lowest (initial)
            # setup bandwidth, determine which LSPs can signal and for how much traffic
            if len(routed_lsps_in_group) != len(lsps) and len(routed_lsps_in_group) > 0:
                self._optimize_parallel_lsp_group_res_bw(
                    self, routed_lsps_in_group, traffic_in_demand_group
                )

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

        lsp.path = {
            "interfaces": path,
            "path_cost": path_cost,
            "baseline_path_reservable_bw": baseline_path_reservable_bw,
        }

    def _optimize_parallel_lsp_group_res_bw(
        self, input_model, routed_lsps_in_group, traffic_in_demand_group
    ):
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

            lsp_path_interfaces_before = lsp.path["interfaces"]
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
                for interface in lsp.path["interfaces"]:
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

        groups = defaultdict(list)
        for lsp in self.rsvp_lsp_objects:
            key = "{}-{}".format(lsp.source_node_object.name, lsp.dest_node_object.name)
            groups[key].append(lsp)

        self._parallel_lsp_groups = dict(groups)
        return self._parallel_lsp_groups

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

        groups = defaultdict(list)
        for dmd in self.demand_objects:
            key = "{}-{}".format(dmd.source_node_object.name, dmd.dest_node_object.name)
            groups[key].append(dmd)

        return dict(groups)

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
                " nodes have duplicate interface names {}".format(exception_interfaces)
            )

        else:
            return True

    @property
    def all_interface_circuit_ids(self):
        """
        Returns all interface circuit_ids
        """
        return {interface.circuit_id for interface in self.interface_objects}

    def add_demand(self, source_node_name, dest_node_name, traffic=0, name="none"):
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
            message = "{} already exists in demand_objects".format(added_demand)
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
            lsp_info = lsp_line.split("\t")
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

            new_lsp = RSVP_LSP(
                source_node,
                dest_node,
                name,
                configured_setup_bandwidth=configured_setup_bw,
                configured_manual_metric=manual_metric,
            )

            if new_lsp._key not in {lsp._key for lsp in lsp_set}:
                lsp_set.add(new_lsp)
            else:
                print(
                    "{} already exists in model; disregarding line {}".format(
                        new_lsp, lines.index(lsp_line)
                    )
                )

    @classmethod
    def _add_demand_from_data(cls, demand_line, demand_set, lines, node_set):
        """
        Adds Demand from line of data

        :param demand_line: line of data for demand
        :param demand_set: set of Demands in model
        :param lines: lines of data from input file
        :param node_set: set of Nodes from model

        """
        demand_info = demand_line.split("\t")
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
        demand_name = "none" if name == "" else name
        new_demand = Demand(source_node, dest_node, traffic, demand_name)
        if new_demand._key not in {dmd._key for dmd in demand_set}:
            demand_set.add(new_demand)
        else:
            print(
                "{} already exists in model; disregarding line {}".format(
                    new_demand, lines.index(demand_line)
                )
            )

    @classmethod
    def _add_node_from_data(
        cls, demand_set, interface_set, lsp_set, node_line, node_set
    ):
        node_info = node_line.split("\t")
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
            existing_node = cls(
                interface_set, node_set, demand_set, lsp_set
            ).get_node_object(node_name=node_name)
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
        interface_key_iterator = (
            interface._key for interface in self.interface_objects
        )

        if int_key not in (interface_key_iterator):
            raise ModelException("specified interface does not exist")

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

        ckts = [
            ckt
            for ckt in self.circuit_objects
            if interface in (ckt.interface_a, ckt.interface_b)
        ]

        return ckts[0]

    def get_failed_interface_objects(self):
        """
        Returns a list of all failed interfaces in self
        """
        return [
            interface for interface in iter(self.interface_objects) if interface.failed
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
            demand for demand in iter(self.demand_objects) if demand.path == "Unrouted"
        ]

    def change_interface_name(
        self, node_name, current_interface_name, new_interface_name
    ):
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
            ModelException("specified interface does not exist")

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
            ModelException("specified interface does not exist")

        # Find the remote interface
        remote_interface = interface_object.get_remote_interface(self)

        # Ensure local and remote nodes are failed == False and set reservable
        # bandwidth on each interface to interface.capacity
        if (
            self.get_node_object(interface_object.node_object.name).failed is False
            and self.get_node_object(remote_interface.node_object.name).failed is False
        ):
            remote_interface.failed = False
            remote_interface.reserved_bandwidth = 0
            interface_object.failed = False
            interface_object.reserved_bandwidth = 0
            self.validate_model()
        else:
            if raise_exception:
                message = (
                    "Local and/or remote node are failed; cannot have "
                    "unfailed interface on failed node."
                )
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

        int_object = [
            interface
            for interface in node_object.interfaces(self)
            if interface.name == interface_name
        ]
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
                self.unfail_interface(
                    remote_int.name, remote_int.node_object.name, False
                )

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
    def display_interface_status(self):  # pragma: no cover
        """Returns failed = True/False for each interface"""

        print("Node".ljust(12), "Interface".ljust(12), "Remote Node".ljust(12), end=" ")
        print("Failed".ljust(12))

        interface_iterator = iter(self.interface_objects)

        for interface in interface_iterator:
            print(
                interface.node_object.name.ljust(12), interface.name.ljust(12), end=" "
            )
            print(interface.remote_node_object.name.ljust(12), end=" ")
            print(str(interface.failed).ljust(12))

    def display_node_status(self):  # pragma: no cover
        """Returns failed = True/False for each node"""

        print("Node".ljust(12), "Failed".ljust(12))

        node_iterator = iter(self.node_objects)

        for node in node_iterator:
            print(node.name.ljust(12), str(node.failed).ljust(12))

    def display_interfaces_traffic(self):  # pragma: no cover
        """
        A human-readable(-ish) display of interfaces and traffic on each
        """

        print(
            "Node".ljust(12),
            "Interface".ljust(12),
            "Remote Node".ljust(12),
            "Traffic".ljust(12),
        )

        interface_iterator = iter(self.interface_objects)

        for interface in interface_iterator:
            print(
                interface.node_object.name.ljust(12), interface.name.ljust(12), end=" "
            )
            print(interface.remote_node_object.name.ljust(12), end=" ")
            print(repr(interface.traffic).ljust(12))

    def display_demand_paths(self):  # pragma: no cover
        """
        Displays each demand and its path(s) across the network
        """

        demand_iter = iter(self.demand_objects)

        for demand in demand_iter:
            print("demand._key is", demand._key)
            print("Demand has %s paths:" % (len(demand.path)))
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

        srlg_already_in_model = [
            srlg for srlg in self.srlg_objects if srlg.name == srlg_name
        ]

        if len(srlg_already_in_model) == 1:
            return srlg_already_in_model[
                0
            ]  # There will only be one SRLG with srlg_name
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
        nodes_to_fail_iterator = (
            node for node in self.node_objects if node in srlg_to_fail.node_objects
        )

        for node in nodes_to_fail_iterator:
            self.fail_node(node.name)

        # Find SRLG's Interfaces to fail
        interfaces_to_fail_iterator = (
            interface
            for interface in self.interface_objects
            if interface in srlg_to_fail.interface_objects
        )

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
        nodes_to_unfail_iterator = (
            node for node in self.node_objects if node in srlg_to_unfail.node_objects
        )

        # Node will stay failed if it's part of another SRLG that is still failed;
        # in that case, the unfail_node will create an exception; ignore that exception
        for node in nodes_to_unfail_iterator:
            try:
                self.unfail_node(node.name)
            except ModelException:
                pass

        # Find SRLG's Interfaces to unfail
        interfaces_to_unfail_iterator = (
            interface
            for interface in self.interface_objects
            if interface in srlg_to_unfail.interface_objects
        )

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
            raise ModelException(
                "SRLG with name {} already exists in Model".format(srlg_name)
            )
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
            message = "A node with name {} already exists in the model".format(
                node_object.name
            )
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
            message = "{} already exists in rsvp_lsp_objects".format(added_lsp)
            raise ModelException(message)
        self.rsvp_lsp_objects.add(added_lsp)

        self.validate_model()

    def get_demand_object(self, source_node_name, dest_node_name, demand_name="none"):
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
            if (
                demand.source_node_object.name == source_node_name
                and demand.dest_node_object.name == dest_node_name
                and demand.name == demand_name
            ):
                demand_to_return = demand
                return demand_to_return

        if demand_to_return is None:
            raise ModelException("no matching demand")

    def get_rsvp_lsp(self, source_node_name, dest_node_name, lsp_name="none"):
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
            msg = (
                "LSP with source node %s, dest node %s, and name %s "
                "does not exist in model" % (source_node_name, dest_node_name, lsp_name)
            )
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
            intf = Interface(
                interface["name"],
                interface["cost"],
                interface["capacity"],
                Node(interface["node"]),
                Node(interface["remote_node"]),
                interface["circuit_id"],
            )
            network_interface_objects.add(intf)

            # Check to see if the Interface's Node already exists, if not, add it
            node_names = [node.name for node in self.node_objects]
            if interface["node"] not in node_names:
                network_node_objects.add(Node(interface["node"]))
            if interface["remote_node"] not in node_names:
                network_node_objects.add(Node(interface["remote_node"]))

        return (network_interface_objects, network_node_objects)

    def __repr__(self):
        return "%s(Interfaces: %s, Nodes: %s, Demands: %s, RSVP_LSPs: %s)" % (
            self.__class__.__name__,
            len(self.interface_objects),
            len(self.node_objects),
            len(self.demand_objects),
            len(self.rsvp_lsp_objects),
        )

    def visualize(self, output_file=None, open_browser=True):
        """
        Open an interactive visualization of the current simulation state
        in the default web browser. Nodes are draggable, interfaces are
        color-coded by utilization, and demands/LSPs can be selected to
        trace their paths across the network.

        Must be called after update_simulation().

        :param output_file: Path to save the HTML file. If None, a temporary
            file is created.
        :param open_browser: If True, open the file in the default browser.
        :return: Path to the generated HTML file.

        Example::

            model = Model.load_model_file('network.csv')
            model.update_simulation()
            model.visualize()                        # opens in browser
            model.visualize('my_network.html')       # saves to specific path
        """
        from .interactive_visualization import InteractiveVisualization

        vis = InteractiveVisualization(self)
        return vis.create_visualization(
            output_file=output_file, open_browser=open_browser
        )

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

        new_interface_objects, new_node_objects = self._make_network_interfaces(
            network_interfaces
        )
        self.node_objects = self.node_objects.union(new_node_objects)
        self.interface_objects = self.interface_objects.union(new_interface_objects)
        self.validate_model()

    def validate_model(self):
        """
        Validates that data fed into the model creates a valid network model
        """

        # create circuits table, flags ints that are not part of a circuit
        circuits = self._make_circuits_multidigraph(return_exception=True)

        # Make dict to hold interface data, each entry has the following
        # format:
        # {'lsps': [], 'reserved_bandwidth': 0}
        int_info = self._make_int_info_dict()

        # Interface reserved bandwidth error sets
        int_res_bw_too_high = set([])
        int_res_bw_sum_error = set([])

        error_data = []  # list of all errored checks

        for interface in iter(self.interface_objects):  # pragma: no cover
            self._reserved_bw_error_checks(
                int_info, int_res_bw_sum_error, int_res_bw_too_high, interface
            )

        # If creation of circuits returns a dict, there are problems
        if isinstance(circuits, dict):  # pragma: no cover
            error_data.append({"ints_w_no_remote_int": circuits["data"]})

        # Append any failed checks to error_data
        if int_res_bw_too_high:  # pragma: no cover
            error_data.append({"int_res_bw_too_high": int_res_bw_too_high})

        if int_res_bw_sum_error:  # pragma: no cover
            error_data.append({"int_res_bw_sum_error": int_res_bw_sum_error})

        # Validate there are no duplicate interfaces
        unique_interfaces_per_node = self._unique_interface_per_node()

        # Log any duplicate interfaces on a node
        if not unique_interfaces_per_node:  # pragma: no cover
            error_data.append(unique_interfaces_per_node)

        # Make validate_model() check for matching failed statuses
        # on the interfaces and matching interface capacity
        circuits_with_mismatched_interface_capacity = []
        for ckt in iter(self.circuit_objects):
            self._validate_circuit_interface_capacity(
                circuits_with_mismatched_interface_capacity, ckt
            )

        if circuits_with_mismatched_interface_capacity:
            int_status_error_dict = {
                "circuits_with_mismatched_interface_capacity": circuits_with_mismatched_interface_capacity
            }
            error_data.append(int_status_error_dict)

        # Validate Nodes in each SRLG have the SRLG in their srlgs set.
        # srlg_errors is a dict of node names as keys and a list of SRLGs that node is
        # a member of in the model but that the SRLG is not in node.srlgs
        srlg_errors = {}

        for (
            srlg
        ) in (
            self.srlg_objects
        ):  # pragma: no cover  # noqa  # TODO - perhaps cover this later in unit testing
            nodes_in_srlg_but_srlg_not_in_node_srlgs = [
                node for node in srlg.node_objects if srlg not in node.srlgs
            ]
            for node in nodes_in_srlg_but_srlg_not_in_node_srlgs:
                try:
                    srlg_errors[node.name].append(srlg.name)
                except KeyError:
                    srlg_errors[node.name] = []

        if srlg_errors:
            error_data.append(srlg_errors)

        # Verify no duplicate nodes
        node_names = {node.name for node in self.node_objects}
        if (len(self.node_objects)) != (len(node_names)):  # pragma: no cover
            node_dict = {
                "len_node_objects": len(self.node_objects),
                "len_node_names": len(node_names),
            }
            error_data.append(node_dict)

        # Read error_data
        if error_data:
            message = "network interface validation failed, see returned data"
            pprint(message)
            pprint(error_data)
            raise ModelException((message, error_data))
        else:
            return self

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
        for interface_object in (
            interface_object
            for interface_object in self.interface_objects
            if interface_object.failed is not True
        ):
            non_failed_interfaces.add(interface_object)
            available_nodes.add(interface_object.node_object)
            available_nodes.add(interface_object.remote_node_object)

        # Create a model consisting only of the non-failed interfaces and
        # corresponding non-failed (available) nodes
        non_failed_interfaces_model = Model(
            non_failed_interfaces,
            available_nodes,
            self.demand_objects,
            self.rsvp_lsp_objects,
        )

        # Reset the reserved_bandwidth, traffic on each interface
        for interface in iter(self.interface_objects):
            interface.reserved_bandwidth = 0
            interface.traffic = 0

        for lsp in iter(self.rsvp_lsp_objects):
            lsp.path = "Unrouted"
            lsp.clear_effective_metric_cache()

        for demand in iter(self.demand_objects):
            demand.path = "Unrouted"

        time_before_lsp_load = datetime.now()
        print("Routing the LSPs . . . ")
        # Route the RSVP LSPs
        self = self._route_lsps()
        lsp_load_time = datetime.now() - time_before_lsp_load
        print(
            "LSPs routed (if present) in {}; routing demands now . . .".format(
                lsp_load_time
            )
        )
        # Route the demands
        demand_load_start_time = datetime.now()
        self = self._route_demands(non_failed_interfaces_model)
        demand_load_time = datetime.now() - demand_load_start_time
        print("Demands routed in {}; validating model . . . ".format(demand_load_time))

        self.validate_model()

    # TODO - for some reason this is getting called 2x when the model is being updated
    #  initially.  Troubleshoot that.
    def _route_demands(self, model):
        """
        Routes demands in input 'model'

        :param model: input 'model' parameter object (may be different from self)
        :return: model with routed demands
        """

        G = self._make_weighted_network_graph_mdg(include_failed_circuits=False)

        for demand in model.demand_objects:
            demand.path = []

            # Find all LSPs that can carry the demand from source to dest:
            key = "{}-{}".format(
                demand.source_node_object.name, demand.dest_node_object.name
            )
            try:
                lsp_list = [
                    lsp
                    for lsp in self.parallel_lsp_groups()[key]
                    if "Unrouted" not in lsp.path
                ]
            except KeyError:
                lsp_list = []

            # Check for manually assigned metrics
            if len(lsp_list) > 0:
                min_lsp_metric = min([lsp.effective_metric(self) for lsp in lsp_list])
                for lsp in lsp_list:
                    if lsp.effective_metric(self) == min_lsp_metric:
                        demand.path.append([lsp])

            if demand.path == []:  # There are no end to end LSPs for the demand
                src = demand.source_node_object.name
                dest = demand.dest_node_object.name

                # Shortest path in networkx multidigraph
                try:
                    nx_sp = list(nx.all_shortest_paths(G, src, dest, weight="cost"))
                except nx.exception.NetworkXNoPath:
                    # There is no path, demand.path = 'Unrouted'
                    demand.path = "Unrouted"
                    continue

                # all_paths is list of shortest paths from source to destination; these paths
                # may include paths that have multiple links between nodes
                all_paths = self._get_all_paths_mdg(G, nx_sp)

                # Make sure that each path in all_paths only has a single link
                # between each node.  This is path normalization
                path_list = self._normalize_multidigraph_paths(all_paths)

                # Check for IGP shortcuts
                path_list = self.find_igp_shortcuts(path_list, nx_sp)

                demand.path = path_list

        self._update_interface_utilization()

        return self

    def find_igp_shortcuts(self, paths, node_paths):
        """
        Check for LSPs along the shortest path; find the first
        LSP the demand can take with a source and destination that
        is on the LSP's IGP path

        1.  examine each IGP path
        2.  If none of the nodes on the path have IGP shortcuts, continue to next path
        3.  If some nodes have IGP shortcuts enabled, note the hop number (1, 2, 3, etc)
        4.  For nodes that have IGP shortcuts, is there an LSP from that node to a downstream node on the path?

          - if yes, compare the IGP metric of the path to the LSP remote node to that of the LSP metric to that node
          - if no, look at next node downstream with IGP shortcuts

        5.  Look for manually set RSVP LSP metrics that may alter the path calculations

        :param paths: List of lists; each list contains egress Interfaces along the path from source to destination (ordered from source to destination)  # noqa E501
        :param node_paths: List of lists; each list contains node names along the path from source to destination (ordered from source to destination)

        :return: List of lists; each list contains Interfaces and/or RSVP LSPs along each path from source to destination  # noqa E501

        """

        # Check node_paths for igp_shortcuts_enabled nodes
        # TODO - this can likely be optimized

        all_nodes_in_paths = []
        for node_path in node_paths:
            all_nodes_in_paths = all_nodes_in_paths + node_path

        all_nodes_in_paths = set(all_nodes_in_paths)

        shortcut_enabled_nodes = [
            node
            for node in all_nodes_in_paths
            if self.get_node_object(node).igp_shortcuts_enabled is True
        ]

        if len(shortcut_enabled_nodes) == 0:
            return paths

        # ## Find LSPs on shortcut_enabled_nodes that connect to downstream nodes in paths ## #
        # Substitute IGP enabled LSPs for Interfaces in paths

        paths_with_lsps = self._insert_lsp_shortcuts(node_paths, paths)

        if len(paths_with_lsps) == 1:
            return paths_with_lsps

        # Inspect paths to determine if manually set LSP metrics affect path selection
        finalized_paths = self._inspect_for_lsp_metrics(paths_with_lsps)

        return finalized_paths

    def _insert_lsp_shortcuts(self, node_paths, paths):
        """
        Given node_paths and paths, finds and inserts LSPs from shortcut-enabled nodes
        along the path

        :param paths: List of lists; each list contains egress Interfaces along the path from source to destination (ordered from source to destination)  # noqa E501
        :param node_paths: List of lists; each list contains node names along the path from source to destination (ordered from source to destination)

        :return:  List of lists; each list is a path with any possible LSP shortcuts inserted in place
        of the any applicable Interfaces
        """

        # Substitute IGP enabled LSPs for Interfaces in paths
        for node_path in node_paths:
            # Find Nodes along the path that have igp_shortcuts_enabled and have
            # LSPs to downstream Nodes in the path
            path_lsps = []  # List of LSPs to substitute into path
            next_node_to_check = []  # Next node name in path to check for LSPs

            for node_name in node_path:
                # Make sure the next node checked is downstream from the end of any LSPs
                # the traffic has taken thusfar
                if len(next_node_to_check) > 0:
                    if node_path.index(node_name) < node_path.index(
                        next_node_to_check[-1]
                    ):
                        continue
                if self.get_node_object(node_name).igp_shortcuts_enabled is True:
                    # Get the source node object
                    source_node = self.get_node_object(node_name)
                    # Get the source node object index in node_path
                    source_node_index = node_path.index(node_name)

                    # Check for LSPs from present node in path (source_node) to downstream nodes in path;
                    # look for the LSPs that go furthest downstream first
                    destinations = node_path[source_node_index + 1 :]
                    destinations.reverse()
                    for destination in destinations:
                        # Take the LSPs whose source node matches source_node and whose dest node matches
                        # the destination we are iterating through and whose effective metric matches the
                        # shortest path from source_node to destination

                        key = "{}-{}".format(source_node.name, destination)
                        try:
                            candidate_lsps_for_demand = self.parallel_lsp_groups()[key]
                            min_metric = min(
                                lsp.effective_metric(self)
                                for lsp in candidate_lsps_for_demand
                                if "Unrouted" not in lsp.path
                            )
                            lsps = [
                                lsp
                                for lsp in candidate_lsps_for_demand
                                if lsp.effective_metric(self) == min_metric
                                and "Unrouted" not in lsp.path
                            ]
                        except (KeyError, ValueError):
                            # If there is no LSP group that matches the demand source/dest (KeyError) or
                            # there are no routed LSPs for the demand (ValueError), then set lsps
                            # to empty list
                            lsps = []

                        if lsps:
                            # Break out of the destinations iteration as traffic will want to take
                            # the first LSP(s) available the traffic farthest along the path
                            path_lsps.append(lsps)
                            lsp_end_node = lsps[0].dest_node_object.name
                            next_node_to_check.append(lsp_end_node)
                            break

        # Now that path_lsps is known, substitute those into path
        finalized_paths = []
        if len(path_lsps) > 0:
            for interface_path in paths:
                finalized_path = self._insert_lsps_into_path(path_lsps, interface_path)
                if finalized_path != -1:
                    for path in finalized_path:
                        # finalized_path may be a list of lists, so add each component path
                        if path not in finalized_paths:
                            finalized_paths.append(path)
                else:
                    finalized_paths.append(interface_path)
        else:
            # No LSPs available for shortcuts
            finalized_paths = paths

        return finalized_paths

    def _inspect_for_lsp_metrics(self, paths_with_lsps):
        """
        Checks for manually set LSP metrics and how they affect best path
        """
        if len(paths_with_lsps) <= 1:
            return
        # Metrics for each path
        path_metrics = set()
        # List with each path and its metric
        paths_with_metrics = []
        for path in paths_with_lsps:
            path_metric = 0
            for item in path:
                if isinstance(item, Interface):
                    path_metric += item.cost
                elif isinstance(item, RSVP_LSP):
                    path_metric += item.effective_metric(self)
            path_metrics.add(path_metric)
            paths_with_metrics.append([path, path_metric])
            # See if all paths have same metric
        if len(path_metrics) == 1:
            return paths_with_lsps
        else:
            lowest_metric = min(path_metrics)
            return [
                path_and_metric[0]
                for path_and_metric in paths_with_metrics
                if path_and_metric[1] == lowest_metric
            ]

    def _update_interface_utilization(self):
        """Updates each interface's utilization; returns Model object with
        updated interface utilization."""

        # In the model, in an interface is failed, set the traffic attribute
        # to 'Down', otherwise, initialize the traffic to zero
        for interface_object in self.interface_objects:
            interface_object.traffic = "Down" if interface_object.failed else 0.0
        routed_demand_object_generator = (
            demand_object
            for demand_object in self.demand_objects
            if "Unrouted" not in demand_object.path
        )

        # For each demand that is not Unrouted, add its traffic value to each
        # interface object in the path
        for demand_object in routed_demand_object_generator:
            # Expand each LSP into its interfaces and add that the traffic per LSP
            # to the LSP's path interfaces.

            # Can demand take LSP?
            # Is there a parallel_lsp_group that matches the source and dest for the demand_object?
            key = "{}-{}".format(
                demand_object.source_node_object.name,
                demand_object.dest_node_object.name,
            )

            # Find the routed LSPs that can carry the demand
            try:
                candidate_lsps_for_demand = self.parallel_lsp_groups()[key]
                min_metric = min(
                    lsp.effective_metric(self)
                    for lsp in candidate_lsps_for_demand
                    if "Unrouted" not in lsp.path
                )
                lsps_for_demand = [
                    lsp
                    for lsp in candidate_lsps_for_demand
                    if lsp.effective_metric(self) == min_metric
                    and "Unrouted" not in lsp.path
                ]
            except (KeyError, ValueError):
                # If there is no LSP group that matches the demand source/dest (KeyError) or there are no routed
                # LSPs for the demand (ValueError), then set lsps_for_demand to empty list
                lsps_for_demand = []

            if lsps_for_demand != []:
                self._update_int_traffic_for_end_to_end_lsps(
                    demand_object, lsps_for_demand
                )

            # If demand_object is not taking LSPs end to end, IGP route it, using hop by hop ECMP
            else:
                # demand_traffic_per_int will be dict of
                # ('source_node_name-dest_node_name': <traffic from demand>) k,v pairs
                #
                # Example: The interface from node G to node D has 2.5 units of traffic from 'demand'
                # {'G-D': 2.5, 'A-B': 10.0, 'B-D': 2.5, 'A-D': 5.0, 'D-F': 10.0, 'B-G': 2.5}
                demand_traffic_per_item = self._demand_traffic_per_item(demand_object)

                for item, traffic in demand_traffic_per_item.items():
                    if isinstance(item, Interface):
                        for path, path_info in demand_object._path_detail.items():
                            if item in path_info["items"]:
                                item.traffic += path_info["path_traffic"]
                    elif isinstance(item, RSVP_LSP):
                        # Get LSP interfaces
                        interfaces = item.path["interfaces"]
                        for interface in interfaces:
                            # Add traffic to the Interface
                            interface.traffic += traffic

        return self

    def _update_int_traffic_for_end_to_end_lsps(self, demand_object, lsps_for_demand):
        """
        For a given Demand that is taking a single RSVP LSP end to end, update the traffic
        on the LSP's interfaces within self.

        :param demand_object: Demand that is traveling end to end on a single LSP
        :param lsps_for_demand: List of parallel LSPs that transport demand_object
        end to end.  The demand_object splits its traffic evenly across the LSPs

        :return: None; interface traffic updated within self
        """
        # demand_object takes LSP end to end.
        # Find each demand's path list, determine the ECMP split across the
        # routed LSPs, and find the traffic per path (LSP)
        num_routed_lsps_for_demand = len(lsps_for_demand)
        traffic_per_demand_path = round(
            demand_object.traffic / num_routed_lsps_for_demand, 4
        )
        path_detail = {}
        for lsp in lsps_for_demand:
            # Build the path detail: lsp and path traffic
            path_detail["path_{}".format(lsps_for_demand.index(lsp))] = {}
            path_detail["path_{}".format(lsps_for_demand.index(lsp))]["items"] = [lsp]
            path_detail["path_{}".format(lsps_for_demand.index(lsp))][
                "path_traffic"
            ] = traffic_per_demand_path
        # Add detailed path info to demand
        demand_object._path_detail = path_detail
        # Get the interfaces for each LSP in the demand's path
        for lsp in lsps_for_demand:
            try:
                lsp_path_interfaces = lsp.path["interfaces"]
            except TypeError:  # Will error if lsp.path == 'Unrouted'
                pass

            # Now that all interfaces are known,
            # update traffic on interfaces demand touches
            for interface in lsp_path_interfaces:
                # Get the interface's existing traffic and add the
                # portion of the demand's traffic
                interface.traffic += traffic_per_demand_path

    def _demand_traffic_per_item(self, demand):
        """
        Given a Demand object, return the (key, value) pairs for how much traffic each
        Interface/LSP gets from the routing of the traffic load over Model Interfaces.

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

        shortest_path_item_list = []
        for path in demand.path:
            shortest_path_item_list += path

        # Unique interfaces across all shortest paths
        # shortest_path_int_set = set(shortest_path_int_list)
        shortest_path_item_set = set(shortest_path_item_list)

        unique_next_hops = self._find_unique_next_hops(shortest_path_item_set)

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
        #                                  remote_node_object=Node('E'), circuit_id='7'): 6}}}
        shortest_path_info = {}
        path_counter = 0

        # Iterate thru each path for the demand to get traffic per interface
        # and the splits for each demand
        for path in demand.path:
            # Dict of cumulative splits per interface
            traffic_splits_per_interface = {}

            path_key = "path_" + str(path_counter)

            shortest_path_info[path_key] = {}

            # Create cumulative path splits for each item in the path
            total_splits = 1

            # Normalize any paths with LSPs
            for item in path:
                # Update the total cumulative splits in the path before
                # traffic reaches the item in the path
                if isinstance(item, Interface):
                    total_splits = total_splits * len(
                        unique_next_hops[item.node_object.name]
                    )
                elif isinstance(item, RSVP_LSP):
                    total_splits = total_splits * len(
                        unique_next_hops[item.source_node_object.name]
                    )

                traffic_splits_per_interface[item] = total_splits

            # Find path traffic
            max_split = max([split for split in traffic_splits_per_interface.values()])
            path_traffic = float(demand.traffic) / float(max_split)

            shortest_path_info[path_key]["items"] = path
            shortest_path_info[path_key]["splits"] = traffic_splits_per_interface
            shortest_path_info[path_key]["path_traffic"] = path_traffic
            path_counter += 1

        # For each path, determine which interfaces it transits and add
        # that path's traffic to the interface

        # Create dict to hold cumulative traffic for each interface for demand
        traff_per_int = dict.fromkeys(shortest_path_item_set, 0)
        for path, info in shortest_path_info.items():
            for interface in info["items"]:
                traff_per_int[interface] += info["path_traffic"]

        # Round all traffic values to 1 decimal place
        traff_per_int = {
            interface: round(traffic, 1) for interface, traffic in traff_per_int.items()
        }

        demand._path_detail = shortest_path_info

        return traff_per_int

    def _find_unique_next_hops(self, shortest_path_item_set):
        """
        From a set of items from all the shortest paths, determine how many unique
        next hops there are from a given node.

        :param shortest_path_item_set: a set of items (Interfaces, RSVP_LSPs) from all
        the shortest paths

        :return: a dict with keys for each Node name and values being a list of each unique
        next hop from that Node

        In the example output below, Node B has 2 unique next hops, buth of which are RSVP LSPs

        Example output::

            {'A': [Interface(name = 'A-G', cost = 25, capacity = 100, node_object = Node('A'),
                   remote_node_object = Node('G'), circuit_id = '6'),
                   Interface(name = 'A-B', cost = 10, capacity = 100, node_object = Node('A'),
                   remote_node_object = Node('B'), circuit_id = '1')],
             'B': [RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_1'),
                   RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_2')],
             'D': [RSVP_LSP(source = D, dest = F, lsp_name = 'lsp_d_f_1')],
             'G': [Interface(name = 'G-F', cost = 25, capacity = 100, node_object = Node('G'),
                   remote_node_object = Node('F'), circuit_id = '7')]}
        """
        # Dict to store how many unique next hops each node has in the shortest paths
        unique_next_hops = {}
        # Iterate through all the items
        for item in shortest_path_item_set:
            if isinstance(item, Interface):
                unique_next_hops[item.node_object.name] = []
                # For a given Interface's node_object, determine how many
                # Interfaces on that Node are facing next hops
                for hop in shortest_path_item_set:
                    if (
                        isinstance(hop, Interface)
                        and hop.node_object.name == item.node_object.name
                        or not isinstance(hop, Interface)
                        and isinstance(hop, RSVP_LSP)
                        and hop.source_node_object.name == item.node_object.name
                    ):
                        unique_next_hops[item.node_object.name].append(hop)
            elif isinstance(item, RSVP_LSP):
                unique_next_hops[item.source_node_object.name] = []
                # For an LSP's source_node_object,
                for hop in shortest_path_item_set:
                    if (
                        isinstance(hop, Interface)
                        and hop.node_object.name == item.source_node_object.name
                        or not isinstance(hop, Interface)
                        and isinstance(hop, RSVP_LSP)
                        and hop.source_node_object.name == item.source_node_object.name
                    ):
                        unique_next_hops[item.source_node_object.name].append(hop)
        return unique_next_hops

    def _insert_lsps_into_path(self, path_lsps, path):
        """
        Substitutes the path_lsps into the path.  Although the path
        argument is a single path, multiple paths will be returned if there
        are multiple parallel LSPs (in path_lsps component lists) between
        any hops in the path.

        :param path_lsps: List of lists.  Each component list holds
        the parallel LSPs from a common source to a common destination

        Example::

            [[RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_2'),
            RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_1')],
            [RSVP_LSP(source = D, dest = F, lsp_name = 'lsp_d_f_1')]]

        :param path: List of Interfaces in path from source to destination

        :return:  List of path permutations with the LSPs substituted in
        """

        # path_slices is a list of lists; each component list is a tuple
        # for an LSP substitution in the path:
        # [(start_index, end_index, parallel_lsp_1), . .
        # . . ((start_index, end_index, parallel_lsp_x)]
        # Example: 2 LSPs from B to D and 1 LSP from D to F
        #  [[[1, 3, RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_2')],
        #   [1, 3, RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_1')]],
        #   [[3, 5, RSVP_LSP(source = D, dest = F, lsp_name = 'lsp_d_f_1')]]]
        path_slices = []
        for lsp_group in path_lsps:
            # lsp_group_slices is a list of tuples for each parallel LSP in lsp_group:
            # [(start_index, end_index, parallel_lsp_1),. .
            # . . ((start_index, end_index, parallel_lsp_x)]
            lsp_group_slices = []

            try:
                start_interface = [
                    interface
                    for interface in path
                    if isinstance(interface, Interface)
                    and interface.node_object == lsp_group[0].source_node_object
                ][0]

                end_interface = [
                    interface
                    for interface in path
                    if isinstance(interface, Interface)
                    and interface.remote_node_object == lsp_group[0].dest_node_object
                ][0]

            except IndexError:
                # There is no LSP source/dest match for the Interfaces in path; this may happen
                # with Demands that take ECMP paths, where one path has LSP shortcuts and other
                # paths do not have LSP shortcuts
                return -1  # code for no LSPs on path

            slice_to_sub_start_index = path.index(start_interface)
            slice_to_sub_end_index = path.index(end_interface) + 1
            for lsp in lsp_group:
                lsp_group_slices.append(
                    [slice_to_sub_start_index, slice_to_sub_end_index, lsp]
                )

            path_slices.append(lsp_group_slices)

        # Sub in the LSPs, starting from the end of the path (to preserve index values)
        path_slices.reverse()

        path_slice_combos = list(itertools.product(*path_slices))

        # List to hold the path(s) with the LSP(s) substituted in
        paths_with_substitutions = []
        for path_slice_combo in path_slice_combos:
            path_prime = path[:]
            for path_slice in path_slice_combo:
                start_index = path_slice[0]
                end_index = path_slice[1]
                lsp = path_slice[2]
                path_prime[start_index:end_index] = [lsp]

            paths_with_substitutions.append(path_prime)

        return paths_with_substitutions

    def _get_all_paths_mdg(self, G, nx_sp):
        """
        Examines hop-by-hop paths in G and determines specific
        edges transited from one hop to the next

        :param G:  networkx multidigraph object containing nx_sp, contains
        Interface objects in edge data
        :param nx_sp:  List of node paths in G

        Example::

            nx_sp from A to D in graph G::
             [['A', 'D'], ['A', 'B', 'D'], ['A', 'B', 'G', 'D']]

        :return:  List of lists of possible specific model paths from source to
        destination nodes.  Each 'hop' in a given path may include multiple possible
        Interfaces that could be transited from one node to the next adjacent node.

        Example::

            all_paths from 'A' to 'D' is a list of lists; notice that there are
            two Interfacs that could be transited from Node 'B' to Node 'G'
            [[[Interface(name = 'A-to-D', cost = 40, capacity = 20.0, node_object = Node('A'),
                remote_node_object = Node('D'), circuit_id = 1)]],
            [[Interface(name = 'A-to-B', cost = 20, capacity = 125.0, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 2)],
             [Interface(name = 'B-to-D', cost = 20, capacity = 125.0, node_object = Node('B'),
                remote_node_object = Node('D'), circuit_id = 3)]],
            [[Interface(name = 'A-to-B', cost = 20, capacity = 125.0, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 4)],
             [Interface(name = 'B-to-G', cost = 10, capacity = 100.0, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 5),
              Interface(name = 'B-to-G_2', cost = 10, capacity = 50.0, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 6)],
            [Interface(name = 'G-to-D', cost = 10, capacity = 100.0, node_object = Node('G'),
                remote_node_object = Node('D'), circuit_id = 7)]]]

        """

        all_paths = []
        for path in nx_sp:
            current_hop = path[0]
            this_path = []
            for next_hop in path[1:]:
                this_hop = []
                values_source_hop = G[current_hop][next_hop].values()
                min_weight = min(d["cost"] for d in values_source_hop)
                ecmp_links = [
                    interface_index
                    for interface_index, interface_item in G[current_hop][
                        next_hop
                    ].items()
                    if interface_item["cost"] == min_weight
                ]

                # Add Interface(s) to this_hop list and add traffic to Interfaces
                for link_index in ecmp_links:
                    this_hop.append(G[current_hop][next_hop][link_index]["interface"])
                this_path.append(this_hop)
                current_hop = next_hop
            all_paths.append(this_path)

        return all_paths

    def _make_weighted_network_graph_mdg(
        self, include_failed_circuits=True, needed_bw=0, rsvp_required=False
    ):
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

        G = nx.MultiDiGraph()

        # Get all the edges that meet 'failed' and 'reservable_bw' criteria
        if include_failed_circuits is False:
            considered_interfaces = (
                interface
                for interface in self.interface_objects
                if (
                    interface.failed is False
                    and interface.reservable_bandwidth >= needed_bw
                )
            )
        elif include_failed_circuits is True:
            considered_interfaces = (
                interface
                for interface in self.interface_objects
                if interface.reservable_bandwidth >= needed_bw
            )

        if rsvp_required is True:
            edge_names = (
                (
                    interface.node_object.name,
                    interface.remote_node_object.name,
                    {
                        "cost": interface.cost,
                        "interface": interface,
                        "circuit_id": interface.circuit_id,
                    },
                )
                for interface in considered_interfaces
                if interface.rsvp_enabled is True
            )
        else:
            edge_names = (
                (
                    interface.node_object.name,
                    interface.remote_node_object.name,
                    {
                        "cost": interface.cost,
                        "interface": interface,
                        "circuit_id": interface.circuit_id,
                    },
                )
                for interface in considered_interfaces
            )

        # Add edges to networkx DiGraph
        G.add_edges_from(edge_names)

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

        return G

    def _normalize_multidigraph_paths(self, path_info):  # TODO - static?
        """
        Takes the multidigraph_path_info and normalizes it to create all the
        path combos that only have one link between each node.

        :param path_info: List of of interface hops from a source
        node to a destination node.  Each hop in the path
        is a list of all the interfaces from the current node
        to the next node.

        :return: List of lists.  Each component list is a list with a unique
        Interface combination for the egress Interfaces from source to destination

        path_info example from source node 'B' to destination node 'D'.
        Example::

            [
                [[Interface(name = 'B-to-D', cost = 20, capacity = 125, node_object = Node('B'),
                        remote_node_object = Node('D'), circuit_id = '3')]], # there is 1 interface from B to D and a
                        complete path
                [[Interface(name = 'B-to-G_3', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '28'),
                  Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '8'),
                  Interface(name = 'B-to-G_2', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '18')], # there are 3 interfaces from B to G
                [Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                        remote_node_object = Node('D'), circuit_id = '9')]] # there is 1 int from G to D; end of path 2
            ]

        Example::

            [
                [Interface(name = 'B-to-D', cost = 20, capacity = 125, node_object = Node('B'),
                    remote_node_object = Node('D'), circuit_id = '3')], # this is a path with one hop
                [Interface(name = 'B-to-G_3', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '28'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')], # this is a path with 2 hops
                [Interface(name = 'B-to-G_2', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '18'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')], # this is a path with 2 hops
                [Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '8'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')]  # this is a path with 2 hops
            ]

        """
        # List to hold unique path(s)
        path_list = []

        for path in path_info:
            path = list(itertools.product(*path))
            for path_option in path:
                path_list.append(list(path_option))

        return path_list

    def _make_circuits_multidigraph(
        self, return_exception=True, include_failed_circuits=True
    ):
        """
        Matches interface objects into circuits and returns the circuits list

        :param return_exception: Should an exception be returned if not all the
                                 interfaces can be matched into a circuit?
        :param include_failed_circuits:  Should circuits that will be in a
                                         failed state be created?

        :return: a set of Circuit objects in the Model, each Circuit
                 comprised of two Interface objects
        """

        G = self._make_weighted_network_graph_mdg(
            include_failed_circuits=include_failed_circuits
        )

        # Determine which interfaces pair up into good circuits in G
        graph_interfaces = (
            (local_node_name, remote_node_name, data)
            for (local_node_name, remote_node_name, data) in G.edges(data=True)
            if G.has_edge(remote_node_name, local_node_name)
        )

        # Set interface object in_ckt = False
        for interface in iter(self.interface_objects):
            interface.in_ckt = False

        circuits = set([])

        # Using the paired interfaces (source_node, dest_node) pairs from G,
        # get the corresponding interface objects from the model to create
        # the Circuit object
        for interface in iter(graph_interfaces):
            # Get each interface from model for each
            try:
                int1 = self.get_interface_object_from_nodes(
                    interface[0], interface[1], circuit_id=interface[2]["circuit_id"]
                )[0]
            except (
                TypeError,
                IndexError,
            ):  # TODO - are the exception catches necessary?
                msg = (
                    "No matching Interface Object found: source node {}, dest node {} "
                    "circuit_id {} ".format(
                        interface[0], interface[1], interface[2]["circuit_id"]
                    )
                )
                raise ModelException(msg)
            try:
                int2 = self.get_interface_object_from_nodes(
                    interface[1], interface[0], circuit_id=interface[2]["circuit_id"]
                )[0]
            except (TypeError, IndexError):
                msg = (
                    "No matching Interface Object found: source node {}, dest node {} "
                    "circuit_id {} ".format(
                        interface[1], interface[0], interface[2]["circuit_id"]
                    )
                )
                raise ModelException(msg)
            # Mark the interfaces as in ckt
            if int1.in_ckt is False and int2.in_ckt is False:
                # Mark interface objects as in_ckt = True
                int1.in_ckt = True
                int2.in_ckt = True

                ckt = Circuit(int1, int2)
                circuits.add(ckt)

        # Find any interfaces that don't have counterpart
        exception_ints_not_in_ckt = [
            (local_node_name, remote_node_name, data)
            for (local_node_name, remote_node_name, data) in G.edges(data=True)
            if not (G.has_edge(remote_node_name, local_node_name))
        ]

        if exception_ints_not_in_ckt:
            exception_msg = (
                "WARNING: These interfaces were not matched "
                "into a circuit {}".format(exception_ints_not_in_ckt)
            )
            if return_exception:
                raise ModelException(exception_msg)
            else:
                return {"data": exception_ints_not_in_ckt}

        self.circuit_objects = circuits

    def get_interface_object_from_nodes(
        self, local_node_name, remote_node_name, circuit_id=None
    ):
        """
        Returns a list of Interface objects with the specified
        local and remote node names.

        If 'circuit_id' is not specified, may return a list of len > 1, as
        multiple/parallel interfaces are allowed in Parallel_Link_Model
        objects.

        If 'circuit_id' is specified, will return a list of len == 1, as specifying
        the 'circuit_id' will narrow down any list of multiple interfaces to a single
        interface because circuit_ids bond interfaces on different nodes into
        a Circuit object.

        :param local_node_name: Name of local node Interface resides on
        :param remote_node_name: Name of Interface's remote Node
        :param circuit_id: circuit_id of Interface (optional)

        :return: list of Interface objects with common local node and remote node
        """

        interface_gen = iter(self.interface_objects)

        if circuit_id is None:
            interface_list = [
                interface
                for interface in interface_gen
                if interface.node_object.name == local_node_name
                and interface.remote_node_object.name == remote_node_name
            ]
        else:
            interface_list = [
                interface
                for interface in interface_gen
                if interface.node_object.name == local_node_name
                and interface.remote_node_object.name == remote_node_name
                and interface.circuit_id == circuit_id
            ]

            if len(interface_list) > 1:
                msg = (
                    "There is an internal error with circuit_iding; Interface circuit_ids must be unique"
                    " per Node and the same circuit_id can only appear in a Parallel_Link_Model object "
                    "twice and on separate Nodes"
                )
                return ModelException(msg)
        return interface_list

    def add_circuit(
        self,
        node_a_object,
        node_b_object,
        node_a_interface_name,
        node_b_interface_name,
        cost_intf_a=1,
        cost_intf_b=1,
        capacity=1000,
        failed=False,
        circuit_id=None,
    ):
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
            circuit_id = max(circuit_ids, default=0) + 1
        else:
            circuit_ids = self.all_interface_circuit_ids

        if circuit_id in circuit_ids:
            err_msg = "circuit_id value {} is already exists in model".format(
                circuit_id
            )
            raise ModelException(err_msg)

        int_a = Interface(
            node_a_interface_name,
            cost_intf_a,
            capacity,
            node_a_object,
            node_b_object,
            circuit_id,
        )
        int_b = Interface(
            node_b_interface_name,
            cost_intf_b,
            capacity,
            node_b_object,
            node_a_object,
            circuit_id,
        )

        existing_int_keys = {interface._key for interface in self.interface_objects}

        if int_a._key in existing_int_keys:
            raise ModelException(
                "interface {} on node {} - "
                "interface already exists in model".format(int_a, node_a_object)
            )
        elif int_b._key in existing_int_keys:
            raise ModelException(
                "interface {} on node {} - "
                "interface already exists in model".format(int_b, node_b_object)
            )

        self.interface_objects.add(int_a)
        self.interface_objects.add(int_b)

        self.validate_model()

    def get_all_paths_reservable_bw(
        self,
        source_node_name,
        dest_node_name,
        include_failed_circuits=True,
        cutoff=10,
        needed_bw=0,
    ):
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
                 path = {'path': [list of shortest path routes]}

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
        G = self._make_weighted_network_graph_mdg(
            include_failed_circuits=include_failed_circuits, needed_bw=needed_bw
        )

        # Define the Model-style path to be built
        converted_path = {"path": []}
        # Find the simple paths in G between source and dest
        digraph_all_paths = nx.all_simple_paths(
            G, source_node_name, dest_node_name, cutoff=cutoff
        )

        # Remove duplicate paths from digraph_all_paths
        # (duplicates can be caused by multiple links between nodes)
        digraph_unique_paths = [
            list(path) for path in {tuple(path) for path in digraph_all_paths}
        ]

        try:
            for path in digraph_unique_paths:
                model_path = self._convert_nx_path_to_model_path(path, needed_bw)
                converted_path["path"].append(model_path)
        except BaseException:
            return converted_path

        # Normalize the path info to get all combinations of with parallel
        # interfaces
        path_info = self._normalize_multidigraph_paths(converted_path["path"])
        return {"path": path_info}

    def get_shortest_path(self, source_node_name, dest_node_name, needed_bw=0):
        """
        For a source and dest node name pair, find the shortest path(s) with at
        least needed_bw available.

        :param source_node_name: name of source node in path
        :param dest_node_name: name of destination node in path
        :param needed_bw: the amount of reservable bandwidth required on the path
        :return: Return the shortest path in dictionary form:
                 shortest_path = {'path': [list of shortest path routes], 'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph_mdg(
            include_failed_circuits=False, needed_bw=needed_bw
        )

        # Define the Model-style path to be built
        converted_path = dict()
        converted_path["path"] = []
        converted_path["cost"] = None

        # Find the shortest paths in G between source and dest

        multidigraph_shortest_paths = nx.all_shortest_paths(
            G, source_node_name, dest_node_name, weight="cost"
        )
        # Get shortest path(s) from source to destination; this may include paths
        # that have multiple links between nodes
        try:
            for path in multidigraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path(path, needed_bw)
                converted_path["path"].append(model_path)
                converted_path["cost"] = nx.shortest_path_length(
                    G, source_node_name, dest_node_name, weight="cost"
                )
        except BaseException:
            return converted_path

        # Normalize the path info to get all combinations of with parallel
        # interfaces
        path_info = self._normalize_multidigraph_paths(converted_path["path"])

        return {"cost": converted_path["cost"], "path": path_info}

    def get_shortest_path_for_routed_lsp(
        self, source_node_name, dest_node_name, lsp, needed_bw
    ):
        """
        For a source and dest node name pair, find the shortest path(s) with at
        least needed_bw available for an LSP that is already routed.
        Return the shortest path in dictionary form:
        shortest_path = {'path': [list of shortest path routes], 'cost': path_cost}

        :param source_node_name: name of source node
        :param dest_node_name: name of destination node
        :param lsp: LSP object
        :param needed_bw: reserved bandwidth for LSPs
        :return: dict {'path': [list of lists, each list a shortest path route], 'cost': path_cost}
        """

        # Define a networkx DiGraph to find the path
        G = self._make_weighted_network_graph_routed_lsp(lsp, needed_bw=needed_bw)

        # Define the Model-style path to be built
        converted_path = {"path": [], "cost": None}
        # Find the shortest paths in G between source and dest
        digraph_shortest_paths = nx.all_shortest_paths(
            G, source_node_name, dest_node_name, weight="cost"
        )

        try:
            for path in digraph_shortest_paths:
                model_path = self._convert_nx_path_to_model_path_routed_lsp(
                    path, needed_bw, lsp
                )
                converted_path["path"].append(model_path)
                converted_path["cost"] = nx.shortest_path_length(
                    G, source_node_name, dest_node_name, weight="cost"
                )
        except BaseException:
            return converted_path

        # Normalize the path info to get all combinations of with parallel
        # interfaces
        path_info = self._normalize_multidigraph_paths(converted_path["path"])

        return {"cost": converted_path["cost"], "path": path_info}

    def _convert_nx_path_to_model_path(self, nx_graph_path, needed_bw):
        """
        Given a path from an networkx DiGraph, converts that
        path to a Model style path and returns that Model style path

        A networkx path is a list of nodes in order of transit.
        ex: ['A', 'B', 'G', 'D', 'F']

        The corresponding model style path would be::

            [Interface(name = 'A-to-B', cost = 20, capacity = 125, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 9),
            Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 6),
            Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                remote_node_object = Node('D'), circuit_id = 2),
            Interface(name = 'D-to-F', cost = 10, capacity = 300, node_object = Node('D'),
                remote_node_object = Node('F'), circuit_id = 1)]

        :param nx_graph_path: list of node names
        :param needed_bw: needed reservable bandwidth on the requested path
        :return: List of Model Interfaces from source to destination
        """

        # Define a model-style path to build
        model_path = []

        # look at each hop in the path
        for current_hop_index, hop in enumerate(nx_graph_path):
            next_hop_index = current_hop_index + 1
            if next_hop_index < len(nx_graph_path):
                next_hop = nx_graph_path[next_hop_index]

                interface = [
                    interface
                    for interface in self.get_interface_object_from_nodes(hop, next_hop)
                    if interface.reservable_bandwidth >= needed_bw
                ]

                model_path.append(interface)

        return model_path

    def _convert_nx_path_to_model_path_routed_lsp(self, nx_graph_path, needed_bw, lsp):
        """
        Given a path from an networkx DiGraph, converts that
        path to a Model style path and returns that Model style path

        A networkx path is a list of nodes in order of transit.
        ex: ['A', 'B', 'G', 'D', 'F']

        Because a networkx path does not show the edges used, this def
        examines the interface(s) from each hop to the next hop and adds them
        to a hop_interface_list

        The corresponding model style path could be::
            [Interface(name = 'A-to-B', cost = 20, capacity = 125, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 9),
            Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 6),
            Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                remote_node_object = Node('D'), circuit_id = 2),
            Interface(name = 'D-to-F', cost = 10, capacity = 300, node_object = Node('D'),
                remote_node_object = Node('F'), circuit_id = 1)]

        :param nx_graph_path: list of node names
        :param needed_bw: needed reservable bandwidth on the requested path
        :param lsp: RSVP LSP object to be acted on
        :return: List of Model Interfaces from source to destination
        """

        # Define a model-style path to build
        model_path = []

        # look at each hop in the path
        for current_hop_index, hop in enumerate(nx_graph_path):
            next_hop_index = current_hop_index + 1
            if next_hop_index < len(nx_graph_path):
                next_hop = nx_graph_path[next_hop_index]
                for interface in self.get_interface_object_from_nodes(hop, next_hop):
                    # Look at all the interface(s) from (current) hop to next_hop; see if
                    # any of those interfaces are in the current path for lsp; if they are,
                    # see if any of them could handle the additional_needed_bandwidth for lsp
                    hop_interface_list = []
                    if interface in lsp.path["interfaces"] and (
                        interface.reservable_bandwidth + lsp.reserved_bandwidth
                        >= needed_bw
                    ):
                        hop_interface_list.append(interface)

                    elif interface.reservable_bandwidth >= needed_bw:
                        # If the interface is not in the current path but can
                        # accommodate the needed_bw, then add that interface
                        # to model_path
                        hop_interface_list.append(interface)

                    if hop_interface_list:
                        model_path.append(hop_interface_list)
        return model_path

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

        # Track the needed_bw for which the graph was last built so we
        # only rebuild when the bandwidth requirement changes
        cached_graph = None
        cached_needed_bw = None

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

            # Rebuild graph only when needed_bw changes or after bandwidth
            # was consumed by a previously routed LSP in this group
            if cached_graph is None or lsp.setup_bandwidth != cached_needed_bw:
                cached_graph = self._make_weighted_network_graph_mdg(
                    include_failed_circuits=False,
                    rsvp_required=True,
                    needed_bw=lsp.setup_bandwidth,
                )
                cached_needed_bw = lsp.setup_bandwidth

            G = cached_graph

            lsp.path = {}

            # Get shortest paths in networkx multidigraph
            try:
                nx_sp = list(
                    nx.all_shortest_paths(
                        G,
                        lsp.source_node_object.name,
                        lsp.dest_node_object.name,
                        weight="cost",
                    )
                )
            except nx.exception.NetworkXNoPath:
                # There is no path; path = 'Unrouted'
                lsp.path = "Unrouted"
                lsp.reserved_bandwidth = "Unrouted"
                continue

            # Convert node hop by hop paths from G into Interface-based paths
            all_paths = self._get_all_paths_mdg(G, nx_sp)

            # all_paths may have hops between nodes that can take different Interfaces;
            # normalize those hops that could transit any of multiple Interfaces into
            # distinct, unique possible paths
            candidate_path_info = self._normalize_multidigraph_paths(all_paths)

            # Candidate paths with enough reservable bandwidth
            candidate_path_info_w_reservable_bw = []

            # Determine which candidate paths have enough reservable bandwidth
            for path in candidate_path_info:
                if (
                    min(interface.reservable_bandwidth for interface in path)
                    >= lsp.setup_bandwidth
                ):
                    candidate_path_info_w_reservable_bw.append(path)

            # If multiple lowest_metric_paths, find those with fewest hops
            if not candidate_path_info_w_reservable_bw:
                lsp.path = "Unrouted"
                lsp.reserved_bandwidth = "Unrouted"
                continue

            elif len(candidate_path_info_w_reservable_bw) > 1:
                fewest_hops = min(
                    len(path) for path in candidate_path_info_w_reservable_bw
                )
                lowest_hop_count_paths = [
                    path
                    for path in candidate_path_info_w_reservable_bw
                    if len(path) == fewest_hops
                ]
                if len(lowest_hop_count_paths) > 1:
                    new_path = random.choice(lowest_hop_count_paths)
                else:
                    new_path = lowest_hop_count_paths[0]
            else:
                new_path = candidate_path_info_w_reservable_bw[0]

            # Change LSP path into more verbose form and set LSP's path
            self._add_lsp_path_data(lsp, new_path)

            for interface in [
                interface
                for interface in lsp.path["interfaces"]
                if lsp.path != "Unrouted"
            ]:
                interface.reserved_bandwidth += lsp.reserved_bandwidth

            # Invalidate cached graph since bandwidth was consumed
            cached_graph = None

    def _make_weighted_network_graph_routed_lsp(self, lsp, needed_bw=0):
        """
        Returns a networkx weighted network directional graph from the input Model object.
        Considers edges with needed_bw of reservable_bandwidth and also takes into account
        reserved_bandwidth by the lsp on Interfaces in the existing LSP path.

        :param include_failed_circuits: failed circuits can be included in
        the graph as functional edges
        :param lsp:  LSP to be considered
        :param needed_bw: amount of reservable bandwidth an interface must have
        to be added to the graph
        :return:
        """

        # The Interfaces that the lsp is routed over currently
        lsp_path_interfaces = lsp.path["interfaces"]

        eligible_interface_generator = (
            interface
            for interface in self.interface_objects
            if (interface.failed is False and interface.rsvp_enabled is True)
        )

        eligible_interfaces = set()

        # Find only the interfaces that are not failed and that have
        # enough reservable_bandwidth
        for interface in eligible_interface_generator:
            # Add back the lsp's reserved bandwidth to Interfaces already in its path
            if interface in lsp_path_interfaces:
                effective_reservable_bw = (
                    interface.reservable_bandwidth + lsp.reserved_bandwidth
                )
            else:
                effective_reservable_bw = interface.reservable_bandwidth

            if effective_reservable_bw >= needed_bw:
                eligible_interfaces.add(interface)

        # Get edge names in eligible_interfaces
        edge_names = (
            (
                interface.node_object.name,
                interface.remote_node_object.name,
                interface.cost,
            )
            for interface in eligible_interfaces
        )

        # Make a new graph with the eligible interfaces (interfaces
        # with enough effective_reservable_bw)
        G = nx.MultiDiGraph()

        # Add edges to networkx MultiDiGraph
        G.add_weighted_edges_from(edge_names, weight="cost")

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

        return G

    @classmethod
    def load_model_file(cls, data_file):  # TODO - allow commas instead of tabs
        """
        Opens a network_modeling data file, returns a model containing
        the info in the data file, and runs update_simulation().

        The data file must be of the appropriate
        format to produce a valid model.  This cannot be used to open
        multiple models in a single python instance - there may be
        unpredictable results in the info in the models.

        The format for the file must be a tab separated value file.

        CIRCUIT ID (circuit_id) MUST BE SPECIFIED AS THIS IS WHAT ALLOWS THE CLASS
        TO DISCERN WHAT MULTIPLE, PARALLEL INTERFACES BETWEEN THE SAME NODES MATCH
        UP INTO WHICH CIRCUIT.  THE circuit_id CAN BE ANY COMMON KEY, SUCH AS IP SUBNET ID
        OR DESIGNATED CIRCUIT ID FROM PRODUCTION.

        This docstring you are reading may not display the table info
        explanations/examples below correctly on https://pyntm.readthedocs.io/en/latest/api.html.
        Recommend either using help(Model.load_model_file) at the python3 cli or
        looking at one of the sample model data_files in github:
        https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples/sample_network_model_file.csv
        https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples/lsp_model_test_file.csv

        The following headers must exist, with the following tab-column
        names beneath::

            INTERFACES_TABLE
            - node_object_name - name of node	where interface resides
            - remote_node_object_name	- name of remote node
            - name - interface name
            - cost - IGP cost/metric for interface
            - capacity - capacity
            - circuit_id - id of the circuit; used to match two Interfaces into Circuits;
                - each circuit_id can only appear twice in the model
                - circuit_id can be string or integer
            - rsvp_enabled (optional) - is interface allowed to carry RSVP LSPs? True|False; default is True
            - percent_reservable_bandwidth (optional) - percent of capacity allowed to be reserved by RSVP LSPs; this
            value should be given as a percentage value - ie 80% would be given as 80, NOT .80.  Default is 100

            Note - The existence of Nodes will be inferred from the INTERFACES_TABLE.
            So a Node created from an Interface does not have to appear in the
            NODES_TABLE unless you want to add additional attributes for the Node
            such as latitude/longitude

            NODES_TABLE -
            - name - name of node
            - lon - longitude (or y-coordinate)
            - lat - latitude (or x-coordinate)
            - igp_shortcuts_enabled(default=False)

            Note - The NODES_TABLE is present for 2 reasons:
            - to add a Node that has no interfaces
            - and/or to add additional attributes for a Node inferred from
            the INTERFACES_TABLE

            DEMANDS_TABLE
            - source - source node name
            - dest - destination node name
            - traffic	- amount of traffic on demand
            - name - name of demand

            RSVP_LSP_TABLE (this table is optional)
            - source - source node name
            - dest - destination node name
            - name - name of LSP
            - configured_setup_bw - if LSP has a fixed, static configured setup bandwidth, place that static value here,
            if LSP is auto-bandwidth, then leave this blank for the LSP (optional)
            - manual_metric - manually assigned metric for LSP, if not using default metric from topology
            shortest path (optional)

        Functional model files can be found in this directory in
        https://github.com/tim-fiola/network_traffic_modeler_py3/tree/master/examples

        Here is an example of a data file.

        Example::

            INTERFACES_TABLE
            node_object_name	remote_node_object_name	name	cost	capacity    circuit_id  rsvp_enabled    percent_reservable_bandwidth # noqa E501
            A	B	A-to-B_1    20	120 1   True  50
            B	A	B-to-A_1    20	120 1   True  50
            A   B   A-to-B_2    20  150 2
            B   A   B-to-A_2    20  150 2
            A   B   A-to-B_3    10  200 3   False
            B   A   B-to-A_3    10  200 3   False

            NODES_TABLE
            name	lon	lat igp_shortcuts_enabled(default=False)
            A	50	0   True
            B	0	-50 False

            DEMANDS_TABLE
            source	dest	traffic	name
            A	B	80	dmd_a_b_1

            RSVP_LSP_TABLE
            source	dest	name    configured_setup_bw manual_metric
            A	B	lsp_a_b_1   10  19
            A	B	lsp_a_b_2       6

        :param data_file: file with model info
        :return: Model object

        """
        # TODO - allow user to add user-defined columns in NODES_TABLE and add that as an attribute to the Node

        interface_set = set()
        node_set = set()
        demand_set = set()
        lsp_set = set()

        # Open the file with the data, read it, and split it into lines
        with open(data_file, "r", encoding="utf-8-sig") as f:
            data = f.read()

        lines = data.splitlines()

        # Define the Interfaces from the data and extract the presence of
        # Nodes from the Interface data
        int_info_begin_index = lines.index("INTERFACES_TABLE") + 2
        int_info_end_index = find_end_index(int_info_begin_index, lines)

        # Detect whether the file has a circuit_id column by checking
        # the header line (the line right after INTERFACES_TABLE)
        header_line = lines[lines.index("INTERFACES_TABLE") + 1]
        header_cols = [col.strip().lower() for col in header_line.split("\t")]
        has_circuit_id_col = "circuit_id" in header_cols

        # Check that each circuit_id appears exactly 2 times (only for
        # files that include circuit_id column)
        if has_circuit_id_col:
            circuit_id_list = []
            for line in lines[int_info_begin_index:int_info_end_index]:
                try:
                    circuit_id_item = line.split("\t")[5]
                    circuit_id_list.append(circuit_id_item)
                except IndexError:
                    pass

            bad_circuit_ids = [
                {"circuit_id": item, "appearances": circuit_id_list.count(item)}
                for item in set(circuit_id_list)
                if circuit_id_list.count(item) != 2
            ]

            if len(bad_circuit_ids) != 0:
                msg = (
                    "Each circuit_id value must appear exactly twice; the following circuit_id values "
                    "do not meet that criteria: {}".format(bad_circuit_ids)
                )
                raise ModelException(msg)

        interface_set, node_set = cls._extract_interface_data_and_implied_nodes(
            int_info_begin_index, int_info_end_index, lines, has_circuit_id_col
        )
        # Define the explicit nodes info from the file
        nodes_info_begin_index = lines.index("NODES_TABLE") + 2
        nodes_info_end_index = find_end_index(nodes_info_begin_index, lines)
        node_lines = lines[nodes_info_begin_index:nodes_info_end_index]
        for node_line in node_lines:
            node_set = cls._add_node_from_data(
                demand_set, interface_set, lsp_set, node_line, node_set
            )

        # Define the demands info
        demands_info_begin_index = lines.index("DEMANDS_TABLE") + 2
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
            lsp_info_begin_index = lines.index("RSVP_LSP_TABLE") + 2
            cls._add_lsp_from_data(lsp_info_begin_index, lines, lsp_set, node_set)
        except ValueError:
            print("RSVP_LSP_TABLE not in file; no LSPs added to model")
        except ModelException as e:
            err_msg = e.args[0]
            raise ModelException(err_msg)

        return cls(interface_set, node_set, demand_set, lsp_set)

    @classmethod
    def _extract_interface_data_and_implied_nodes(
        cls, int_info_begin_index, int_info_end_index, lines, has_circuit_id_col=True
    ):
        """
        Extracts interface data from lines and adds Interface objects to a set.
        Also extracts the implied Nodes from the Interfaces and adds those Nodes to a set.

        :param int_info_begin_index: Index position in lines where interface info begins
        :param int_info_end_index:  Index position in lines where interface info ends
        :param lines: lines of data describing a Model objects
        :param has_circuit_id_col: True if file has circuit_id column (6th column)
        :return: set of Interface objects, set of Node objects created from lines
        """

        interface_set = set()
        node_set = set()
        interface_lines = lines[int_info_begin_index:int_info_end_index]
        # Auto-assign circuit_ids for files without circuit_id column.
        # Paired interfaces (A->B and B->A) must share the same circuit_id.
        _auto_circuit_id_counter = 1
        _node_pair_to_circuit_id = {}  # frozenset({nodeA, nodeB}) -> circuit_id
        # Add the Interfaces to a set
        for interface_line in interface_lines:
            cols = interface_line.split("\t")
            num_cols = len(cols)

            # Minimum columns required
            if num_cols < 5:
                msg = (
                    "node_name, remote_node_name, name, cost, capacity "
                    "must be defined for line {}, line index {}".format(
                        interface_line, lines.index(interface_line)
                    )
                )
                raise ModelException(msg)

            node_name = cols[0]
            remote_node_name = cols[1]
            name = cols[2]
            cost = cols[3]
            capacity = cols[4]
            rsvp_enabled_bool = True
            percent_reservable_bandwidth = 100

            if has_circuit_id_col:
                # Format with circuit_id column: cols[5] = circuit_id
                if num_cols < 6:
                    msg = (
                        "node_name, remote_node_name, name, cost, capacity "
                        "must be defined for line {}, line index {}".format(
                            interface_line, lines.index(interface_line)
                        )
                    )
                    raise ModelException(msg)
                circuit_id = cols[5]
                if num_cols >= 7:
                    rsvp_enabled = cols[6]
                    rsvp_enabled_bool = rsvp_enabled in [True, "T", "True", "true"]
                if num_cols >= 8:
                    percent_reservable_bandwidth = cols[7]
            else:
                # No circuit_id column — auto-assign paired circuit_ids
                pair_key = frozenset([node_name, remote_node_name])
                if pair_key in _node_pair_to_circuit_id:
                    circuit_id = _node_pair_to_circuit_id.pop(pair_key)
                else:
                    circuit_id = _auto_circuit_id_counter
                    _node_pair_to_circuit_id[pair_key] = circuit_id
                    _auto_circuit_id_counter += 1
                if num_cols >= 6:
                    rsvp_enabled = cols[5]
                    rsvp_enabled_bool = rsvp_enabled in [True, "T", "True", "true"]
                if num_cols >= 7:
                    percent_reservable_bandwidth = cols[6]

            node_names = [node.name for node in node_set]

            if node_name in node_names:
                node_object = [node for node in node_set if node.name == node_name][0]
            else:
                node_object = Node(node_name)

            if remote_node_name in node_names:
                remote_node_object = [
                    node for node in node_set if node.name == remote_node_name
                ][0]
            else:
                remote_node_object = Node(remote_node_name)

            new_interface = Interface(
                name,
                int(cost),
                int(capacity),
                node_object,
                remote_node_object,
                circuit_id,
                rsvp_enabled_bool,
                float(percent_reservable_bandwidth),
            )

            if new_interface._key not in {
                interface._key for interface in interface_set
            }:
                interface_set.add(new_interface)
            else:
                print(
                    "{} already exists in model; disregarding line {}".format(
                        new_interface, lines.index(interface_line)
                    )
                )

            # Derive Nodes from the Interface data
            if node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.node_object)
            if remote_node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.remote_node_object)

        return interface_set, node_set
