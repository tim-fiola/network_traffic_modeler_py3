"""A Demand is a traffic load that traverses the network from a source Node
to a destination Node"""

import pdb

class Demand(object):
    """A representation of traffic load on the modeled network"""

    def __init__(self, source_node_object, dest_node_object, traffic = 0, name = 'none'):
        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.traffic = traffic
        self.name = name
        self.path = 'Unrouted'
        
        # Validate traffic value
        if not(isinstance(traffic, (int, float))) or traffic < 0:
            raise ValueError('Must be a positive int or float')

    @property
    def _key(self):
        """Unique identifier for the demand: (Node('source'), Node('dest'), name)"""
        return (self.source_node_object, self.dest_node_object, self.name)

    def __repr__(self):
        return 'Demand(source = %s, dest = %s, traffic = %s, name = %r)'%\
                                                (self.source_node_object.name,
                                                self.dest_node_object.name,
                                                self.traffic,
                                                self.name)

    def _add_demand_path(self, model):
        """Adds a path to a demand"""

        # Find if there is an LSP with source/dest same as demand source/dest
        #if len(model.rsvp_lsp_objects) > 0:
            #demand_path = []
            #for lsp in (lsp for lsp in model.rsvp_lsp_objects):
                #if (lsp.source_node_object == self.source_node_object and \
                    #lsp.dest_node_object == self.dest_node_object):
                    #demand_path.append(lsp)
                #else: # no LSP matches demand source/dest pair
 
        # Find if there is an LSP with source/dest same as demand source/dest                
        demand_path = []
        
        # Find all LSPs that can carry the demand:
        for lsp in (lsp for lsp in model.rsvp_lsp_objects):
            if (lsp.source_node_object == self.source_node_object and \
                    lsp.dest_node_object == self.dest_node_object and \
                    lsp.path != 'Unrouted'):
                demand_path.append(lsp)
            
        # If demand can't be carried by LSP, do shortest path routing
        if demand_path == []:
            demand_path = model.get_shortest_path(self.source_node_object.name,
                                            self.dest_node_object.name)['path']
        
        # This code turns on capability to have demand take an RSVP LSP
        for lsp in (lsp for lsp in model.rsvp_lsp_objects):
            if (lsp.source_node_object == self.source_node_object and \
                lsp.dest_node_object == self.dest_node_object and \
                lsp.path != 'Unrouted'):
                print()
                print("# DEBUG lsp", lsp, self)
                status = 'lsp routing'
                #pdb.set_trace()
                demand_path.append(lsp)
            ## If no LSPs, use shortest path IGP routing
            else:
                print()
                print("# DEBUG no LSP", lsp, self)
                status = 'shortest path routing'
                #pdb.set_trace()
                demand_path = model.get_shortest_path(self.source_node_object.name,
                                                self.dest_node_object.name)['path']

        # TODO - remove this legacy code (does not support LSP routing)
        #demand_path = model.get_shortest_path(self.source_node_object.name,
        #                                             self.dest_node_object.name)['path']

        if demand_path == []:
            demand_path = 'Unrouted'
        
        self.path = demand_path

        return self 


