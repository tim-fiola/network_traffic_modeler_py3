
class Weathermap(object):

    def __init__(self, model):
        self.demand_sources = []
        self.demand_destinations = []
        self.lsp_sources = []
        self.lsp_destinations = []
        self.node_list = []
        self._no_selected_interface_text = 'no int selected'
        self._no_selected_demand_text = 'no demand selected'
        self._no_selected_lsp_text = 'no lsp selected'
        self.demand_color = '#DB7093'
        self.lsp_color = '#610B21'
        self.interface_color = '#ADD8E6'

        self.model = model
        self.util_ranges = {'0-24': 'royalblue',
                            '25-49': 'green',
                            '50-74': 'yellow',
                            '75-89': 'orangered',
                            '90-99': 'darkred',
                            '100+': 'darkviolet',
                            'failed': 'grey'}
        self.stylesheet = [
            {
                "selector": 'edge',
                "style": {
                    "mid-target-arrow-color": "blue",
                    "mid-target-arrow-shape": "vee",
                    "curve-style": "bezier",
                    'label': "data(circuit_id)",
                    'line-color': "data(group)",
                    "font-size": "9px",
                    "opacity": 0.4,
                }
            },
            {
                "selector": "edge[group=\"failed\"]",
                "style": {
                    "line-color": "#808080",
                    "curve-style": "bezier",
                    'label': "data(circuit_id)",
                    'line-style': 'dashed'
                }
            },
            {
                "selector": "node",
                "style": {
                    "label": "data(label)",
                    'background-color': 'lightgrey',
                    "font-size": "9px",
                    "text-halign": 'center',
                    'text-valign': 'center',
                    'text-wrap': 'wrap',
                    'width': '20px',
                    'height': '20px',
                    'border-width': 1,
                    'border-color': 'dimgrey'
                }
            },
            {
                "selector": 'node[group=\"failed\"]',
                "style": {
                    'text-color': '#FF0000',
                    'shape': 'rectangle',
                    'label': "data(label)",
                    'background-color': 'red'

                }
            },
            {
                "selector": 'node[group=\"midpoint\"]',
                "style": {
                    'label': "data(label)",
                    'shape': 'rectangle',
                    'width': '10px',
                    'height': '10px'
                }
            },
        ]

    @property
    def util_display_options(self):
        util_display_options_info = []
        for util_range, color in self.util_ranges.items():
            util_display_options_info.append({'label': util_range, 'value': color})

        return util_display_options_info

    def demand_sources_and_destinations(self):
        demand_sources = set()
        demand_destinations = set()
        for entry in self.model.parallel_demand_groups().keys():
            source, dest = entry.split('-')
            demand_sources.add(source)
            demand_destinations.add(dest)
        self.demand_sources = list(demand_sources)
        self.demand_destinations = list(demand_destinations)
        self.demand_sources.sort()
        self.demand_destinations.sort()

    def lsp_sources_and_destinations(self):
        lsp_sources = set()
        lsp_destinations = set()
        for entry in self.model.parallel_lsp_groups().keys():
            source, dest = entry.split('-')
            lsp_sources.add(source)
            lsp_destinations.add(dest)
        self.lsp_sources = list(lsp_sources)
        self.lsp_destinations = list(lsp_destinations)
        self.lsp_sources.sort()
        self.lsp_destinations.sort()

    def make_node_list(self):
        node_names = [node.name for node in self.model.node_objects]
        node_names.sort()
        self.node_list = [{'label': name, 'value': name} for name in node_names]

    def visualization(self):
        # Find demand source and destinations

        # Find LSP source and destinations

        # Make node list

        pass
