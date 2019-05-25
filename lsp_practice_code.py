from network_modeling import Model
from network_modeling import Circuit
from network_modeling import Demand
from network_modeling import graph_network
from network_modeling import Interface
from network_modeling import ModelException
from network_modeling import Node
from network_modeling import RSVP_LSP

from pprint import pprint


# Test cases:
# 1. LSP routes on path with available bandwidth
# 2. Demand shows up on LSP
# 3. Interface utilization reflects demands riding LSPs that use interface
# 4. Multiple LSPs between source and dest ECMP split traffic and update
#       their reserved bandwidth accordingly
# 5.  A non lsp demand will properly route

model = Model.load_model_file('lsp_model_test_file.csv')

# Test 1
print("model is", model)
print()
sample_lsp = model.get_rsvp_lsp('A', 'D', 'test1')
print("one of the LSPs is", sample_lsp)
model.update_simulation()
print("sample_lsp has effective metric of:")
print(sample_lsp.effective_metric(model))
print()
print("sample_lsp.path is:")
print(sample_lsp.path)
print()
print("sample_lsp has reserved_bandwidth of:")
print(sample_lsp.reserved_bandwidth)
print()
print("sample_lsp has these demands:")
print(sample_lsp.demands_on_lsp(model))
print()
print("sample_lsp actual metric is:")
print(sample_lsp.actual_metric(model))
print()

print("Here are the paths for the LSPs in the model")
for lsp in model.rsvp_lsp_objects:
    pprint((lsp.lsp_name, lsp.path))
    print()
print()


sample_demand = model.get_demand_object('A', 'D', 'test1')
print("sample_demand is ", sample_demand)
print()
print("sample_demand has path of:")
print(sample_demand.path)
print()
dmd2 = model.get_demand_object('E', 'F', 'test2')
print("dmd2 does not take an LSP; it has path of:")
pprint(dmd2.path)
print()
print("Here is the interface utilization:")
model.display_interfaces_traffic()
print()
a_to_b = model.get_interface_object('A-to-B', 'A')
a_to_c = model.get_interface_object('A-to-C', 'A')
print()
print("Here are the LSPs on {}:".format(a_to_b))
pprint(a_to_b.lsps(model))
print()
print("Here are the LSPs on {} and their reserved_bandwidth".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()
# Fail interface a_to_b; expected behavior is
# -- lsp that was on a_to_b reroute to path with interface a_to_c
# -- interface a_to_c reservable_bandwidth drops to 0
# -- interface a_to_c reserved_bandwidth goes up to 150
print("Fail interface {}".format(a_to_b))
model.fail_interface('A-to-B', 'A')
model.update_simulation()
print()
print("After failing {}, here are the LSPs on {}:".format(a_to_b, a_to_b))
pprint(a_to_b.lsps(model))
print()
print("After failing {}, here are the LSPs and their "
      "reserved_bandwidth on {}".format(a_to_b, a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()

# Add additional demand from A to D of 100; expected behavior is
# -- both LSPs from A to D take 50 traffic units each since each is signaled for 75 units
# -- both LSPs from A to D don't increase their reserved bandwidth
#    because interface a_to_c only has capacity of 150
print("Adding additional demand of 100 from A to D")
model.add_demand('A', 'D', 100, 'demand_a_to_d_3')
model.update_simulation()
print("After adding demand, here are the LSPs and their "
      "reserved_bandwidth on {}".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()
print("Here are the LSPs and their reserved_bandwidth, baseline_path_reservable_bw, "
      "and reservable_bandwidth for each interface in path:")
for lsp in model.rsvp_lsp_objects:
    print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.path])

