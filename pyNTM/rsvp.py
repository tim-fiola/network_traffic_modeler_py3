"""A class to represent an RSVP label-switched-path in the network model """

import random
from .exceptions import ModelException


class RSVP_LSP(object):
    """A class to represent an RSVP label-switched-path in the network model

    source_node_object: Node where LSP ingresses the network (LSP starts here)

    dest_node_object: Node where LSP egresses the network (LSP ends here)

    lsp_name: name of LSP

    path::

        will either be 'Unrouted' or be a dict containing the following -
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
        self._traffic_from_shortcuts = 0

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
        :return: None
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

    def demands_on_lsp(self, model):
        """
        Returns demands in model object that LSP is transporting.

        :param model: model object containing LSP
        :return: List of demands in model object that LSP carries
        """
        from .flex_model import FlexModel
        demand_set = set()
        for demand in (demand for demand in model.demand_objects):
            if self in demand.path:
                demand_set.add(demand)
            if isinstance(model, FlexModel):
                # Look for the demands from IGP shortcuts
                for dmd_path in demand.path:
                    if isinstance(dmd_path, list) and self in dmd_path:
                        demand_set.add(demand)

        return list(demand_set)

    def traffic_on_lsp(self, model):
        """
        Returns the amount of traffic on the LSP

        :param model: Model object for LSP
        :return: Units of traffic on the LSP
        """

        # Find all LSPs with same source and dest as self
        parallel_lsp_groups = model.parallel_lsp_groups()  # TODO - can this be optimized? cache it in model object

        # TODO - this is coming up wrong; it is assuming that all demand traffic will
        #  take the LSP, but in IGP shortcuts, not all demand traffic will take LSPs; some
        #  demands may be routed via igp and split before it gets on an LSP
        # TODO - need to come up with split factor for demand in its path (perhaps enhanced_path object?)
        total_traffic = sum([demand.traffic for demand in self.demands_on_lsp(model)])

        key = "{}-{}".format(self.source_node_object.name, self.dest_node_object.name)
        parallel_routed_lsps = [lsp for lsp in parallel_lsp_groups[key] if 'Unrouted' not in lsp.path]

        from .performance_model import PerformanceModel, Model
        if isinstance(model, PerformanceModel) or isinstance(model, Model):
            # If it's PerformanceModel, IGP shortcuts not supported, all traffic
            # routes on the parallel LSPs
            source_dest_match_traffic = total_traffic / len(parallel_routed_lsps)
        else:
            source_dest_match_traffic = 0
            # Account for possible IGP shortcut splits
            for demand_object in self.demands_on_lsp(model):
                # from pprint import pprint  # TODO - debug
                # print(demand_object)
                # pprint(demand_object.path_detail)
                # import pdb
                # pdb.set_trace()

                for path, path_data in demand_object.path_detail.items():
                    # Check if self is in path_data
                    if self in path_data['interfaces']:
                        source_dest_match_traffic += path_data['path_traffic']

        return source_dest_match_traffic + self._traffic_from_shortcuts

    def effective_metric(self, model):
        """
        Returns the metric for the best path. This value will be the
        metric for the shortest possible path from LSP's source to dest,
        regardless of whether the LSP takes that shortest path or not.

        :param model: model object containing self
        :return: metric for the LSP's shortest possible path
        """

        return model.get_shortest_path(self.source_node_object.name,
                                       self.dest_node_object.name, needed_bw=0)['cost']

    def actual_metric(self, model):
        """
        Returns the metric sum of the interfaces that the LSP actually
        transits.

        :param model: model object containing self
        :return: sum of the metrics of the Interfaces that the LSP transits
        """
        if 'Unrouted' in self.path:
            metric = 'Unrouted'

        else:
            metric = sum([interface.cost for interface in self.path['interfaces']])

        return metric
