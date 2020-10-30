import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc

util_ranges = {'0-24': 'royalblue',
               '25-49': 'green',
               '50-74': 'yellow',
               '75-89': 'orangered',
               '90-99': 'darkred',
               '>100': 'darkviolet',
               'failed': 'grey'}

default_stylesheet = [
    {
        "selector": 'edge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "curve-style": "bezier",
            'label': "data(label)",
            'line-color': "data(group)",
            "font-size": "6px",
            "opacity": 0.4
        }
    },
    {
        "selector": "edge[group=\"failed\"]",
        "style": {
            "line-color": "#808080",
            "curve-style": "bezier",
            'label': "data(label)",
            "font-size": "6px",
            'line-style': 'dashed'
        }
    },
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "font-size": "6px",
            "text-halign": 'center',
            'text-valign': 'center',
            'text-wrap': 'wrap',
            "size": 3
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
]

app = dash.Dash(__name__)

elements = [
    {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
    {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
    {'data': {'id': 'three', 'label': 'Node 3', 'group': "failed"}, 'position': {'x': 75, 'y': 200}},
    {'data': {'source': 'one', 'target': 'two', "group": util_ranges["failed"], 'label': 'Ckt4',
              'utilization': 'failed'}},
    {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
              'utilization': 'failed'}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["failed"], 'label': 'Ckt1',
              'utilization': 'failed'}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt1',
              'utilization': 'failed'}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["25-49"], 'label': 'Ckt2',
              'utilization': 40}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["75-89"], 'label': 'Ckt2',
              'utilization': 78}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges[">100"], 'label': 'Ckt3',
              'utilization': 110}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["0-24"], 'label': 'Ckt3',
              'utilization': 15}},
]

util_display_options = []
for util_range, color in util_ranges.items():
    util_display_options.append({'label': util_range, 'value': color})

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-prototypes',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '800px'},
        elements=elements,
        stylesheet=default_stylesheet,
    ),
    html.P(id='cytoscape-mouseoverEdgeData-output'),
    html.Label('Multi-Select Dropdown'),
    dcc.Dropdown(id='utilization-dropdown-callback', options=util_display_options,
                 value=[entry['value'] for entry in util_display_options],
                 multi=True)
])


# Need to select interfaces that have utilization ranges selected in values from dropdown

@app.callback(Output('cytoscape-mouseoverEdgeData-output', 'children'),
              [Input('cytoscape-prototypes', 'mouseoverEdgeData')])
def displayTapEdgeData(data):
    if data:
        msg = "Source: {}, Dest: {}, utilization {}%".format(data['source'], data['target'], data['utilization'])
        return msg


@app.callback(Output('cytoscape-prototypes', 'stylesheet'), [Input('utilization-dropdown-callback', 'value')])
def update_stylesheet(edges_to_highlight):
    new_style = []
    for color in edges_to_highlight:
        new_entry = {
            "selector": "edge[group=\"{}\"]".format(color),
            "style": {
                "opacity": 1.0
            }
        }

        new_style.append(new_entry)

    return default_stylesheet + new_style


if __name__ == '__main__':
    app.run_server(debug=True)
