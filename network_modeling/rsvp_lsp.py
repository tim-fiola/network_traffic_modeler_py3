"""A class to represent an RSVP label-switched-path in the network model """

from pprint import pprint
from .model_exception import ModelException

import random
import pdb


# For when the model has both LSPs but not a full LSP mesh, 
# - create the LSP model first
# - if there are not paths between all nodes, find those specific paths
#    in a model made up of just interfaces

class RSVP_LSP(object):
    """A class to represent an RSVP label-switched-path in the network model """
    
    def __init__(self, source_node_object, dest_node_object, 
                                    lsp_name = 'none'):

        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.lsp_name = lsp_name
        self.path = 'Unrouted'
        self.reserved_bandwidth = 'Unrouted'
        self.setup_bandwidth = 'Unrouted'
#        self.demands = []
        
        
    @property
    def _key(self):
        """Unique identifier for the rsvp lsp: (Node('source'), 
        Node('dest'), name)"""
        return (self.source_node_object, self.dest_node_object, self.lsp_name)

    def __repr__(self):
        return 'RSVP_LSP(source = %s, dest = %s, name = %r)'%\
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
            candidate_path_info = self._find_path_cost_and_headroom(candidate_paths, model)

            # Filter out paths that don't have enough headroom
            candidate_paths_with_enough_headroom = [path for path in candidate_path_info
                                                    if path['baseline_path_reservable_bw'] >=
                                                    self.setup_bandwidth]

            # Scenarios for each LSP:
            # 1.There are no viable paths with needed headroom,
            #    LSP is not routed and trying to initially signal
            # 2. There are no viable paths with needed headroom,
            #    LSP is already signaled and looking for more
            #    reserved bandwidth; LSP current path is valid so keep it
            #    on the same path with current reserved_bandwidth:
            # 3. LSP was routed but that path failed.  There are
            #    no other paths to route on with the required
            #    reservable_bandwidth; don't route the LSP
            # 4. LSP did not change path, but something else happened that
            #    will allow it to signal for its full setup bandwidth if it
            #    was not able to before
            # 5. There are viable paths with enough headroom


            # There are no valid candidate paths with enough headroom
            if (len(candidate_paths_with_enough_headroom)) == 0:
                # 3. There are no paths to route;
                #    LSP will be unrouted
                if len(candidate_paths) == 0:
                    self.reserved_bandwidth = 'Unrouted'
                    self.path = 'Unrouted'
                    print('{}; scenario 3'.format(self.lsp_name))

                # 1.There are no viable paths with needed headroom,
                #   LSP is not routed and trying to initially signal
                elif self.path == 'Unrouted':
                    self.reserved_bandwidth = 'Unrouted'
                    self.path = 'Unrouted'
                    print('{}; scenario 1'.format(self.lsp_name))

                # 2. There are no viable paths with needed headroom,
                #    LSP is already signaled on a still valid path and
                #    looking for more reserved bandwidth but none is available;
                #    keep the setup_bandwidth the same
                elif self.path != 'Unrouted' and \
                     self.path['interfaces'] in candidate_paths: # and \
                     # self.setup_bandwidth > self.path['baseline_path_reservable_bw']:
                    print('{}; scenario 2'.format(self.lsp_name))
                    pdb.set_trace()
                    self.reserved_bandwidth = self.reserved_bandwidth

                else:
                    msg = "new LSP routing scenario unaccounted for on lsp {}; exiting".format(self)
                    print(candidate_paths_with_enough_headroom)
                    print(msg)  # TODO - remove debug output
                    pdb.set_trace()
                    raise ModelException(msg)

            # There are valid candidate_paths with enough headroom
            elif len(candidate_paths_with_enough_headroom) > 0:
                self.reserved_bandwidth = self.setup_bandwidth
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
                if self.path != 'Unrouted':
                    for interface in self.path['interfaces']:
                        interface.reserved_bandwidth -= self.reserved_bandwidth

                self.path = new_path

                # Update the reserved_bandwidth on each interface on the new path
                for interface in self.path['interfaces']:
                    # Make LSP reserved_bandwidth = setup_bandwidth because it is able to
                    # signal for the entire amount
#                    self.reserved_bandwidth = self.setup_bandwidth
                    interface.reserved_bandwidth += self.reserved_bandwidth

#                 # 4. LSP was routed and did not change path, but something else may have happened
#                 #    that will allow it to signal for its full setup bandwidth if it was not able
#                 #    to before
#                 if self.path != 'Unrouted' and \
#                      self.setup_bandwidth < self.path['baseline_path_reservable_bw']:
#                     print('{}; scenario 4'.format(self.lsp_name))
#
# #                    pdb.set_trace()
#                     self.reserved_bandwidth = self.setup_bandwidth

            # 6.  Notify of unaccounted for scenario and error out
            else:
                msg = "new LSP routing scenario unaccounted for on lsp {} second catch; exiting".format(self)
                raise ModelException(msg)

        return self

        
    def _find_path_cost_and_headroom(self, candidate_paths, model):
        """
        Returns a list of dictionaries containing the path interfaces as
        well as the path cost and headroom available on the path.
        :param candidate_paths: list of lists of Interface objects
        :param model: Model
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
            if self.lsp_name == 'test2':
                pdb.set_trace()

        return candidate_path_info


    def lsp_can_route(self, model):
        """Can this LSP route?"""
        # TODO - what is lsp_can_route for?  I don't recall
        pass

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

    def route_lsp(self, model):
        
        # Calculate setup bandwidth
        self._calculate_setup_bandwidth(model)
        
        # Route the LSP
        self._add_rsvp_lsp_path(model)
        
        return self
        
