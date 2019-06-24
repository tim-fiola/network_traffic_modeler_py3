"""A class to represent an RSVP label-switched-path in the network model """

from pprint import pprint
from .model_exception import ModelException

import random
import pdb

# TODO - add call to return traffic on LSP

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
        - path_cost: sum of costs of the interfaces (same as self.actual_metric) # TODO - make these the same name
        - baseline_path_reservable_bw: the amount of reservable bandwidth
            available on the LSP's path when the LSP was signaled, not inclusive
            of the bandwidth already reserved by this LSP on that path (if any)

    reserved_bandwidth: amount of bandwidth reserved by this LSP

    setup_bandwidth: amount of bandwidth this LSP wants to signal for

    """
    
    def __init__(self, source_node_object, dest_node_object, 
                                    lsp_name = 'none'):

        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.lsp_name = lsp_name
        self.path = 'Unrouted'
        self.reserved_bandwidth = 'Unrouted'
        self.setup_bandwidth = 'Unrouted'

    @property
    def _key(self):
        """Unique identifier for the rsvp lsp: (Node('source'), 
        Node('dest'), name)"""
        return (self.source_node_object, self.dest_node_object, self.lsp_name)

    def __repr__(self):
        return 'RSVP_LSP(source = %s, dest = %s, lsp_name = %r)'%\
                                                (self.source_node_object.name,
                                                self.dest_node_object.name,
                                                self.lsp_name)

    def _calculate_setup_bandwidth(self, model):
        """Find amount of bandwidth to reserve for LSP"""
        # TODO - this is not optimal because it will do this math for each LSP in group with same source/dest

        # Find all demands that would ride the LSP
        demand_list = []
        for demand in model.demand_objects:
            if demand.source_node_object == self.source_node_object and \
                demand.dest_node_object == self.dest_node_object:
                    demand_list.append(demand)            

        sum_demand_traffic = sum([demand.traffic for demand in demand_list])
        
        # Calculate the amount of bandwidth for each demand
        all_lsps_src_to_dest = [lsp for lsp in model.rsvp_lsp_objects if \
            (lsp.source_node_object == self.source_node_object and
             lsp.dest_node_object == self.dest_node_object)]
           
        needed_bw = sum_demand_traffic/len(all_lsps_src_to_dest)
        
        self.setup_bandwidth = needed_bw

        return self
        
    def _add_rsvp_lsp_path(self, model):
        """Determines the LSP's path"""

        # Find all demands that would take the LSP
        demands_for_lsp = []
        for demand in (demand for demand in model.demand_objects):
            if (demand.source_node_object == self.source_node_object and
                        demand.dest_node_object == self.dest_node_object):
                demands_for_lsp.append(demand)

        # Find sum of all traffic for demands_for_lsp
        demands_for_lsp_traffic = sum((demand.traffic for demand in demands_for_lsp))

        # Find # of LSPs that have same source/dest as self
        num_matching_lsps = len([lsp for lsp in model.rsvp_lsp_objects if
             lsp.source_node_object == self.source_node_object and
             lsp.dest_node_object == self.dest_node_object])

        # Determine ECMP split of traffic across LSPs
        self.setup_bandwidth = demands_for_lsp_traffic/num_matching_lsps

        # Get candidate paths
        candidate_paths = model.get_feasible_paths(self.source_node_object.name, 
                                    self.dest_node_object.name)

        if candidate_paths == []:
            # If there are no possible paths, then LSP is Unrouted
            self.path = 'Unrouted'
            self.reserved_bandwidth = 'Unrouted'
        else:
            # Find the path cost and path headroom for each path candidate
            candidate_path_info = self._find_path_cost_and_headroom(candidate_paths)

            # Filter out paths that don't have enough headroom
            candidate_paths_with_enough_headroom = [path for path in candidate_path_info
                                                    if path['baseline_path_reservable_bw'] >=
                                                    self.setup_bandwidth]

            # Possible scenarios for each LSP:
            # There are no valid candidate paths with enough headroom:
            #    1. There are no viable paths to route LSP; LSP will be unrouted
            #    2. There are no viable paths with needed headroom,
            #       LSP is not routed and trying to initially signal
            #    3. There are no viable paths with needed headroom,
            #       LSP is already signaled on a still valid path and
            #       looking for more reserved bandwidth but none is available;
            #       keep the setup_bandwidth the same
            # 4. There ARE valid candidate paths with enough headroom

            # There are no valid candidate paths with enough headroom
            if (len(candidate_paths_with_enough_headroom)) == 0:
                # 1. There are no valid paths at all;
                #    LSP will be unrouted
                if len(candidate_paths) == 0:
                    self.reserved_bandwidth = 'Unrouted'
                    self.path = 'Unrouted'

                # 2.There are no viable paths with needed headroom,
                #   LSP is not routed and trying to initially signal
                elif self.path == 'Unrouted':
                    self.reserved_bandwidth = 'Unrouted'
                    self.path = 'Unrouted'

                # 3. LSP is signaled on a still valid path

                elif self.path != 'Unrouted' and \
                     self.path['interfaces'] in candidate_paths:


                    # Find the LSP path's headroom; do not count the bandwidth
                    # reserved for self on that current path
                    self.path['baseline_path_reservable_bw'] = (min([interface.reservable_bandwidth
                                                                    for interface in self.path['interfaces']])
                                                                + self.reserved_bandwidth)

                    # Current path has enough 'baseline_path_reservable_bw' to
                    # allow LSP to signal entire setup_bandwidth
                    if self.path['baseline_path_reservable_bw'] > self.setup_bandwidth:

                        # removed reserved_bandwidth from current path
                        for interface in self.path['interfaces']:
                            interface.reserved_bandwidth -= self.reserved_bandwidth

                        # set new reserved_bandwidth to setup_bandwidth
                        self.reserved_bandwidth = self.setup_bandwidth

                        # reserve new reserved_bandwidth on current path
                        for interface in self.path['interfaces']:
                            interface.reserved_bandwidth += self.reserved_bandwidth

                    # current path does not have enough 'baseline_path_reservable_bw' so
                    # stay on current path with current reserved_bandwidth
                    else:
                        self.reserved_bandwidth = self.reserved_bandwidth

                else:
                    # New scenario; raise exception
                    msg = "new LSP routing scenario unaccounted for on lsp {}; exiting".format(self)
                    print(candidate_paths_with_enough_headroom)
                    print(msg)
                    raise ModelException(msg)

            # 4. There are valid candidate_paths with enough headroom
            elif len(candidate_paths_with_enough_headroom) > 0:

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

                # Decrement the LSP's reserved_bandwidth on
                # the existing path interfaces if LSP is routed
                # since LSP is changing path
                if self.path != 'Unrouted':
                    for interface in self.path['interfaces']:
                        interface.reserved_bandwidth -= self.reserved_bandwidth

                self.path = new_path

                # Since there is enough headroom, set LSP reserved_bandwidth
                # to setup_bandwidth
                self.reserved_bandwidth = self.setup_bandwidth

                # Update the reserved_bandwidth on each interface on the new path
                for interface in self.path['interfaces']:
                    # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
                    # signal for the entire amount
                    interface.reserved_bandwidth += self.reserved_bandwidth

            # 6.  Notify of unaccounted for scenario and error out
            else:
                msg = "new LSP routing scenario unaccounted for on lsp {} second catch; exiting".format(self)
                raise ModelException(msg)

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
            
                            
    def effective_metric(self, model):
        """Returns the metric for the best path. This value will be the 
        shortest possible path from LSP's source to dest, regardless of 
        whether the LSP takes that shortest path or not."""
        
        return model.get_shortest_path(self.source_node_object.name,
            self.dest_node_object.name)['cost']

      
    def actual_metric(self, model):
        """Returns the metric sum of the interfaces that the LSP actually
        transits."""
        if self.path == 'Unrouted':
            metric = 'Unrouted'
        else:            
            metric = sum([interface.cost for interface in self.path['interfaces']])
        
        return metric

    def route_lsp(self, model): # TODO - is this call used anywhere?
        
        # Calculate setup bandwidth
        self._calculate_setup_bandwidth(model)
        
        # Route the LSP
        self._add_rsvp_lsp_path(model)
        
        return self
        
