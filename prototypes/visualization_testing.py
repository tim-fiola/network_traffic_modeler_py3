import sys
sys.path.append('../')

from pprint import pprint

from pyNTM import FlexModel

# Make the Parallel_Link_Model
model = FlexModel.load_model_file('model_test_topology_multidigraph.csv')
model.update_simulation()
print()

edge_set = set()
node_set = set()

import pdb
pdb.set_trace()


def make_json_node(x, y, id, label):

    json_node = {}
    json_node['position'] = {'x': x, 'y': y}
    json_node['data'] = {'id': id, 'label': label, 'group': ''}

    return json_node


def make_json_edge(source_id, target_id, label, utilization):
    """
    {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
              'utilization': 'failed'}}

    """

    util_ranges = {'0-24': 'royalblue',
                   '25-49': 'green',
                   '50-74': 'yellow',
                   '75-89': 'orangered',
                   '90-99': 'darkred',
                   '>100': 'darkviolet',
                   'failed': 'grey'}
    group = None

    if utilization.lower() == 'int is down':
        group == 'failed'
    else:
        for range in util_ranges.keys():
            try:
                lower = int(range.split('-')[0])
                upper = int(range.split('-')[1])

                if utilization >= lower and utilization <= upper:
                    group = util_ranges[range]
                    break
            except (ValueError, IndexError):
                pass

    json_edge = {
                    'data': {'source': source_id, 'target': target_id, "group": group,
                             'label': label, 'utilization': utilization}
                 }

    return json_edge

# util_ranges = {'0-24': 'royalblue',
#                '25-49': 'green',
#                '50-74': 'yellow',
#                '75-89': 'orangered',
#                '90-99': 'darkred',
#                '>100': 'darkviolet',
#                'failed': 'grey'}

for ckt in model.circuit_objects:
    int_a = ckt.interface_a
    int_b = ckt.interface_b
    node_a = int_a.node_object
    node_b = int_b.node_object
    node_a_y = node_a.lat
    node_a_x = node_a.lon
    node_b_y = node_b.lat
    node_b_x = node_b.lon
    ckt_id = int_a.circuit_id

    midpoint_x = sum(node_a_x, node_b_x)/2
    midpoint_y = sum(node_a_y, node_b_y)/2

    # Create the midpoint node between the endpoints
    midpoint_label = 'midpoint-{}'.format(ckt_id)
    node_set.add(make_json_node(midpoint_x, midpoint_y, midpoint_label, midpoint_label))
    # Create each end node
    node_set.add(make_json_node(node_a.lon, node_a.lat, node_a.name, node_a.name))
    node_set.add(make_json_node(node_b.lon, node_b.lat, node_b.name, node_b.name))

    # Create the edges
    # {'data': {'source': 'two', 'target': 'one', "group": util_ranges["failed"], 'label': 'Ckt4',
    #           'utilization': 'failed'}}

    # Make edges with midpoints
    edge_set.add(make_json_edge(node_a.name, midpoint_label, ckt_id, int_a.utilization))
    edge_set.add(make_json_edge(node_b.name, midpoint_label, ckt_id, int_b.utilization))


