"""A class to represent an RSVP label-switched-path in the network model """

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
        
        # Find all demands that would ride the LSP
        demand_list = []
        for demand in model.demand_objects:
            if demand.source_node_object == self.source_node_object and \
                demand.dest_node_object == self.dest_node_object:
                    demand_list.append(demand)            

        sum_demand_traffic = sum([demand.traffic for demand in demand_list])
        
        # Calculate the amount of bandwidth for each demand
        all_lsps_src_to_dest = [lsp for lsp in model.rsvp_lsp_objects if \
            (lsp.source_node_object == self.source_node_object and \
            lsp.dest_node_object == self.dest_node_object)]
           
        needed_bw = sum_demand_traffic/len(all_lsps_src_to_dest)
        
        self.setup_bandwidth = needed_bw
        
        return self
        
    def _add_rsvp_lsp_path(self, model):
        """Determines the LSP's path"""
        
        # Get candidate paths
        candidate_paths = model.get_feasible_paths(self.source_node_object.name, 
                                    self.dest_node_object.name)
        if candidate_paths == []:
            self.path = 'Unrouted'
            self.reserved_bandwidth = 'Unrouted'
        else:
            # Find the path cost and path headroom for each path candidate
            candidate_path_info = \
                self._find_path_cost_and_headroom(candidate_paths, model)
            
            # Filter out paths that don't have enough headroom
            candidate_paths_with_enough_headroom = [path for path in \
                candidate_path_info if path['baseline_path_reservable_bw'] >= \
                self.setup_bandwidth]
                
            # 1.There are no viable paths with needed headroom,
            #   LSP is not routed and trying to initially signal
            if len(candidate_paths_with_enough_headroom) == 0 and \
                        self.path == 'Unrouted':
                self.reserved_bandwidth = 'Unrouted'
                self.path = 'Unrouted'
                
            # 2. There are no viable paths with needed headroom,                
            #    LSP is already signaled and looking for more 
            #    reserved bandwidth:
            elif len(candidate_paths_with_enough_headroom) == 0 and \
                    self.path != 'Unrouted':
                # Keep the current setup bandwidth and path
                self.reserved_bandwidth = self.reserved_bandwidth
                self.path = self.path
            # 3. There are viable paths with enough headroom
            else:
                
                
                ### TODO - reservable_bandwidth is not updating? - debug
                
                
                self.reserved_bandwidth = self.setup_bandwidth
                # Find the lowest available path metric
                
                lowest_available_metric = min([path['path_cost'] for path in \
                    candidate_paths_with_enough_headroom])
                    
                # Finally, find all paths with the lowest cost and enough headroom
                best_paths = [ path for path in candidate_paths_with_enough_headroom \
                                if path['path_cost'] == lowest_available_metric ]
                
                # If multiple paths, pick a best path at random
                if len(best_paths)> 1:
                    self.path = random.choice(best_paths)
                else:
                    self.path = best_paths[0]
         
        return self  
        
    def _find_path_cost_and_headroom(self, candidate_paths, model):
        """Returns a list of dictionaries containing the path interfaces as
        well as the path cost and headroom available on the path."""

        # List to hold info on each candidate path
        candidate_path_info = []
#        path_counter = 0

        # Find the path cost and path headroom for each path candidate
        for path in candidate_paths:
            path_cost = 0
            for interface in path:
                path_cost += interface.cost
            # Path headroom is the max amount of traffic that the path 
            # can handle without saturating a component interface
            baseline_path_reservable_bw = min([interface.reservable_bandwidth for interface in path])
            # amount of additional bw on path available for reservation
            # if self.path != 'Unrouted':
            #     available_bw = int(path_headroom) - int(self.reserved_bandwidth)
            # else:
            #     available_bw = 'NA'

            path_info = {'interfaces': path, 'path_cost': path_cost,
                         'baseline_path_reservable_bw': baseline_path_reservable_bw}
            
            candidate_path_info.append(path_info)
#            path_counter += 1
            
        return candidate_path_info

    def lsp_can_route(self, model):
        """ """
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
        
