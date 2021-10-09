import sys

sys.path.append("../")

from pyNTM import FlexModel

model = FlexModel.load_model_file("flex_model_parallel_source_dest_lsps.csv")

lsp_b_d_1 = model.get_rsvp_lsp("B", "D", "lsp_b_d_1")  # lower metric
lsp_b_d_3 = model.get_rsvp_lsp("B", "D", "lsp_b_d_3")  # lower metric
lsp_b_d_2 = model.get_rsvp_lsp("B", "D", "lsp_b_d_2")  # default metric (higher)

dmd_a_d_1 = model.get_demand_object("A", "D", "dmd_a_d_1")
dmd_b_d_1 = model.get_demand_object("B", "D", "dmd_b_d_1")

print("traffic on lsp_b_d_1 = {}".format(lsp_b_d_1.traffic_on_lsp(model)))
print("traffic on lsp_b_d_2 = {}".format(lsp_b_d_2.traffic_on_lsp(model)))
print("traffic on lsp_b_d_3 = {}".format(lsp_b_d_3.traffic_on_lsp(model)))
