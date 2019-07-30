# This is a temp hack to get this to see pyNTM and let it import
import sys  # noqa
sys.path.append('../')  # noqa

from pyNTM import Model
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
print("model demands are:")
pprint(model.demand_objects)
print()
lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
int_b_g = model.get_interface_object('B-to-G', 'B')
int_a_c = model.get_interface_object('A-to-C', 'A')
int_a_b = model.get_interface_object('A-to-B', 'A')
print("model LSPs are:")
pprint(model.rsvp_lsp_objects)
print()
model.update_simulation()
print("Here are the LSPs are their effective and actual metrics")
for lsp in model.rsvp_lsp_objects:
    print(lsp, lsp.effective_metric(model), lsp.actual_metric(model))

# Check/validate metrics for LSPs
if lsp_a_d_1.effective_metric(model) != 40:
    msg = "lsp_a_d_1 effective_metric should be 40"
    raise Exception(msg)
if lsp_a_d_2.effective_metric(model) != 40:
    msg = "lsp_a_d_2 effective_metric should be 40"
    raise Exception(msg)
if lsp_a_d_1.actual_metric == lsp_a_d_2.actual_metric:
    msg = "lsp_a_d_1 and lsp_a_d_2 should have different actual_metrics"
    raise Exception(msg)

print()
print("Here are the paths for the LSPs in the model")
for lsp in model.rsvp_lsp_objects:
    pprint((lsp.lsp_name, lsp.path))
    print()
print()
print("Here are the LSP reserved_bandwidth values:")
for lsp in model.rsvp_lsp_objects:
    print(lsp, lsp.reserved_bandwidth)
# Validate 75 reserved bandwidth on the A-D LSPs
if lsp_a_d_1.reserved_bandwidth != lsp_a_d_2.reserved_bandwidth != 75:
    msg = "lsp_a_d_1 and test2_lsp should have reserved_bandwidth of 75"
    raise Exception(msg)
# lsp_f_e_1 lsp should be unrouted
if 'Unrouted' not in model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1').path:
    msg = "{} should be Unrouted".format(model.get_rsvp_lsp('F', 'E', 'lsp_f_e_1'))
    raise Exception(msg)

print()
print("Here are the LSPs and their demands:")
for lsp in model.rsvp_lsp_objects:
    print(lsp)
    for demand in lsp.demands_on_lsp(model):
        print(demand)
    print()
print()

int_c_d = model.get_interface_object('C-to-D', 'C')

dmd_a_d_1 = model.get_demand_object('A', 'D', 'dmd_a_d_1')

print("Here are the demands and their paths:")
for demand in model.demand_objects:
    print(demand)
    pprint(demand.path)
    print()
# dmd2 = model.get_demand_object('E', 'F', 'test2')
print()
print("Here is the interface utilization:")
model.display_interfaces_traffic()
# Validate utilization
traffic_values = [interface.traffic for interface in model.interface_objects]
expected_traffic = [40.0, 266.6666666666667, 0.0, 20.0, 133.33333333333334,
                    400.0, 133.33333333333334, 0.0, 75.0, 85.0, 95.0, 0.0,
                    400.0, 75.0, 10.0, 133.33333333333334, 133.33333333333334, 10.0]
if traffic_values.sort() != expected_traffic.sort():
    msg = "error in traffic engine"
    raise Exception(msg)
print()
a_to_b = model.get_interface_object('A-to-B', 'A')
a_to_c = model.get_interface_object('A-to-C', 'A')
print()
print("Here are the LSPs on {}:".format(a_to_b))
pprint(a_to_b.lsps(model))
print()
print("Here are the LSPs on {}".format(a_to_c))
pprint(a_to_c.lsps(model))
print()

print("Here are the LSPs on {} and their reserved_bandwidth".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()

print("Here are the LSPs on {} and their reserved_bandwidth".format(a_to_b))
for lsp in a_to_b.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_b, a_to_b.reserved_bandwidth))
print()
print()
print()

# Fail interface a_to_b; expected behavior is
# -- lsp that was on a_to_b reroute to path with interface a_to_c
# -- interface a_to_c reservable_bandwidth drops to 0
# -- interface a_to_c reserved_bandwidth goes up to 150
print("*************** Fail interface {} ***************".format(a_to_b))
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
print("******** Adding additional demand of 100 from A to D *********")
model.add_demand('A', 'D', 100, 'dmd_a_to_d_3')
model.update_simulation()
print("After adding demand, here are the LSPs and their "
      "reserved_bandwidths and setup_bandwidths on {}".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()
print("Here are the routed LSPs and their reserved_bandwidth and baseline_path_reservable_bw values ")
for lsp in model.rsvp_lsp_objects:
    if 'Unrouted' not in lsp.path:
        print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.path['baseline_path_reservable_bw']])
print()
print("Here are the unrouted LSPs")
for lsp in model.rsvp_lsp_objects:
    if 'Unrouted' in lsp.path:
        print([lsp.lsp_name, lsp.setup_bandwidth])
print()


# Unfail interface a_to_b; expected_behavior is
# -- one of the LSPs on a_to_c should move to a_to_b since a_to_c is oversubscribed
#   and each one of the two LSPs on a_to_c has a setup bandwidth of 125 (250/150)
print("******* Unfailing a_to_b *******")
model.unfail_interface('A-to-B', 'A')
model.update_simulation()

print("Here are the LSPs on {} and their reserved and setup bandwidths:".format(a_to_b))
for lsp in a_to_b.lsps(model):
    print(lsp, lsp.reserved_bandwidth, lsp.setup_bandwidth)
print()

print("Here are the LSPs on {} and their reserved and setup bandwidths:".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print(lsp, lsp.reserved_bandwidth, lsp.setup_bandwidth)
print()

print("*************** Adding 3rd LSP from A to D ****************")
model.add_rsvp_lsp('A', 'D', 'lsp_a_d_3')
lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')
model.update_simulation()

print("Here are the routed LSPs and their reserved_bandwidth, setup_bandwidth, and baseline_path_reservable_bw values ")
for lsp in model.rsvp_lsp_objects:
    if 'Unrouted' not in lsp.path:
        print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth, lsp.path['baseline_path_reservable_bw']])
print()
print("Traffic on interface {} is {}".format(a_to_c, a_to_c.traffic))
print("Demands on interface {} are:".format(a_to_c))
pprint(a_to_c.demands(model))
print()
print("Traffic on interface {} is {}".format(a_to_b, a_to_b.traffic))
print("Demands on interface {} are:".format(a_to_b))
pprint(a_to_b.demands(model))
print()

demand_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')
# demand_e_f = model.get_demand_object('E', 'F', 'test2')
print("Path for {} is:".format(demand_a_f))
pprint(demand_a_f.path)
print()
# print("Path for {} is:".format(demand_e_f))
# pprint(demand_e_f.path)


print("Here are demands on {}".format(int_b_g))
for demand in int_b_g.demands(model):
    print(demand)

demand_f_e = model.get_demand_object('F', 'E', 'dmd_f_e_1')

print("*************** Adding 4th LSP from A to D ****************")
model.add_rsvp_lsp('A', 'D', 'lsp_a_d_4')
lsp_a_d_4 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_4')
model.update_simulation()
print("Here are the routed LSPs and their reserved_bandwidth, setup_bandwidth, and baseline_path_reservable_bw values")
for lsp in model.rsvp_lsp_objects:
    if 'Unrouted' not in lsp.path:
        print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth, lsp.path['baseline_path_reservable_bw']])
print()
print("*************** Adding LSP from A to F ******************")
model.add_rsvp_lsp('A', 'F', 'lsp_a_f')
lsp_a_f_1 = model.get_rsvp_lsp('A', 'F', 'lsp_a_f')
model.update_simulation()
print("Here are all the LSPs and their reserved_bandwidth, setup_bandwidth, and baseline_path_reservable_bw values")
for lsp in model.rsvp_lsp_objects:
    print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth])