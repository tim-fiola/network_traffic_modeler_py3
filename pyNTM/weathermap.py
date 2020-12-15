import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc

from dash.exceptions import PreventUpdate

from pyNTM import RSVP_LSP
from pyNTM import Demand

import json


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

        self.styles = {
            'all-content': {
                'width': 'auto',
                'height': 'auto'
            },
            "right_menu": {
                'width': '25vw',
                'min-width': '400px',
                'max-width': '800px',
                'height': '99%',
                'position': 'absolute',
                'top': '0',
                'right': '0',
                'zIndex': 100,
                'fontFamily': 'arial',
            },
            'cytoscape': {
                'position': 'absolute',
                'width': '74vw',
                'height': '100%',
                'backgroundColor': '#D2B48C'
            },
            'json-output': {
                'overflow-y': 'scroll',
                'fontFamily': 'menlo',
                'border': 'thin lightgrey solid',
                'line-height': '1.5'
            },
            'tabs': {},
            'tab': {'height': '75px',
                    'width': '200px',
                    'max-width': '200px',
                    'background-color': '#B695C0'
            },
            'tab-content': {
                'max-width': '400px',
                'min-width': '300px',
                'height': '100%'
            },
            'interface-tab': {'height': '75px',
                              'width': '200px',
                              'max-width': '200px',
                              'background-color': self.interface_color
            },
            'demand-tab': {'height': '75px',
                           'width': '200px',
                           'max-width': '200px',
                           'background-color': self.demand_color
            },
            'lsp-tab': {'height': '75px',
                        'width': '200px',
                        'max-width': '200px',
                        'background-color': self.lsp_color,
                        'color': 'white'
            },
        }

        self.app_layout = html.Div(style=self.styles['all-content'], children=[
            cyto.Cytoscape(
                id='cytoscape-prototypes',
                layout={'name': 'preset'},
                style=self.styles['cytoscape'],
                elements=self.elements,
                stylesheet=self.default_stylesheet,
                responsive=True
            ),
            html.Div(className='right_menu', style=self.styles['right_menu'], children=[
                html.P(children=["Selected Interface:  ",
                                 html.Button('Clear Interface Selection', id='clear-int-button', n_clicks=0),]),
                html.P(id='selected-interface-output', style=self.styles['json-output']),
                html.P(children=["Selected Demand:  ",
                                 html.Button('Clear Demand Selection', id='clear-dmd-button', n_clicks=0),]),
                html.P(id='selected-demand-output', style=self.styles['json-output']),
                html.P(children=["Selected RSVP LSP:  ",
                                 html.Button('Clear LSP Selection', id='clear-lsp-button', n_clicks=0),]),
                html.P(id='selected-lsp-output', style=self.styles['json-output']),
                dcc.Tabs(id='tabs', vertical=True, style=self.styles['tabs'], children=[
                    dcc.Tab(label='Utilization Visualization', style=self.styles['tab'], children=[
                        dcc.Dropdown(
                            style=self.styles['tab-content'],
                            id='utilization-dropdown-callback', options=self.util_display_options,
                            value=[entry['value'] for entry in self.util_display_options],
                            multi=True,
                        )
                    ]),
                    dcc.Tab(label='Find Demands', style=self.styles['demand-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            html.P("Clear the source or destination selection by selecting the 'X' on the right side of the"
                                   " selection menu"),
                            dcc.Dropdown(
                                id='demand-source-callback', placeholder='Select a source node',
                            ),
                            dcc.Dropdown(
                                id='demand-destination-callback', placeholder='Select a dest node',
                            ),
                            dcc.RadioItems(
                                id='find-demands-callback',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            ),
                        ]),
                    ]),
                    dcc.Tab(label='Demand to Interfaces', style=self.styles['demand-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id='demand-path-interfaces',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            )
                        ]),
                    ]),
                    dcc.Tab(label='Demand to LSPs', style=self.styles['demand-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id='demand-path-lsps',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            )
                        ]),
                    ]),
                    dcc.Tab(label='Find Interfaces on Node', style=self.styles['interface-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.Dropdown(
                                id='find-node', placeholder="Select a node by name",
                                options=self.node_list
                            ),
                            dcc.RadioItems(
                                id='interfaces-on-node',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            )
                        ]),
                    ]),
                    dcc.Tab(label='Interface to Demands', style=self.styles['interface-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id='interface-demand-callback',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            ),
                        ]),
                    ]),
                    dcc.Tab(label="Interface to LSPs", style=self.styles['interface-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id="interface-lsp-callback",
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output'],
                            )
                        ])
                    ]),
                    dcc.Tab(label='Find LSPs', style=self.styles['lsp-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            html.P("Clear the source or destination selection by selecting the 'X' on the right side of the"
                                   " selection menu"),
                            dcc.Dropdown(
                                id='lsp-source-callback', placeholder='Select a source node',
                            ),
                            dcc.Dropdown(
                                id='lsp-destination-callback', placeholder='Select a dest node',
                            ),
                            dcc.RadioItems(
                                id='find-lsps-callback',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            ),
                        ]),
                    ]),
                    dcc.Tab(label='LSP to Demands', style=self.styles['lsp-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id='lsp-demand-callback',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            ),
                        ]),
                    ]),
                    dcc.Tab(label='LSP to Interfaces', style=self.styles['lsp-tab'], children=[
                        html.Div(style=self.styles['tab-content'], children=[
                            dcc.RadioItems(
                                id='lsp-interface-callback',
                                labelStyle={'display': 'inline-block'},
                                style=self.styles['json-output']
                            ),
                        ]),
                    ]),
               ]),
            ])
        ])

    app = dash.Dash(__name__)
    app.run_server(debug=True)

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

    # ## Callback defs ## #
    # Def to list Node name dropdown
    @app.callback(Output('interfaces-on-node', 'options'),
                  [Input('find-node', 'value')])
    def interfaces_on_node(self, node):

        if (node):
            node = self.model.get_node_object(node)
            interfaces_on_node = node.interfaces(self.model)

            interface_info_to_display = self.format_interfaces_for_display(interfaces_on_node)

            # Add a choice at the beginning of the list to null out selection
            null_choice = {'label': self.no_selected_interface_text, 'value': ''}
            if len(interface_info_to_display) > 0 and null_choice not in interface_info_to_display:
                interface_info_to_display.insert(0, null_choice)  # Should give user option to clear selected item
            return interface_info_to_display
        else:
            raise PreventUpdate

    # Need to select interfaces that have utilization ranges selected in values from dropdown
    @app.callback(Output('cytoscape-prototypes', 'stylesheet'),
                  [Input(component_id='cytoscape-prototypes', component_property='selectedEdgeData'),
                   Input('utilization-dropdown-callback', 'value'),
                   Input('selected-demand-output', 'children'),
                   Input('selected-interface-output', 'children'),
                   Input('selected-lsp-output', 'children')])
    def update_stylesheet(self, data, edges_to_highlight, selected_demand_info, selected_interface_info, selected_lsp_info):
        """
        Updates stylesheet with style for edges_to_highlight that will change line type
        for the edge to dashed and add pink arrows and squares to the demand edges and
        also turn the nodes for the associated edges pink

        :param edges_to_highlight: list of edge elements to highlight
        :param source: demand source node name
        :param destination: demand destination node name
        :return: updated stylesheet with new elements that will reflect update colors for the
        edges_to_highlight
        """

        new_style = []

        # Utilization color for edges
        for color in edges_to_highlight:
            new_entry = {
                "selector": "edge[group=\"{}\"]".format(color),
                "style": {
                    "opacity": 1.0
                }
            }

            new_style.append(new_entry)

        # Demand source and destination path visualization
        if selected_demand_info is not None and \
                selected_demand_info != '' and \
                json.loads(selected_demand_info) != [{'source': '', 'dest': '', 'name': ''}] and \
                json.loads(selected_demand_info) != {"label": "no demand selected", "value": ""}:
            demand_dict = json.loads(selected_demand_info)
            source = demand_dict['source']
            destination = demand_dict['dest']
            # Find the demands that match the source and destination
            try:
                dmds = self.model.parallel_demand_groups()['{}-{}'.format(source, destination)]
            except KeyError:
                return self.default_stylesheet + new_style

            # Find the interfaces on the demand paths for each demand
            interfaces_to_highlight = self.find_demand_interfaces_and_lsps(dmds)[0]

            # Differentiate demand interfaces
            for interface in interfaces_to_highlight:
                # Add the edge selectors
                new_entry = {
                    "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                                interface.node_object.name),
                    "style": {
                        "width": '4',
                        'line-style': 'dashed',
                        'target-arrow-color': self.demand_color,
                        'target-arrow-shape': 'triangle',
                        'mid-target-arrow-color': self.demand_color,
                        'mid-target-arrow-shape': 'triangle',
                        'source-arrow-color': self.demand_color,
                        'source-arrow-shape': 'square',
                        'zIndex': 1000,
                    }
                }

                new_style.append(new_entry)

                new_entry_2 = {
                    "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                                interface.remote_node_object.name),
                    "style": {
                        "width": '4',
                        'line-style': 'dashed',
                        'source-arrow-color': self.demand_color,
                        'source-arrow-shape': 'triangle',
                        'mid-source-arrow-color': self.demand_color,
                        'mid-source-arrow-shape': 'triangle',
                        'target-arrow-color': self.demand_color,
                        'target-arrow-shape': 'square',
                        'zIndex': 1000,
                    }
                }

                new_style.append(new_entry_2)

                # Add the node selectors
                new_entry_3 = {
                    "selector": "node[id=\"{}\"]".format(interface.node_object.name),
                    "style": {
                        'background-color': self.demand_color
                    }
                }

                new_style.append(new_entry_3)

                new_entry_4 = {
                    "selector": "node[id=\"{}\"]".format(interface.remote_node_object.name),
                    "style": {
                        'background-color': self.demand_color
                    }
                }

                new_style.append(new_entry_4)

        # Selected edge differentiation on weathermap
        if selected_interface_info:
            if self.no_selected_interface_text not in selected_interface_info:
                selected_interface_info = json.loads(selected_interface_info)
                new_entry_5 = {
                    "selector": "edge[source=\"{}\"][circuit_id=\"{}\"]".format(selected_interface_info['source'],
                                                                                selected_interface_info['circuit_id']),
                    "style": {
                        'line-style': 'dotted',
                        'width': '6.5',
                    }
                }

                new_style.append(new_entry_5)

        # LSP path visualization
        if selected_lsp_info:
            if self.no_selected_lsp_text not in selected_lsp_info:
                selected_lsp_info = json.loads(selected_lsp_info)
                lsp_interfaces, node_names =self.get_lsp_interface_data(selected_lsp_info)

                for interface in lsp_interfaces:
                    new_entry_6 = {
                        "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                                    interface.node_object.name),
                        "style": {
                            'line-style': 'dashed',
                            'target-arrow-shape': 'chevron',
                            'arrow-scale': '1.3',
                            'target-arrow-color': self.lsp_color,
                            'z-axis': 2000
                        }
                    }

                    new_style.append(new_entry_6)

                    new_entry_7 = {
                        "selector": "edge[circuit_id=\"{}\"][source=\"{}\"]".format(interface.circuit_id,
                                                                                    interface.remote_node_object.name),
                        "style": {
                            'line-style': 'dashed',
                            'source-arrow-shape': 'chevron',
                            'arrow-scale': '1.3',
                            'source-arrow-color': self.lsp_color,
                            'z-axis': 2000
                        }
                    }

                    new_style.append(new_entry_7)

                # Nodes in LSP path have a thick brick red border
                for node in node_names:
                    new_entry_8 = {
                        "selector": "node[id=\"{}\"]".format(node),
                        "style": {
                            "border-color": self.lsp_color,
                            "border-width": "4px"
                        }
                    }

                    new_style.append(new_entry_8)

        return self.default_stylesheet + new_style


    # Adaptive source/dest dropdowns for LSPs; will alter what they show based on what
    # the other shows, so they will only show existing source/dest possibilities
    @app.callback([Output('lsp-source-callback', 'options'),
                   Output('lsp-destination-callback', 'options'),
                   Output('find-lsps-callback', 'options')],
                  [Input('lsp-source-callback', 'value'),
                   Input('lsp-destination-callback', 'value'), ])
    def display_lsp_dropdowns(self, source, dest, lsps=[{'label': '', 'value': ''}]):
        ctx = dash.callback_context

        # Get source and destination info from the dropdowns
        ctx_src_inputs = ctx.inputs['lsp-source-callback.value']
        ctx_dest_inputs = ctx.inputs['lsp-destination-callback.value']

        if ctx_src_inputs is None and ctx_dest_inputs is None:
            # No source or destination specified
            dest_options = [{'label': dest, 'value': dest} for dest in self.lsp_destinations_list]
            src_options = [{'label': source, 'value': source} for source in self.lsp_sources_list]

        elif ctx_src_inputs != None and ctx_dest_inputs != None:
            # Both source and destination specified
            src_options = [{'label': ctx_src_inputs, 'value': ctx_src_inputs}]
            dest_options = [{'label': ctx_dest_inputs, 'value': ctx_dest_inputs}]

            key = "{}-{}".format(ctx_src_inputs, ctx_dest_inputs)
            lsp_list = self.model.parallel_lsp_groups()[key]

            # Format lsps for display
            lsps = self.format_objects_for_display(lsp_list)

        elif ctx_src_inputs == None and ctx_dest_inputs != None:
            # No source but specified destination
            src_list = self.get_sources(ctx_dest_inputs, model=self.model, object_type='lsp')
            src_list.sort()

            src_options = [{'label': src, 'value': src} for src in src_list]

            dest_options = [{'label': ctx_dest_inputs, 'value': ctx_dest_inputs}]

            # Get the lsps with specified destination
            lsp_keys = self.model.parallel_lsp_groups().keys()
            src_keys = [src_key for src_key in lsp_keys if src_key.split('-')[1] == ctx_dest_inputs]
            lsp_list = []

            for src_key in src_keys:
                lsp_list += self.model.parallel_lsp_groups()[src_key]

            # Format lsps for display
            lsps = self.format_objects_for_display(lsp_list)

        elif ctx_src_inputs != None and ctx_dest_inputs == None:
            # Source specified but no destination
            src_options = [{'label': ctx_src_inputs, 'value': ctx_src_inputs}]
            dest_list = self.get_destinations(ctx_src_inputs, model=self.model, object_type='lsp')
            dest_list.sort()
            dest_options = [{'label': dest, 'value': dest} for dest in dest_list]

            # Get the lsps with specified source
            lsp_keys = self.model.parallel_lsp_groups().keys()
            dest_keys = [dest_key for dest_key in lsp_keys if dest_key.split('-')[0] == ctx_src_inputs]
            lsp_list = []

            for dest_key in dest_keys:
                lsp_list += self.model.parallel_lsp_groups()[dest_key]

            # Format lsps for display
            lsps = self.format_objects_for_display(lsp_list)
        else:
            msg = "Debug output: unaccounted for scenario in display_lsp_dropdowns"
            raise Exception(msg)

        # Add a choice at the beginning of the list to null out selection
        null_choice = {'label': self.no_selected_lsp_text, 'value': ''}
        if len(lsps) > 0 and null_choice not in lsps:
            lsps.insert(0, null_choice)  # Should give user option to clear selected item

        return src_options, dest_options, lsps

    # Adaptive source/dest dropdowns for demands; will alter what they show based on what
    # the other shows, so they will only show existing source/dest possibilities
    @app.callback([Output('demand-source-callback', 'options'),
                   Output('demand-destination-callback', 'options'),
                   Output('find-demands-callback', 'options')],
                  [Input('demand-source-callback', 'value'),
                   Input('demand-destination-callback', 'value'), ])
    def display_demand_dropdowns(self, source, dest, demands=[{'label': '', 'value': ''}]):

        ctx = dash.callback_context

        # Get source and destination info from the dropdowns
        ctx_src_inputs = ctx.inputs['demand-source-callback.value']
        ctx_dest_inputs = ctx.inputs['demand-destination-callback.value']

        if ctx_src_inputs is None and ctx_dest_inputs is None:
            # No source or destination specified
            dest_options = [{'label': dest, 'value': dest} for dest in self.demand_destinations_list]
            src_options = [{'label': source, 'value': source} for source in self.demand_sources_list]

        elif ctx_src_inputs != None and ctx_dest_inputs != None:
            # Both source and destination specified
            src_options = [{'label': ctx_src_inputs, 'value': ctx_src_inputs}]
            dest_options = [{'label': ctx_dest_inputs, 'value': ctx_dest_inputs}]

            key = "{}-{}".format(ctx_src_inputs, ctx_dest_inputs)
            demand_list = self.model.parallel_demand_groups()[key]

            # Format demands for display
            demands = self.format_objects_for_display(demand_list)

        elif ctx_src_inputs == None and ctx_dest_inputs != None:
            # No source but specified destination
            src_list = self.get_sources(ctx_dest_inputs, model=self.model, object_type='demand')
            src_list.sort()
            src_options = [{'label': src, 'value': src} for src in src_list]

            dest_options = [{'label': ctx_dest_inputs, 'value': ctx_dest_inputs}]

            # Get the demands with specified destination
            dmd_keys = self.model.parallel_demand_groups().keys()
            src_keys = [src_key for src_key in dmd_keys if src_key.split('-')[1] == ctx_dest_inputs]
            demand_list = []

            for src_key in src_keys:
                demand_list += self.model.parallel_demand_groups()[src_key]

            # Format demands for display
            demands = self.format_objects_for_display(demand_list)

        elif ctx_src_inputs != None and ctx_dest_inputs == None:
            # Source specified but no destination
            src_options = [{'label': ctx_src_inputs, 'value': ctx_src_inputs}]

            dest_list = self.get_destinations(ctx_src_inputs, model=self.model, object_type='demand')
            dest_list.sort()
            dest_options = [{'label': dest, 'value': dest} for dest in dest_list]

            # Get the demands with specified source
            dmd_keys = self.model.parallel_demand_groups().keys()
            dest_keys = [dest_key for dest_key in dmd_keys if dest_key.split('-')[0] == ctx_src_inputs]
            demand_list = []

            for dest_key in dest_keys:
                demand_list += self.model.parallel_demand_groups()[dest_key]

            # Format demands for display
            demands = self.format_objects_for_display(demand_list)

        else:
            msg = "Debug output: unaccounted for scenario in display_demand_dropdowns"
            raise Exception(msg)

        # Add a choice at the beginning of the list to null out selection
        null_choice = {'label': self.no_selected_demand_text, 'value': ''}
        if len(demands) > 0 and null_choice not in demands:
            demands.insert(0, null_choice)  # Should give user option to clear selected item

        return src_options, dest_options, demands

    # def that displays info about selected LSP
    @app.callback(Output('selected-lsp-output', 'children'),
                  [Input('demand-path-lsps', 'value'),
                   Input('find-lsps-callback', 'value'),
                   Input('interface-lsp-callback', 'value'),
                   Input('clear-lsp-button', 'n_clicks')])
    def display_selected_lsp(self, path_lsps, find_lsps, interface_lsps, clear_lsp_button):
        """

        :param path_lsps:
        :param find_lsps:
        :return:
        """
        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'clear-lsp-button.n_clicks':
            selected_lsp = json.dumps({'label': self.no_selected_lsp_text, 'value': ''})
        elif ctx.triggered[0]['value'] is None or ctx.triggered[0]['value'] == '':
            selected_lsp = json.dumps({'label': self.no_selected_lsp_text, 'value': ''})
        elif ctx.triggered[0]['value'] in [self.no_selected_demand_text, self.no_selected_interface_text]:
            selected_lsp = json.dumps({'label': self.no_selected_lsp_text, 'value': ''})
        elif ctx.triggered[0]['value'] == json.dumps([{"source": "", "dest": "", "name": ""}]):
            raise PreventUpdate
        else:
            selected_lsp = ctx.triggered[0]['value']

        return selected_lsp

    # def that displays info about the selected edge and updates selected_interface
    @app.callback(Output('selected-interface-output', 'children'),
                  [Input('cytoscape-prototypes', 'selectedEdgeData'),
                   Input('demand-path-interfaces', 'value'),
                   Input('interfaces-on-node', 'value'),
                   Input('lsp-interface-callback', 'value'),
                   Input('clear-int-button', 'n_clicks')])
    def display_selected_edge(self, data, demand_interface, node_interface, lsp_interface, clear_int_button):
        """

        :param data: list consisting of a single dict containing info about the edge/interface
        :return: json string of a dict containing metadata about the selected edge
        """

        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'clear-int-button.n_clicks' or ctx.triggered[0]['value'] == '':
            # Clear interface selection button clicked
            selected_interface = json.dumps({'label': self.no_selected_interface_text, 'value': ''})
        elif ctx.triggered[0]['prop_id'] == 'cytoscape-prototypes.selectedEdgeData' and \
                len(ctx.triggered[0]['value']) > 0:
            # If trigger is 'cytoscape-prototypes.selectedEdgeData' and
            # the selected edge is not null
            int_data = ctx.triggered[0]['value'][0]

            end_target = [item for item in int_data['target'].split('-')[1:] if item != int_data['source']][0]
            int_info = {'source': int_data['source'], 'interface-name': int_data['interface-name'],
                        'dest': end_target, 'circuit_id': int_data['circuit_id'],
                        'utilization %': int_data['utilization'], 'cost': int_data['cost']}
            # Convert dict to string for return
            selected_interface = json.dumps(int_info)
        elif ctx.triggered[0]['prop_id'] != '.':
            # No interface has been selected
            if ctx.triggered[0]['value'] == self.no_selected_demand_text:
                selected_interface = json.dumps({'label': self.no_selected_interface_text, 'value': ''})
            elif ctx.triggered[0]['value'] == []:
                raise PreventUpdate
            else:
                int_data = json.loads(ctx.triggered[0]['value'])
                if self.no_selected_demand_text not in int_data:
                    util = self.model.get_interface_object(int_data['interface-name'], int_data['source']).utilization
                    int_info = {'source': int_data['source'], 'interface-name': int_data['interface-name'],
                                'dest': int_data['dest'], 'circuit_id': int_data['circuit_id'],
                                'utilization %': util, 'cost': int_data['cost']}
                    # Convert dict to string for return
                    selected_interface = json.dumps(int_info)
        else:
            # No int selected
            selected_interface = json.dumps({'label': self.no_selected_interface_text, 'value': ''})

        return selected_interface

    # def that displays info about the selected demand and updates selected_demand
    @app.callback(Output('selected-demand-output', 'children'),
                  [Input('interface-demand-callback', 'value'),
                   Input('find-demands-callback', 'value'),
                   Input('lsp-demand-callback', 'value'),
                   Input('clear-dmd-button', 'n_clicks')])
    def display_selected_demand_data(self, model, int_demand, src_dest_demand, dmd_on_lsp, clear_int_button):

        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'clear-dmd-button.n_clicks':
            selected_demand = json.dumps({'label': self.no_selected_demand_text, 'value': ''})
        elif ctx.triggered[0]['value'] is None or ctx.triggered[0]['value'] == '':
            selected_demand = json.dumps({'label': self.no_selected_demand_text, 'value': ''})
        elif ctx.triggered[0]['value'] in [self.no_selected_lsp_text, self.no_selected_interface_text]:
            selected_demand = json.dumps({'label': self.no_selected_demand_text, 'value': ''})
        elif ctx.triggered[0]['value'] == json.dumps([{"source": "", "dest": "", "name": ""}]):
            raise PreventUpdate
        else:
            selected_demand = ctx.triggered[0]['value']

        return selected_demand

    # Def that finds and displays LSPs on the selected_interface
    @app.callback(Output('interface-lsp-callback', 'options'),
                  [Input('selected-interface-output', 'children')])
    def lsps_on_interface(self, interface_info):
        """

        :param interface_info: serialized dict info about the interface
        :return: LSPs on the interface
        """

        if interface_info and self.no_selected_interface_text not in interface_info:
            int_dict = json.loads(interface_info)
            interface = self.model.get_interface_object(int_dict['interface-name'], int_dict['source'])
            lsps = interface.lsps(self.model)
            if len(lsps) == 0:
                return [
                    {'label': 'no lsps on interface', 'value': json.dumps([{'source': '', 'dest': '', 'name': ''}])}]

            lsps_on_interface = self.format_objects_for_display(lsps)

            # Add a choice at the beginning of the list to null out selection
            null_choice = {'label': self.no_selected_lsp_text, 'value': ''}
            if len(lsps_on_interface) > 0 and null_choice not in lsps_on_interface:
                lsps_on_interface.insert(0, null_choice)  # Should give user option to clear selected item

            return lsps_on_interface

        else:
            return [{"label": self.no_selected_interface_text, "value": ''}]

    # def that finds and displays demands on the selected interface
    @app.callback(Output('interface-demand-callback', 'options'),
                  [Input('selected-interface-output', 'children')])
    def demands_on_interface(self, interface_info):
        """


        :param interface_info: serialized dict info about the interface
        :return: Demands on the interface
        """

        if interface_info and self.no_selected_interface_text not in interface_info:
            int_dict = json.loads(interface_info)
            interface = self.model.get_interface_object(int_dict['interface-name'], int_dict['source'])
            demands = interface.demands(self.model)
            if len(demands) == 0:
                return [
                    {'label': 'no demands on interface', 'value': json.dumps([{'source': '', 'dest': '', 'name': ''}])}]

            demands_on_interface = self.format_objects_for_display(demands)

            # Add a choice at the beginning of the list to null out selection
            null_choice = {'label': self.no_selected_demand_text, 'value': ''}
            if len(demands_on_interface) > 0 and null_choice not in demands_on_interface:
                demands_on_interface.insert(0, null_choice)  # Should give user option to clear selected item

            return demands_on_interface
        else:
            return [{"label": self.no_selected_interface_text, "value": ''}]

    # def that finds and displays demands on the selected interface
    @app.callback(Output('lsp-demand-callback', 'options'),
                  [Input('selected-lsp-output', 'children')])
    def demands_on_lsp(self, lsp_info):
        """


        :param interface_info: serialized dict info about the interface
        :return: Demands on the interface
        """

        if lsp_info and self.no_selected_lsp_text not in lsp_info:
            lsp_dict = json.loads(lsp_info)
            lsp = self.model.get_rsvp_lsp(lsp_dict['source'], lsp_dict['dest'], lsp_dict['name'])
            demands = lsp.demands_on_lsp(self.model)
            if len(demands) == 0:
                return [{'label': 'no demands on lsp', 'value': json.dumps([{'source': '', 'dest': '', 'name': ''}])}]

            demands_on_lsp = self.format_objects_for_display(demands)

            # Add a choice at the beginning of the list to null out selection
            null_choice = {'label': self.no_selected_demand_text, 'value': ''}
            if len(demands_on_lsp) > 0 and null_choice not in demands_on_lsp:
                demands_on_lsp.insert(0, null_choice)  # Should give user option to clear selected item

            return demands_on_lsp
        else:
            return [{"label": self.no_selected_lsp_text, "value": ''}]

    # def that finds and displays interfaces and LSPs on selected_demand's path;
    # this def updates both the 'Demand to Interfaces' and 'Demand to LSPs' tabs
    @app.callback([Output('demand-path-interfaces', 'options'),
                   Output('demand-path-lsps', 'options')],
                  [Input('selected-demand-output', 'children')])
    def demand_interfaces(self, demand):

        if demand:
            if self.no_selected_demand_text not in demand:
                demand = json.loads(demand)
                dmd = self.model.get_demand_object(demand['source'], demand['dest'], demand['name'])
                dmd_ints, dmd_lsps = self.find_demand_interfaces_and_lsps([dmd])

                interfaces_list = self.format_interfaces_for_display(dmd_ints)

                # Add a choice at the beginning of the list to null out selection for interfaces
                null_choice = {'label': self.no_selected_interface_text, 'value': ''}
                if len(interfaces_list) > 0 and null_choice not in interfaces_list:
                    interfaces_list.insert(0, null_choice)  # Should give user option to clear selected item

                if not dmd_lsps:
                    lsp_list = [{'label': 'Demand does not take LSPs', 'value': ''}]
                else:
                    lsp_list = self.format_objects_for_display(list(dmd_lsps))

                    # Add a choice at the beginning of the list to null out selection for lsps
                    null_choice = {'label': self.no_selected_lsp_text, 'value': ''}
                    if len(lsp_list) > 0 and null_choice not in lsp_list:
                        lsp_list.insert(0, null_choice)  # Should give user option to clear selected item
                return interfaces_list, lsp_list

            else:
                selected_demand = self.no_selected_demand_text
                return ([{'label': selected_demand, 'value': selected_demand}],
                        [{'label': selected_demand, 'value': selected_demand}])
        else:
            selected_demand = self.no_selected_demand_text
            return ([{'label': selected_demand, 'value': selected_demand}],
                    [{'label': selected_demand, 'value': selected_demand}])

    # def that finds and displays interfaces on selected_lsp's path
    @app.callback(Output('lsp-interface-callback', 'options'),
                  [Input('selected-lsp-output', 'children')])
    def lsp_interfaces(self, lsp):
        if lsp:
            if self.no_selected_lsp_text not in lsp:
                lsp = json.loads(lsp)
                lsp = self.model.get_rsvp_lsp(lsp['source'], lsp['dest'], lsp['name'])
                lsp_interfaces = lsp.path['interfaces']

                interfaces_list = self.format_interfaces_for_display(lsp_interfaces)

                # Add a choice at the beginning of the list to null out selection
                null_choice = {'label': self.no_selected_interface_text, 'value': ''}
                if len(interfaces_list) > 0 and null_choice not in interfaces_list:
                    interfaces_list.insert(0, null_choice)  # Should give user option to clear selected item

                return interfaces_list
            else:
                return [{'label': self.no_selected_lsp_text, 'value': self.no_selected_lsp_text}]
        else:
            return [{'label': self.no_selected_lsp_text, 'value': self.no_selected_lsp_text}]



    # ## Utility Functions ## #
    def format_objects_for_display(self, object_list):
        """
        Takes a list of LSP or demand objects and returns a list of info that can
        be displayed in visualization menus.

        :param object_list: list of Demand objects
        :return: List of info about each demand.  Each list entry is a dict with 'label' and
        'value' keys

        Example Input::
            [Demand(source = F, dest = B, traffic = 50, name = 'dmd_f_b_1'),
            Demand(source = A, dest = B, traffic = 50, name = 'dmd_a_b_1')]

        Example Output::
            [{'label': "Demand(source = F, dest = B, traffic = 50, name = 'dmd_f_b_1')",
            'value': '{"source": "F", "dest": "B", "name": "dmd_f_b_1"}'},
            {'label': "Demand(source = A, dest = B, traffic = 50, name = 'dmd_a_b_1')",
            'value': '{"source": "A", "dest": "B", "name": "dmd_a_b_1"}'}]

        """

        if isinstance(object_list[0], RSVP_LSP):
            object_type = 'lsp'
        elif isinstance(object_list[0], Demand):
            object_type = 'demand'

        # Initialize object list
        objects = []
        for object in object_list:
            # Return the demand's value as a dict with demand info (dmd_info)
            src = object.source_node_object.name
            dest = object.dest_node_object.name
            if object_type == 'demand':
                name = object.name
            elif object_type == 'lsp':
                name = object.lsp_name
            object_info = {'source': src, 'dest': dest, 'name': name}
            objects.append({"label": object.__repr__(), "value": json.dumps(object_info)})
        return objects

    def format_interfaces_for_display(self, interface_list):
        """
        Reformats information about Interface objects for display

        :param interface_list: list of Interface objects
        :return: list of dict entries with interface information
        """
        interfaces_list = []
        for interface in interface_list:
            source_node_name = interface.node_object.name
            dest_node_name = interface.remote_node_object.name
            name = interface.name
            circuit_id = interface.circuit_id
            cost = interface.cost
            int_dict = {'source': source_node_name, 'interface-name': name,
                        'dest': dest_node_name, 'circuit_id': circuit_id, 'cost': cost}
            int_info = {'label': interface.__repr__(), 'value': json.dumps(int_dict)}
            interfaces_list.append(int_info)
        return interfaces_list


    def find_demand_interfaces_and_lsps(self, dmds):
        """
        Finds interfaces for each demand in dmds.  If there
        are RSVP LSPs in path, the interfaces for that LSP path
        are added to the set of output interfaces

        :param dmds: iterable of demand objects
        :return: set of interfaces that any given demand in dmds transits
        """
        interfaces_to_highlight = set()
        lsps = set()
        for dmd in dmds:
            dmd_path = dmd.path[:]
            for path in dmd_path:
                for hop in path:
                    if isinstance(hop, RSVP_LSP):
                        lsps.add(hop)
                        for lsp_hop in hop.path['interfaces']:
                            interfaces_to_highlight.add(lsp_hop)
                    else:
                        interfaces_to_highlight.add(hop)
        return interfaces_to_highlight, lsps

    def get_sources(self, destination, model, object_type):
        """
        Returns a list of sources in the model that have
        LSPs or Demands that terminate on the specified destination node.

        :param destination: destination for LSPs or demands
        :param model: pyNTM Model object
        :param object_type: Either 'demand' or 'lsp'

        :return: List of sources in the model that have LSPs or demands that are sourced from
        the sources and terminate on the specified destination.
        """

        if object_type not in ['demand', 'lsp']:
            msg = "'object_type' value must be 'demand'|'lsp'"
            raise Exception(msg)

        if object_type == 'demand':
            source_dest_pairs = [pair.split('-') for pair in model.parallel_demand_groups().keys()]
        elif object_type == 'lsp':
            source_dest_pairs = [pair.split('-') for pair in model.parallel_lsp_groups().keys()]

        sources = [pair[0] for pair in source_dest_pairs if pair[1] == destination]

        return sources

    def get_destinations(self, src, model, object_type):
        """
        Returns a list of destinations in the model that have
        LSPs or Demands that originate on the specified source.

        :param source: origin for LSPs or demands
        :param model: pyNTM Model object
        :param type: Either 'demand' or 'lsp'

        :return: List of destinations in the model that have LSPs or demands that terminate on
        the destinations and originate on the specified origin node.
        """

        if object_type not in ['demand', 'lsp']:
            msg = "'object_type' value must be 'demand'|'lsp'"
            raise Exception(msg)

        if object_type == 'demand':
            source_dest_pairs = [pair.split('-') for pair in model.parallel_demand_groups().keys()]
        elif object_type == 'lsp':
            source_dest_pairs = [pair.split('-') for pair in model.parallel_lsp_groups().keys()]

        destinations = [pair[1] for pair in source_dest_pairs if pair[0] == src]

        return destinations

    def get_lsp_interface_data(self, lsp_data):
        """
        Gets circuit_id and node info for each lsp in lsp_data

        :param lsp_data:
        :return: tuple of [list of circuit ids], set(node names)
        """

        lsp = self.model.get_rsvp_lsp(lsp_data['source'], lsp_data['dest'], lsp_data['name'])
        lsp_interfaces = lsp.path['interfaces']
        nodes = set()
        for interface in lsp_interfaces:
            nodes.add(interface.node_object.name)
            nodes.add(interface.remote_node_object.name)
        return lsp_interfaces, nodes