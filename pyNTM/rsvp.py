"""A class to represent an RSVP label-switched-path in the network model """

import random

from .exceptions import ModelException

# debug code
import pdb
from pprint import pprint

# For when the model has both LSPs but not a full LSP mesh,
# - create the LSP model first
# - if there are not paths between all nodes, find those specific paths
#    in a model made up of just interfaces

class RSVP_LSP(object):
    """A class to represent an RSVP label-switched-path in the network model

    source_node_object: Node where LSP ingresses the network (LSP starts here)

    dest_node_object: Node where LSP egresses the network (LSP ends here)

    lsp_name: name of LSP

    path: will either be 'Unrouted' or be a dict containing the following -
        - interfaces: list of interfaces that LSP egresses in the order it
            egresses them
        - path_cost: sum of costs of the interfaces
        - baseline_path_reservable_bw: the amount of reservable bandwidth
            available on the LSP's path when the LSP was signaled, not inclusive
            of the bandwidth already reserved by this LSP on that path (if any)

    reserved_bandwidth: amount of bandwidth reserved by this LSP

    setup_bandwidth: amount of bandwidth this LSP wants to signal for

    """

    def __init__(self, source_node_object, dest_node_object,
                 lsp_name='none'):

        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.lsp_name = lsp_name
        self.path = 'Unrouted - initial'
        self.reserved_bandwidth = 'Unrouted - initial'
        self.setup_bandwidth = 'Unrouted - initial'  # TODO - getter/setter

    @property
    def _key(self):
        """Unique identifier for the rsvp lsp: (Node('source').name, Node('dest').name, name)"""
        return (self.source_node_object.name, self.dest_node_object.name, self.lsp_name)

    def __repr__(self):
        return 'RSVP_LSP(source = %s, dest = %s, lsp_name = %r)' % \
               (self.source_node_object.name,
                self.dest_node_object.name,
                self.lsp_name)

    # TODO - make __ def to allow use of <, >, == by looking at source and deset only

    def _calculate_setup_bandwidth(self, model):
        """Find amount of bandwidth to reserve for LSP"""
        # TODO - not needed

        # Find all demands that would ride the LSP
        demand_list = []
        for demand in model.demand_objects:
            if demand.source_node_object == self.source_node_object and \
                    demand.dest_node_object == self.dest_node_object:
                demand_list.append(demand)

        sum_demand_traffic = sum([demand.traffic for demand in demand_list])

        all_lsps_src_to_dest = [lsp for lsp in model.rsvp_lsp_objects if
                                lsp.source_node_object == self.source_node_object and
                                lsp.dest_node_object == self.dest_node_object]

        needed_bw = sum_demand_traffic / len(all_lsps_src_to_dest)

        self.setup_bandwidth = needed_bw

        return self

    def routed_parallel_lsp_group(self, model):
        """
        Finds all routed LSPs whose source node and destination node match that of self
        :param model: Model object
        :return:  list of all routed LSPs from self.source_node_object to self.dest_node_object
        """
        # Calculate the amount of bandwidth for each LSP
        routed_lsps_src_to_dest = [lsp for lsp in model.rsvp_lsp_objects if
                                   (lsp.source_node_object == self.source_node_object and
                                    lsp.dest_node_object == self.dest_node_object and
                                    'Unrouted' not in lsp.path)]
        return routed_lsps_src_to_dest

    def _find_path_cost_and_headroom_routed_lsp(self, candidate_paths):
        """
        Returns a list of dictionaries containing the path interfaces as
        well as the path cost and headroom available on the path.
        :param candidate_paths: list of lists of Interface objects
        :return: list of dictionaries of paths: {'interfaces': path,
                                                 'path_cost': path_cost,
                                                 'baseline_path_reservable_bw': baseline_path_reservable_bw}
        """

        # List to hold info on each candidate path
        candidate_path_info = []

        # Find the path cost and path headroom for each path candidate
        for path in candidate_paths:

            path_cost = 0
            for interface in path:
                path_cost += interface.cost

            # Find the path cost and reservable bandwidth on each path.
            # If the path you are examining has an interface that is on
            # the LSP's current path, don't count (or add back in) the
            # reserved bandwidth for the LSP to that interface
            proto_reservable_bw = {}
            for interface in path:
                if interface in self.path['interfaces']:
                    proto_reservable_bw[interface] = interface.reservable_bandwidth + self.reserved_bandwidth
                else:
                    proto_reservable_bw[interface] = interface.reservable_bandwidth

            # baseline_path_reservable_bw is the max amount of traffic that the path
            # can handle without saturating a component interface

            baseline_path_reservable_bw = min(proto_reservable_bw.values())


            path_info = {'interfaces': path, 'path_cost': path_cost,
                         'baseline_path_reservable_bw': baseline_path_reservable_bw}

            candidate_path_info.append(path_info)

        return candidate_path_info

    def find_rsvp_path_w_bw(self, requested_bandwidth, model):
        """
        Will search the topology of 'model' for a path for self that has at least
        'requested_bandwidth' of reservable_bandwidth.  If there is one, will update
        self.path; if not, will keep same self.path

        :param model: Model object to search
        :param requested_bandwidth: number of units set for reserved_bandwidth
        :return: self with the current or updated path info
        """

        # Get candidate paths
        candidate_paths = model.get_feasible_paths(self.source_node_object.name,
                                                   self.dest_node_object.name)

        # Find the path cost and path headroom for each path candidate
        candidate_path_info = self._find_path_cost_and_headroom_routed_lsp(candidate_paths)

        # Filter out paths that don't have enough headroom
        candidate_paths_with_enough_headroom = [path for path in candidate_path_info
                                                if (path['baseline_path_reservable_bw']) >=
                                                requested_bandwidth]

        # If there are no paths with enough headroom, return self
        if len(candidate_paths_with_enough_headroom) == 0:
            return self
        # If there is only one path with enough headroom, make that self.path
        elif len(candidate_paths_with_enough_headroom) == 1:
            self.path = candidate_paths_with_enough_headroom[0]
        # If there is more than one path with enough headroom,
        # choose one at random and make that self.path
        elif len(candidate_paths_with_enough_headroom) > 1:
            self.path = random.choice(candidate_paths_with_enough_headroom)

        self.reserved_bandwidth = requested_bandwidth
        self.setup_bandwidth = requested_bandwidth
        return self





    def _add_rsvp_lsp_path(self, model, setup_bandwidth):
        """
        Determines the LSP's path regardless of whether it was previously routed
        or not (non stateful).
        If this LSP is currently routed and takes takes on additional traffic
        and there is not a path that can handle the additional traffic,
        this LSP will not signal.
        :param model: Model object that the LSP is in
        :return: self with 'path' attribute
        """

        # TODO - delete all this . . .
#         # Find all demands that would take the LSP
#         demands_for_lsp = []
#         for demand in (demand for demand in model.demand_objects):
#             if (demand.source_node_object == self.source_node_object and
#                     demand.dest_node_object == self.dest_node_object):
#                 demands_for_lsp.append(demand)
#
#         # Find sum of all traffic for demands_for_lsp TODO - remove this
# #        demands_for_lsp_traffic = sum((demand.traffic for demand in demands_for_lsp))
#
#         # Find setup bandwidth
#         self = self._calculate_setup_bandwidth(model)

        # Get candidate paths
        candidate_paths = model.get_feasible_paths(self.source_node_object.name,
                                                   self.dest_node_object.name)

        # Route LSP
        #   Options:
        #   a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
        #   b.  There are viable paths, but none with enough headroom - LSP will not be routed
        #   c.  LSP can route with current setup_bandwidth

        # Option a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
        if candidate_paths == []:
            # If there are no possible paths, then LSP is Unrouted
            self.path = 'Unrouted - no path' # TODO - make this 'Unrouted - no path'
            self.reserved_bandwidth = 'Unrouted - no path' # TODO - make this 'Unrouted - no path'
            return self

        # Find the path cost and path headroom for each path candidate
        candidate_path_info = self._find_path_cost_and_headroom(candidate_paths)

        # Filter out paths that don't have enough headroom
        candidate_paths_with_enough_headroom = [path for path in candidate_path_info
                                                if path['baseline_path_reservable_bw'] >=
                                                self.setup_bandwidth]

        # Option b. There are viable paths, but none that can
        # accommodate the setup_bandwidth
        if candidate_paths_with_enough_headroom == []:
            self.path = 'Unrouted - setup_bandwidth'
            self.reserved_bandwidth = 'Unrouted - setup_bandwidth'
            return self

        # Option c.  LSP can route with current setup_bandwidth

        # Find the lowest available path metric
        lowest_available_metric = min([path['path_cost'] for path in
                                       candidate_paths_with_enough_headroom])

        # Finally, find all paths with the lowest cost and enough headroom
        best_paths = [path for path in candidate_paths_with_enough_headroom
                      if path['path_cost'] == lowest_available_metric]

        # If multiple paths, pick a best path at random
        if len(best_paths) > 1:
            new_path = random.choice(best_paths)
        else:
            new_path = best_paths[0]

        self.path = new_path

        # Since there is enough headroom, set LSP reserved_bandwidth
        # to setup_bandwidth
        self.reserved_bandwidth = self.setup_bandwidth

        # Update the reserved_bandwidth on each interface on the new path
        for interface in self.path['interfaces']:
            # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
            # signal for the entire amount
            interface.reserved_bandwidth += self.reserved_bandwidth

        return self

    # def _add_rsvp_lsp_path_prototype(self, model):
    #     """
    #     TODO - this will only work if you route LSPs by groups with the same source/dest node pairing.
    #     TODO - But even that won't account for other LSPs that may be bandwidth constrained
    #     For use in stateful model
    #     Determines the LSP's path.
    #     :param model: Model object that the LSP is in
    #     :return: self with 'path' attribute
    #     """
    #
    #     # Find all demands that would take the LSP
    #     demands_for_lsp = []
    #     for demand in (demand for demand in model.demand_objects):
    #         if (demand.source_node_object == self.source_node_object and
    #                 demand.dest_node_object == self.dest_node_object):
    #             demands_for_lsp.append(demand)
    #
    #     # Find sum of all traffic for demands_for_lsp
    #     demands_for_lsp_traffic = sum((demand.traffic for demand in demands_for_lsp))
    #
    #     # Find setup bandwidth
    #     self = self._calculate_setup_bandwidth(model)
    #
    #     # Get candidate paths
    #     candidate_paths = model.get_feasible_paths(self.source_node_object.name,
    #                                                self.dest_node_object.name)
    #
    #     # Route LSP
    #     #   Options:
    #     #   a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
    #     #   b.  There are viable paths, but none with enough headroom - LSP will not be routed
    #     #   c.  LSP can route with current setup_bandwidth
    #
    #     # Option a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
    #     if candidate_paths == []:
    #         # If there are no possible paths, then LSP is Unrouted
    #         self.path = 'Unrouted'  # TODO - make this 'Unrouted - no path'
    #         self.reserved_bandwidth = 'Unrouted'  # TODO - make this 'Unrouted - no path'
    #         return self
    #
    #     # Find the path cost and path headroom for each path candidate
    #     candidate_path_info = self._find_path_cost_and_headroom(candidate_paths)
    #
    #     # Filter out paths that don't have enough headroom
    #     candidate_paths_with_enough_headroom = [path for path in candidate_path_info
    #                                             if path['baseline_path_reservable_bw'] >=
    #                                             self.setup_bandwidth]
    #
    #     # Option b. There are viable paths, but none that can
    #     # accommodate the setup_bandwidth
    #     if candidate_paths_with_enough_headroom == []:
    #         # Check to see if LSP is currently routed.
    #         # - if routed already, keep current setup and reserved bandwidth on current path
    #         # - if not routed already, LSP will be unrouted
    #         if 'Unrouted' not in self.path and self.path['interfaces'] in candidate_paths:
    #             # Update the reserved_bandwidth on each interface on the new path
    #             for interface in self.path['interfaces']:
    #                 # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
    #                 # signal for the entire amount
    #                 interface.reserved_bandwidth += self.reserved_bandwidth
    #             pdb.set_trace()
    #             return self
    #         else:
    #             self.path = 'Unrouted'  # TODO - make this 'Unrouted - setup_bandwidth'
    #             self.reserved_bandwidth = 'Unrouted'  # TODO - make this 'Unrouted - setup_bandwidth'
    #             return self
    #
    #     # Option c.  LSP can route with current setup_bandwidth
    #
    #     # Find the lowest available path metric
    #     lowest_available_metric = min([path['path_cost'] for path in
    #                                    candidate_paths_with_enough_headroom])
    #
    #     # Finally, find all paths with the lowest cost and enough headroom
    #     best_paths = [path for path in candidate_paths_with_enough_headroom
    #                   if path['path_cost'] == lowest_available_metric]
    #
    #     # If multiple paths, pick a best path at random
    #     if len(best_paths) > 1:
    #         new_path = random.choice(best_paths)
    #     else:
    #         new_path = best_paths[0]
    #
    #     self.path = new_path
    #
    #     # Since there is enough headroom, set LSP reserved_bandwidth
    #     # to setup_bandwidth
    #     self.reserved_bandwidth = self.setup_bandwidth
    #
    #     # Update the reserved_bandwidth on each interface on the new path
    #     for interface in self.path['interfaces']:
    #         # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
    #         # signal for the entire amount
    #         interface.reserved_bandwidth += self.reserved_bandwidth
    #
    #     return self

    # def _add_rsvp_lsp_path_stateful(self, model):
    #     """
    #     Determines the LSPs path, taking into account if it is currently routed.
    #     If this LSP is currently routed and takes on additional traffic and there
    #     is not a path that can handle the additional traffic, this LSP will remain
    #     signaled at the current reserved_bandwidth, but still carry the additional
    #     traffic.
    #
    #     This reflects the behavior of LSPs in a real network
    #     :param model: Model object that the LSP is in
    #     :return: self with 'path' attribute
    #     """
    #     # TODO - debug output
    #     print("LSP is {}".format(self))
    #     print()
    #
    #
    #     # Find all demands that would take the LSP
    #     demands_for_lsp = []
    #     for demand in (demand for demand in model.demand_objects):
    #         if (demand.source_node_object == self.source_node_object and
    #                 demand.dest_node_object == self.dest_node_object):
    #             demands_for_lsp.append(demand)
    #
    #     # Find sum of all traffic for demands_for_lsp
    #     demands_for_lsp_traffic = sum((demand.traffic for demand in demands_for_lsp))
    #
    #     # Find # of LSPs that have same source/dest as self
    #     num_matching_lsps = len([lsp for lsp in model.rsvp_lsp_objects if
    #                              lsp.source_node_object == self.source_node_object and
    #                              lsp.dest_node_object == self.dest_node_object])
    #
    #     # Determine ECMP split of traffic across LSPs
    #     # TODO - is this duplicating _calculate_setup_bandwidth?!
    #     self.setup_bandwidth = demands_for_lsp_traffic / num_matching_lsps
    #
    #     # Get candidate paths
    #     candidate_paths = model.get_feasible_paths(self.source_node_object.name,
    #                                                self.dest_node_object.name)
    #
    #     if candidate_paths == []:
    #         # If there are no possible paths, then LSP is Unrouted
    #         self.path = 'Unrouted - no path'
    #         self.reserved_bandwidth = 'Unrouted - no path'
    #         return self
    #     else:
    #         # Find the path cost and path headroom for each path candidate
    #         candidate_path_info = self._find_path_cost_and_headroom(candidate_paths)
    #
    #         # Filter out paths that don't have enough headroom
    #         # TODO - look here for why the 4th LSP A-D fails . . .
    #         candidate_paths_with_enough_headroom = [path for path in candidate_path_info
    #                                                 if path['baseline_path_reservable_bw'] >=
    #                                                 self.setup_bandwidth]
    #
    #         # Possible scenarios for each LSP:
    #         # There are no valid candidate paths with enough headroom:
    #         #    1. There are no viable paths to route LSP; LSP will be unrouted
    #         #    2. There are no viable paths with needed headroom,
    #         #       LSP is not routed and trying to initially signal
    #         #    3. There are no viable paths with needed headroom,
    #         #       LSP is already signaled on a still valid path and
    #         #       looking for more reserved bandwidth but none is available;
    #         #       keep the setup_bandwidth the same
    #         # There ARE valid candidate paths with enough headroom
    #         #   4. LSP does not need to adjust its setup bandwidth down
    #         #   5. LSP does need to adjust its setup bandwidth down
    #
    #         # There are no valid candidate paths with enough headroom
    #         if (len(candidate_paths_with_enough_headroom)) == 0:
    #             # 1. There are no valid paths at all;
    #             #    LSP will be unrouted
    #             if len(candidate_paths) == 0:
    #                 self.reserved_bandwidth = 'Unrouted - setup_bandwidth'
    #                 self.path = 'Unrouted - setup_bandwidth'
    #
    #             # 2.There are no viable paths with needed headroom,
    #             #   LSP is not routed and trying to initially signal
    #             elif 'Unrouted' in self.path:
    #                 self.reserved_bandwidth = 'Unrouted - setup_bandwidth'
    #                 self.path = 'Unrouted - setup_bandwidth'
    #
    #             # 3. LSP is signaled on a still valid path
    #
    #             elif 'Unrouted' not in self.path and self.path['interfaces'] in candidate_paths:
    #
    #                 # Find the LSP path's headroom; do not count the bandwidth
    #                 # reserved for self on that current path
    #                 self.path['baseline_path_reservable_bw'] = (min([interface.reservable_bandwidth
    #                                                                  for interface in self.path['interfaces']])
    #                                                             + self.reserved_bandwidth)
    #
    #                 # Current path has enough 'baseline_path_reservable_bw' to
    #                 # allow LSP to signal entire setup_bandwidth
    #                 if self.path['baseline_path_reservable_bw'] > self.setup_bandwidth:
    #
    #                     # removed reserved_bandwidth from current path
    #                     for interface in self.path['interfaces']:
    #                         interface.reserved_bandwidth -= self.reserved_bandwidth
    #
    #                     # set new reserved_bandwidth to setup_bandwidth
    #                     self.reserved_bandwidth = self.setup_bandwidth
    #
    #                     # reserve new reserved_bandwidth on current path
    #                     for interface in self.path['interfaces']:
    #                         interface.reserved_bandwidth += self.reserved_bandwidth
    #
    #                 # current path does not have enough 'baseline_path_reservable_bw' so
    #                 # stay on current path with current reserved_bandwidth
    #                 else:
    #                     self.reserved_bandwidth = self.reserved_bandwidth
    #
    #             else:
    #                 # New scenario; raise exception
    #                 msg = "new LSP routing scenario unaccounted for on lsp {}; exiting".format(self)
    #                 print(candidate_paths_with_enough_headroom)
    #                 print(msg)
    #                 raise ModelException(msg)
    #
    #         # There are valid candidate_paths with enough headroom
    #         elif len(candidate_paths_with_enough_headroom) > 0:
    #
    #             # 4.  LSP does not need to adjust its setup bandwidth down
    #
    #             # 5.  LSP does need to adjust its setup bandwidth down
    #
    #             # Find the lowest available path metric
    #             lowest_available_metric = min([path['path_cost'] for path in
    #                                            candidate_paths_with_enough_headroom])
    #
    #             # Finally, find all paths with the lowest cost and enough headroom
    #             best_paths = [path for path in candidate_paths_with_enough_headroom
    #                           if path['path_cost'] == lowest_available_metric]
    #
    #
    #             # If multiple paths, pick a best path at random
    #             if len(best_paths) > 1:
    #                 new_path = random.choice(best_paths)
    #             else:
    #                 new_path = best_paths[0]
    #
    #             # Decrement the LSP's reserved_bandwidth on
    #             # the existing path interfaces if LSP is routed
    #             # since LSP is changing path
    #             if 'Unrouted' not in self.path:
    #                 for interface in self.path['interfaces']:
    #                     interface.reserved_bandwidth -= self.reserved_bandwidth
    #
    #             self.path = new_path
    #
    #             # Since there is enough headroom, set LSP reserved_bandwidth
    #             # to setup_bandwidth
    #             self.reserved_bandwidth = self.setup_bandwidth
    #
    #             # Update the reserved_bandwidth on each interface on the new path
    #             for interface in self.path['interfaces']:
    #                 # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
    #                 # signal for the entire amount
    #                 interface.reserved_bandwidth += self.reserved_bandwidth
    #
    #         # 6.  Notify of unaccounted for scenario and error out
    #         else:
    #             msg = "new LSP routing scenario unaccounted for on lsp {} second catch; exiting".format(self)
    #             raise ModelException(msg)
    #
    #         # debug code below
    #         print("candidate_path_info:")
    #         pprint(candidate_path_info)
    #         print()
    #         print("candidate_paths_with_enough_headroom:")
    #         pprint(candidate_paths_with_enough_headroom)
    #         print()
    #         print("setup_bandwidth is {}".format(self.setup_bandwidth))
    #         print()
    #         print("lsp path is")
    #         pprint(self.path)
    #         print()
    #         print()
    #
    #
    #
    #
    #     return self

    def _find_path_cost_and_headroom(self, candidate_paths):
        """
        Returns a list of dictionaries containing the path interfaces as
        well as the path cost and headroom available on the path.
        :param candidate_paths: list of lists of Interface objects
        :return: list of dictionaries of paths: {'interfaces': path,
                                                 'path_cost': path_cost,
                                                 'baseline_path_reservable_bw': baseline_path_reservable_bw}
        """

        # List to hold info on each candidate path
        candidate_path_info = []

        # Find the path cost and path headroom for each path candidate
        for path in candidate_paths:
            path_cost = 0
            for interface in path:
                path_cost += interface.cost

            # baseline_path_reservable_bw is the max amount of traffic that the path
            # can handle without saturating a component interface
            baseline_path_reservable_bw = min([interface.reservable_bandwidth for interface in path])

            path_info = {'interfaces': path, 'path_cost': path_cost,
                         'baseline_path_reservable_bw': baseline_path_reservable_bw}

            candidate_path_info.append(path_info)

        return candidate_path_info

    def demands_on_lsp(self, model):
        """Returns demands that LSP is transporting."""
        demand_list = []
        for demand in (demand for demand in model.demand_objects):
            if self in demand.path:
                demand_list.append(demand)

        return demand_list

    def traffic_on_lsp(self, model):  # TODO - do getter/setter for this? experimental
        """
        Returns the amount of traffic on the LSP
        :param model: Model object for LSP
        :return: Units of traffic on the LSP
        """

        # Find all LSPs with same source and dest as self
        parallel_routed_lsps = self.routed_parallel_lsp_group(model)
        total_traffic = sum([demand.traffic for demand in self.demands_on_lsp(model)])

        if len(parallel_routed_lsps) > 0:
            traffic_on_lsp = total_traffic / len(parallel_routed_lsps)
        else:
            traffic_on_lsp = total_traffic

        return traffic_on_lsp

    def effective_metric(self, model):
        """Returns the metric for the best path. This value will be the
        shortest possible path from LSP's source to dest, regardless of
        whether the LSP takes that shortest path or not."""

        return model.get_shortest_path(self.source_node_object.name,
                                       self.dest_node_object.name)['cost']

    def actual_metric(self, model):
        """Returns the metric sum of the interfaces that the LSP actually
        transits."""
        if 'Unrouted' in self.path:
            metric = 'Unrouted'
        else:
            metric = sum([interface.cost for interface in self.path['interfaces']])

        return metric

    def route_lsp(self, model, setup_bandwidth):
        """
        Used in Model object to route each LSP
        :param model:
        :return:
        """

        # Calculate setup bandwidth
#        self._calculate_setup_bandwidth(model)
        self.setup_bandwidth = setup_bandwidth

        # Route the LSP
        self._add_rsvp_lsp_path(model, setup_bandwidth)

        return self
