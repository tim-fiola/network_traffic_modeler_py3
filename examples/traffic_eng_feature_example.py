import sys
sys.path.append('../')


# Test cases
# - LSPs won't transit over non-rsvp_enabled interface on both models
# - percent_reserved_bandwidth limits amount of reservable_bandwidth on Interface
#       - test return self._reservable_bandwidth on Interface
# - try manually setting reservable_bandwidth on an interface

# TODO - make model file that has 3 identical circuit_id values - should error out
# TODO - test parallel links but one w higher metric

from pprint import pprint

from pyNTM import PerformanceModel

model = PerformanceModel.load_model_file('traffic_eng_example_model.csv')
model.update_simulation()

int_a_b = model.get_interface_object('A-to-B', 'A')
int_a_c = model.get_interface_object('A-to-C', 'A')
int_a_d = model.get_interface_object('A-to-D', 'A')

lsp_a_e_1 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_1')
lsp_a_e_2 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_2')
lsp_a_e_3 = model.get_rsvp_lsp('A', 'E', 'lsp_a_e_3')

dmd_a_e_1 = model.get_demand_object('A', 'E', 'dmd_a_e_1')
dmd_a_e_2 = model.get_demand_object('A', 'E', 'dmd_a_e_2')

# int_a_d is not rsvp_enabled, so it should have no RSVP LSPs
print("int_a_d is rsvp_enabled: {}".format(int_a_d.rsvp_enabled))
print("int_a_d has {} RSVP LSPs".format(len(int_a_d.lsps(model))))
print()
# int_a_b has 50% of capacity reservable
print("int_a_b percent_reservable_bandwidth = {}".format(int_a_b.percent_reservable_bandwidth))
print("int_a_b capacity = {}".format(int_a_b.capacity))
print("int_a_b reserved_bandwidth is {}".format(int_a_b.reserved_bandwidth))
print("int_a_b reservable_bandwidth is {}".format(int_a_b.reservable_bandwidth))
print("int_a_b reserved_bandwidth + reservable_bandwidth = {}".format(int_a_b.reserved_bandwidth
                                                                      + int_a_b.reservable_bandwidth))



