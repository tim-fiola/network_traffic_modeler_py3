import dash
import dash_cytoscape as cyto
import dash_html_components as html

utilization_color = '#9400D3'

default_stylesheet = [
    {
        "selector": 'edge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "curve-style": "bezier",
            'label': "data(label)",
            'line-color': utilization_color,
            "font-size": "6px"
        }
    },
    {
        "selector": "edge[group=\"failed\"]",
        "style": {
            "line-color": "#008080",
            "curve-style": "bezier",
            'label': "data(label)",
            "font-size": "6px"
        }
    },
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "font-size": "6px"
        }
    }
]

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '800px'},
        elements=[
            {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
            {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
            {'data': {'id': 'three', 'label': 'Node 3'}, 'position': {'x': 75, 'y': 200}},
            {'data': {'source': 'one', 'target': 'two'}},
            {'data': {'source': 'two', 'target': 'one'}},
            {'data': {'source': 'one', 'target': 'three', "group": "failed", 'label': 'Ckt1'}},
            {'data': {'source': 'three', 'target': 'one', "group": "failed", 'label': 'Ckt1'}},
            {'data': {'source': 'one', 'target': 'three', "group": "", 'label': 'Ckt2'}},
            {'data': {'source': 'three', 'target': 'one', "group": "", 'label': 'Ckt2'}},
            {'data': {'source': 'one', 'target': 'three', "group": "", 'label': 'Ckt3'}},
            {'data': {'source': 'three', 'target': 'one', "group": "", 'label': 'Ckt3'}},
        ],
        stylesheet=default_stylesheet
    )
])

# TODO -
# Make different node colors - done
# Make different line colors - done
# Make node/line color groups removable from visualization
# bidirectional visualization


if __name__ == '__main__':
    app.run_server(debug=True)
