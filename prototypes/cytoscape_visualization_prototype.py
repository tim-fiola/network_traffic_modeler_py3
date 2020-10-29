import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc

# TODO - need to make callback to show only items selected in dropdown
# https://dash.plotly.com/layout Core Components section

util_ranges = {'0-24': 'royalblue',
               '25-49': 'green',
               '50-74': 'yellow',
               '75-89': 'orangered',
               '90-99': 'darkred',
               '100-': 'darkviolet'}

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
    {
        "selector": 'edge[group=\"util_ranges\", group not in \"util_display_options\"]',
        "style": {
            "opacity": 0.4
        }
    }
]

app = dash.Dash(__name__)

elements = [
    {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
    {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
    {'data': {'id': 'three', 'label': 'Node 3', 'group': "failed"}, 'position': {'x': 75, 'y': 200}},
    {'data': {'source': 'one', 'target': 'two', "group": "failed", 'label': 'Ckt4',
              'utilization': 'failed'}},
    {'data': {'source': 'two', 'target': 'one', "group": "failed", 'label': 'Ckt4',
              'utilization': 'failed'}},
    {'data': {'source': 'one', 'target': 'three', "group": "failed", 'label': 'Ckt1',
              'utilization': 'failed'}},
    {'data': {'source': 'three', 'target': 'one', "group": "failed", 'label': 'Ckt1',
              'utilization': 'failed'}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["25-49"], 'label': 'Ckt2',
              'utilization': 40}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["75-89"], 'label': 'Ckt2',
              'utilization': 78}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["100-"], 'label': 'Ckt3',
              'utilization': 110}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["0-24"], 'label': 'Ckt3',
              'utilization': 15}},
]

util_display_options = []
for item in util_ranges.keys():
    util_display_options.append({'label': item, 'value': item})

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '800px'},
        elements=elements,
        stylesheet=default_stylesheet,
    ),
    html.P(id='cytoscape-mouseoverEdgeData-output'),
    html.Label('Multi-Select Dropdown'),
    dcc.Dropdown(options=util_display_options,
                 value=[entry['value'] for entry in util_display_options],
                 multi=True)
])


# Need to select interfaces that have utilization ranges selected in values from dropdown

@app.callback(Output('cytoscape-mouseoverEdgeData-output', 'children'),
              [Input('cytoscape-two-nodes', 'mouseoverEdgeData')])
def displayTapEdgeData(data):
    if data:
        msg = "Source: {}, Dest: {}, utilization {}%".format(data['source'], data['target'], data['utilization'])
        return msg


if __name__ == '__main__':
    app.run_server(debug=True)
