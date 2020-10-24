"""A Demand is a traffic load that traverses the network from a source Node
to a destination Node"""


class Demand(object):
    """
    A representation of traffic load on the modeled network
    """

    def __init__(self, source_node_object, dest_node_object, traffic=0, name='none'):
        self.source_node_object = source_node_object
        self.dest_node_object = dest_node_object
        self.traffic = traffic
        self.name = name
        self.path = 'Unrouted'
        self._path_detail = 'Unrouted_detail'

        # Validate traffic value
        if not(isinstance(traffic, (int, float))) or traffic < 0:
            raise ValueError('Must be a positive int or float')

    @property
    def _key(self):
        """Unique identifier for the demand: (Node('source').name, Node('dest').name, name)"""
        return (self.source_node_object.name, self.dest_node_object.name, self.name)

    def __repr__(self):
        return 'Demand(source = %s, dest = %s, traffic = %s, name = %r)' % \
               (self.source_node_object.name,
                self.dest_node_object.name,
                self.traffic,
                self.name)

    def _add_demand_path(self, model):
        """
        Adds path(s) the the demand for the given model the demand routes through.

        :param model: Model object
        :return: list of paths the demand takes or 'Unrouted' string
        """

        # Find if there is an LSP with source/dest same as demand source/dest
        demand_path = []

        # Find all LSPs that can carry the demand:
        for lsp in (lsp for lsp in model.rsvp_lsp_objects):
            if (lsp.source_node_object == self.source_node_object and
                    lsp.dest_node_object == self.dest_node_object and
                    'Unrouted' not in lsp.path):

                demand_path.append(lsp)

        # If demand can't be carried by LSP, do shortest path routing
        if demand_path == []:
            demand_path = model.get_shortest_path(self.source_node_object.name,
                                                  self.dest_node_object.name, needed_bw=0)['path']

        if demand_path == []:
            demand_path = 'Unrouted'

        self.path = demand_path

        return self

    @property
    def path_detail(self):
        return self._path_detail
