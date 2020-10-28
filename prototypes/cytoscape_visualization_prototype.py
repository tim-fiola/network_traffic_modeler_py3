import dash
import dash_cytoscape as cyto
import dash_html_components as html
from dash.dependencies import Input, Output

# TODO - make interactive legend - https://dash.plotly.com/layout

util_ranges = {'0-24': '#002366',
               '25-49': '#008000',
               '50-74': '#FFFF00',
               '75-89': '#FF4500',
               '90-99': '#8B0000',
               '100-': '#9400D3'}

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
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["25-49"], 'label': 'Ckt2'}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["75-89"], 'label': 'Ckt2'}},
    {'data': {'source': 'one', 'target': 'three', "group": util_ranges["100-"], 'label': 'Ckt3'}},
    {'data': {'source': 'three', 'target': 'one', "group": util_ranges["0-24"], 'label': 'Ckt3'}},
]

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '800px'},
        elements=elements,
        stylesheet=default_stylesheet,
    ),
    html.P(id='cytoscape-mouseoverEdgeData-output')
])


@app.callback(Output('cytoscape-mouseoverEdgeData-output', 'children'),
              [Input('cytoscape-two-nodes', 'mouseoverEdgeData')])
def displayTapEdgeData(data):
    if data:
        return "You recently hovered over the edge between " + data['source'].upper() + " and " + data['target'].upper()


if __name__ == '__main__':
    app.run_server(debug=True)
