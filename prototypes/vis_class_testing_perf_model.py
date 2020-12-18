import sys
sys.path.append('../')

from pyNTM import PerformanceModel
from pyNTM import make_visualization_beta

#
#
#
model = PerformanceModel.load_model_file('sample_network_model_file.csv')
model.update_simulation()

lat_lon = [(node.name, node.lat, node.lon) for node in model.node_objects]
print(lat_lon)
print()
for interface in model.interface_objects:
    node_a = interface.node_object
    node_b = interface.remote_node_object
    lat_lon_a = (node_a.name, node_a.lat, node_a.lon)
    lat_lon_b = (node_b.name, node_b.lat, node_b.lon)

    print((interface, lat_lon_a, lat_lon_b))

# vis = vu.make_visualization_beta(model)
make_visualization_beta(model, font_size="20px")