from datetime import datetime
import sys
sys.path.append('../')
sys.path.append('../pyNTM')

from pprint import pprint

# from pyNTM import Parallel_Link_Model
from pyNTM.parallel_link_model import Parallel_Link_Model

time_before_load = datetime.now()

model = Parallel_Link_Model.load_model_file('big_model_multi_digraph_file.txt')

time_after_load = datetime.now()

model.update_simulation()

time_after_update_sim = datetime.now()

time_to_load = time_after_load - time_before_load
time_to_update_sim = time_after_update_sim - time_after_load

print("time_to_load = {}".format(time_to_load))
print("time_to_update_sim = {}".format(time_to_update_sim))

lsps_routed_no_demands = [lsp for lsp in model.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                          lsp.demands_on_lsp(model) == []]

lsps_routed_with_demands = [lsp for lsp in model.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                          lsp.demands_on_lsp(model) != []]

print("There are {} LSPs that are routed but have no demands".format(len(lsps_routed_no_demands)))
print("There are {} LSPs that are routed and carry demands".format(len(lsps_routed_with_demands)))

# Find the source/dest nodes for each LSP
lsp_source_dest_pairs = set([(lsp.source_node_object.name,
                              lsp.dest_node_object.name) for lsp in model.rsvp_lsp_objects])

# Find the source/dest nodes for each demand
dmd_source_dest_pairs = set([(dmd.source_node_object.name,
                              dmd.dest_node_object.name) for dmd in model.demand_objects])


dmds_paired_with_lsps = []
for dmd_info in dmd_source_dest_pairs:
    for lsp_info in lsp_source_dest_pairs:
            if dmd_info == lsp_info:
                    dmds_paired_with_lsps.append(dmd_info)

dmds_paired_with_lsps = set(dmds_paired_with_lsps)

print("{} of the demands ride LSPs".format(len(dmds_paired_with_lsps)))

unrouted_lsps = [lsp for lsp in model.rsvp_lsp_objects if lsp.path == 'Unrouted']

print("There are {} unrouted LSPs".format(len(unrouted_lsps)))

print("There are {} unrouted demands".format(len(model.get_unrouted_demand_objects())))