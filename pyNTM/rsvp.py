"""A class to represent an RSVP label-switched-path in the network model """

import random
from .exceptions import ModelException


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
                 lsp_name='none', configured_setup_bandwidth=None):

        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.lsp_name = lsp_name
        self.path = 'Unrouted - initial'
        self.reserved_bandwidth = 'Unrouted - initial'
        self._setup_bandwidth = 'Unrouted - initial'
        self.configured_setup_bandwidth = configured_setup_bandwidth

    @property
    def _key(self):
        """Unique identifier for the rsvp lsp: (Node('source').name, Node('dest').name, name)"""
        return (self.source_node_object.name, self.dest_node_object.name, self.lsp_name)

    def __repr__(self):
        return 'RSVP_LSP(source = %s, dest = %s, lsp_name = %r)' % \
               (self.source_node_object.name,
                self.dest_node_object.name,
                self.lsp_name)

    def _find_path_cost_and_headroom_routed_lsp(self, candidate_paths):
        """
        Returns a list of dictionaries containing the path interfaces as
        well as the path cost and headroom available on the path.  This def
        takes into account that self is a routed LSP and is looking to
        signal for additional bandwidth.  As such, this def adds back its
        existing reserved_bandwidth to any Interface in a path in
        candidate_paths that it is already signaled on.
        :param candidate_paths: list of lists of Interface objects
        :return: list of dictionaries of paths: {'interfaces': path,
                                                 'path_cost': path_cost,
                                                 'baseline_path_reservable_bw': baseline_path_reservable_bw}
        """

        # List to hold info on each candidate path
        candidate_path_info = []

        # Find the path cost and path headroom for each path candidate
        for path in candidate_paths['path']:
            path_cost = 0
            for interface in path:
                path_cost += interface.cost

            # Find the path cost and reservable bandwidth on each path.
            # If the path you are examining has an interface that is on
            # the LSP's current path, add back in the
            # reserved bandwidth for the LSP to that interface
            proto_reservable_bw = {}
            for interface in path:
                if interface in self.path['interfaces']:
                    proto_reservable_bw[interface] = interface.reservable_bandwidth + self.reserved_bandwidth
                else:
                    proto_reservable_bw[interface] = interface.reservable_bandwidth

            # baseline_path_reservable_bw is the max amount of traffic
            # that the path can handle without using more than a component
            # interface's reservable_bandwidth
            baseline_path_reservable_bw = min(proto_reservable_bw.values())

            path_info = {'interfaces': path, 'path_cost': path_cost,
                         'baseline_path_reservable_bw': baseline_path_reservable_bw}

            candidate_path_info.append(path_info)

        return candidate_path_info

    @property
    def setup_bandwidth(self):
        """
        The bandwidth the LSP attempts to signal for.
        :return: the bandwidth the LSP attempts to signal for
        """

        return self._setup_bandwidth

    @setup_bandwidth.setter
    def setup_bandwidth(self, proposed_setup_bw):
        """
        Puts guardrails on the setup bandwidth for the RSVP LSP
        :param proposed_setup_bw: setup bandwidth value to be evaluated
        :return:
        """

        # Check for configured_setup_bandwidth
        if self.configured_setup_bandwidth:
            self._setup_bandwidth = float(self.configured_setup_bandwidth)
        elif proposed_setup_bw >= 0:
            self._setup_bandwidth = float(proposed_setup_bw)
        elif proposed_setup_bw < 0:
            msg = "setup_bandwidth must be 0 or greater"
            raise ModelException(msg)

    def find_rsvp_path_w_bw(self, requested_bandwidth, model):
        """
        Will search the topology of 'model' for a path for self that has at least
        'requested_bandwidth' of reservable_bandwidth.  If there is one, will update
        self.path; if not, will keep same self.path.  When checking paths,
        this def will take into account its own reserved bandwidth if it
        is looking at paths that have interfaces already in its
        path['interfaces'] list.

        :param model: Model object to search; this will typically be a Model
        object consisting of only non-failed interfaces
        :param requested_bandwidth: number of units set for reserved_bandwidth
        :return: self with the current or updated path info
        """

        # Get candidate paths; only include interfaces that have requested_bandwidth
        # of reservable_bandwidth
        candidate_paths = model.get_shortest_path_for_routed_lsp(self.source_node_object.name,
                                                                 self.dest_node_object.name,
                                                                 self, requested_bandwidth)

        # Find the path cost and path headroom for each path candidate
        candidate_path_info = self._find_path_cost_and_headroom_routed_lsp(candidate_paths)

        # If there are no paths with enough headroom, return self
        if len(candidate_path_info) == 0:
            return self
        # If there is only one path with enough headroom, make that self.path
        elif len(candidate_path_info) == 1:
            self.path = candidate_path_info[0]
        # If there is more than one path with enough headroom,
        # choose one at random and make that self.path
        elif len(candidate_path_info) > 1:
            self.path = random.choice(candidate_path_info)

        self.reserved_bandwidth = requested_bandwidth
        self.setup_bandwidth = requested_bandwidth
        return self

    def _add_rsvp_lsp_path(self, model):
        """
        Determines the LSP's path regardless of whether it was previously routed
        or not (non stateful).
        If this LSP is currently routed and takes takes on additional traffic
        and there is not a path that can handle the additional traffic,
        this LSP will not signal.
        :param model: Model object that the LSP is in
        :return: self with 'path' attribute
        """

        # Try all shortest paths with needed reservable bandwidth
        candidate_paths = model.get_shortest_path(self.source_node_object.name,
                                                  self.dest_node_object.name, self.setup_bandwidth)

        # Route LSP
        #   Options:
        #   a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
        #   b.  LSP can route with current setup_bandwidth

        # Option a.  There are no viable paths on the topology to route LSP - LSP will be unrouted
        if candidate_paths['path'] == []:
            # If there are no possible paths, then LSP is Unrouted
            self.path = 'Unrouted'
            self.reserved_bandwidth = 'Unrouted'
            return self

        self.path = {}

        # Find the path cost and path headroom for each path candidate
        candidate_path_info = self._find_path_cost_and_headroom(candidate_paths)

        # Option b.  LSP can route with current setup_bandwidth

        # If multiple lowest_metric_paths, find those with fewest hops
        if len(candidate_path_info) > 1:
            fewest_hops = min([len(path['interfaces']) for path in candidate_path_info])
            lowest_hop_count_paths = [path for path in candidate_path_info if len(path['interfaces']) == fewest_hops]
            if len(lowest_hop_count_paths) > 1:
                new_path = random.choice(lowest_hop_count_paths)
            else:
                new_path = lowest_hop_count_paths[0]
        else:
            new_path = candidate_path_info[0]

        self.path = new_path

        # Since there is enough headroom, set LSP
        # reserved_bandwidth to setup_bandwidth
        self.reserved_bandwidth = self.setup_bandwidth

        # Update the reserved_bandwidth on each interface on the new path
        for interface in self.path['interfaces']:
            # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
            # signal for the entire amount
            interface.reserved_bandwidth += self.reserved_bandwidth

        return self

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
        for path in candidate_paths['path']:
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

    def traffic_on_lsp(self, model):
        """
        Returns the amount of traffic on the LSP
        :param model: Model object for LSP
        :return: Units of traffic on the LSP
        """

        # Find all LSPs with same source and dest as self
        parallel_lsp_groups = model.parallel_lsp_groups()
        total_traffic = sum([demand.traffic for demand in self.demands_on_lsp(model)])

        key = "{}-{}".format(self.source_node_object.name, self.dest_node_object.name)
        parallel_routed_lsps = [lsp for lsp in parallel_lsp_groups[key] if 'Unrouted' not in lsp.path]

        traffic_on_lsp = total_traffic / len(parallel_routed_lsps)

        return traffic_on_lsp

    def effective_metric(self, model):
        """Returns the metric for the best path. This value will be the
        shortest possible path from LSP's source to dest, regardless of
        whether the LSP takes that shortest path or not."""

        return model.get_shortest_path(self.source_node_object.name,
                                       self.dest_node_object.name, needed_bw=0)['cost']

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
        self.setup_bandwidth = setup_bandwidth

        # Route the LSP
        self._add_rsvp_lsp_path(model)

        return self
