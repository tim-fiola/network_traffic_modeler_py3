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

        demand_path = model.get_shortest_path(self.source_node_object.name,
                                                     self.dest_node_object.name)['path']
        if demand_path == []:
            demand_path = 'Unrouted'
        
        self.path = demand_path

        return self 

