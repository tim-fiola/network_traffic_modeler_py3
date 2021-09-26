import sys

sys.path.append("../")

from pprint import pprint
from pyNTM import FlexModel

# Make the Parallel_Link_Model
model = FlexModel.load_model_file("igp_shortcuts_model_mult_lsps_in_path.csv")
model.update_simulation()

dmd_a_f_1 = model.get_demand_object("A", "F", "dmd_a_f_1")
dmd_d_f_1 = model.get_demand_object("D", "F", "dmd_d_f_1")
node_a = model.get_node_object("A")

lsp_b_d_1 = model.get_rsvp_lsp("B", "D", "lsp_b_d_1")
lsp_b_d_2 = model.get_rsvp_lsp("B", "D", "lsp_b_d_2")

print("Interfaces with traffic")
for interface in model.interface_objects:
    if interface.traffic > 0:
        print([interface, interface.traffic, interface.utilization])
print()
# for dmd in model.demand_objects:
#     pprint([dmd, dmd.path_detail])

print("LSPs and their traffic")
for lsp in model.rsvp_lsp_objects:
    print([lsp, lsp.traffic_on_lsp(model)])
print()
lsp_d_f = model.get_rsvp_lsp("D", "F", "lsp_d_f_1")

print("demands on lsp_d_f:")
pprint(lsp_d_f.demands_on_lsp(model))

# print()
# print("Remove igp shortcuts from Node B:")
#
# node_b = model.get_node_object('B')
# node_b.igp_shortcuts_enabled = False
# model.update_simulation()
#
# lsp_c_e = model.get_rsvp_lsp('C', 'E', 'lsp_c_e_1')
# print("Traffic on lsp_c_e = {}".format(lsp_c_e.traffic_on_lsp(model)))
