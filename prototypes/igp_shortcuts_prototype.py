import sys
sys.path.append('../')

from pprint import pprint
from pyNTM import FlexModel

from distutils import util

# Make the Parallel_Link_Model
model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path.csv')
model.update_simulation()

dmd_a_f_1 = model.get_demand_object('A', 'F', 'dmd_a_f_1')
node_a = model.get_node_object('A')

for interface in model.interface_objects:
    if interface.traffic > 0:
        print([interface, interface.traffic, interface.utilization])

for lsp in model.rsvp_lsp_objects:
    print([lsp.traffic_on_lsp(model)])



