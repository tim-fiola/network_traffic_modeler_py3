from pprint import pprint

from pyNTM import Model

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
test1_lsp = model.get_rsvp_lsp('A', 'D', 'test1')
test2_lsp = model.get_rsvp_lsp('A', 'D', 'test2')
b_to_g = model.get_interface_object('B-to-G', 'B')

print("model LSPs are:")
pprint(model.rsvp_lsp_objects)
print()
model.update_simulation()
print("Here are the LSPs are their effective and actual metrics")
for lsp in model.rsvp_lsp_objects:
    print(lsp, lsp.effective_metric(model), lsp.actual_metric(model))

# Check/validate metrics for LSPs
if test1_lsp.effective_metric(model) != 40:
    msg = "test1_lsp effective_metric should be 40"
    raise Exception(msg)
if test2_lsp.effective_metric(model) != 40:
    msg = "test2_lsp effective_metric should be 40"
    raise Exception(msg)
if test1_lsp.actual_metric == test2_lsp.actual_metric:
    msg = "test1_lsp and test2_lsp should have different actual_metrics"
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
if test1_lsp.reserved_bandwidth != test2_lsp.reserved_bandwidth != 75:
    msg = "test1_lsp and test2_lsp should have reserved_bandwidth of 75"
    raise Exception(msg)
# test3 lsp should be unrouted
if model.get_rsvp_lsp('F', 'E', 'test3').path != 'Unrouted':
    msg = "{} should be Unrouted".format(model.get_rsvp_lsp('F', 'E', 'test3'))
    raise Exception(msg)

print()
print("Here are the LSPs and their demands:")
for lsp in model.rsvp_lsp_objects:
    print(lsp)
    for demand in lsp.demands_on_lsp(model):
        print(demand)
    print()
print()

c_to_d = model.get_interface_object('C-to-D', 'C')

sample_demand = model.get_demand_object('A', 'D', 'test1')

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
model.add_demand('A', 'D', 100, 'demand_a_to_d_3')
model.update_simulation()
print("After adding demand, here are the LSPs and their "
      "reserved_bandwidths and setup_bandwidths on {}".format(a_to_c))
for lsp in a_to_c.lsps(model):
    print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth])
print("{} reserved_bandwidth is {}".format(a_to_c, a_to_c.reserved_bandwidth))
print()
print("Here are the routed LSPs and their reserved_bandwidth and baseline_path_reservable_bw values ")
for lsp in model.rsvp_lsp_objects:
    if lsp.path != 'Unrouted':
        print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.path['baseline_path_reservable_bw']])
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
model.add_rsvp_lsp('A', 'D', 'test3')
model.update_simulation()
print("Here are the routed LSPs and their reserved_bandwidth, setup_bandwidth, and baseline_path_reservable_bw values ")
for lsp in model.rsvp_lsp_objects:
    if lsp.path != 'Unrouted':
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
demand_a_f = model.get_demand_object('A', 'F', 'test5')
# demand_e_f = model.get_demand_object('E', 'F', 'test2')
print("Path for {} is:".format(demand_a_f))
pprint(demand_a_f.path)
print()
# print("Path for {} is:".format(demand_e_f))
# pprint(demand_e_f.path)

# TODO - b_to_g has traffic that should be on LSPs (A to D demands)
print("Here are demands on {}".format(b_to_g))
for demand in b_to_g.demands(model):
    print(demand)

demand_f_e = model.get_demand_object('F', 'E', 'test4')

# print("*************** Adding 4th LSP from A to D ****************")
# model.add_rsvp_lsp('A', 'D', 'test4')
# model.update_simulation()
# print("Here are the routed LSPs and their reserved_bandwidth, setup_bandwidth, and baseline_path_reservable_bw
# values ")
# for lsp in model.rsvp_lsp_objects:
#     if lsp.path != 'Unrouted':
#         print([lsp.lsp_name, lsp.reserved_bandwidth, lsp.setup_bandwidth, lsp.path['baseline_path_reservable_bw']])
# print()
