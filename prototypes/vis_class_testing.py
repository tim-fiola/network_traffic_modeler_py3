import sys
sys.path.append('../')

from pyNTM import FlexModel
from pyNTM import make_visualization_beta

#
#
#
model = FlexModel.load_model_file('model_test_topology_multidigraph.csv')
model.update_simulation()

for interface in model.interface_objects:
    node_a = interface.node_object
    node_b = interface.remote_node_object
    lat_lon_a = (node_a.name, node_a.lat, node_a.lon)
    lat_lon_b = (node_b.name, node_b.lat, node_b.lon)

    print((interface, lat_lon_a, lat_lon_b))

# vis = vu.make_visualization_beta(model)
make_visualization_beta(model, font_size="20px")

# wm = Weathermap(model)
# wm.create_visualization()


