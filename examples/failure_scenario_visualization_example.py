"""
Example: Visualize a network failure scenario.

This script loads a model, captures the baseline state, then fails an
interface and a node. After re-running the simulation, it opens the
interactive visualization so you can see the traffic redistribution.

In the visualization:
  - Failed interfaces render as dashed lines
  - Interfaces are color-coded by utilization
  - Select demands to see how their paths changed after the failure

Requirements:
    - sample_network_model_file.csv in the same directory
"""

import sys

sys.path.append("../")  # noqa

from pyNTM import Model


# Load the model and run the baseline simulation
model = Model.load_model_file("sample_network_model_file.csv")
model.update_simulation()

print("Baseline interface utilization:")
model.display_interfaces_traffic()
print()

# Fail an interface and a node
print("Failing interface B-to-D on node B...")
model.fail_interface("B-to-D", "B")

print("Failing node E...")
model.fail_node("E")

# Re-converge the simulation with the failures in place
model.update_simulation()

print("\nInterface utilization after failures:")
model.display_interfaces_traffic()
print()

# Show any demands that could not be routed
unrouted = model.get_unrouted_demand_objects()
if unrouted:
    print("Unrouted demands after failures:")
    for demand in unrouted:
        print("  -", demand)
else:
    print("All demands remain routed after the failures.")
print()

# Open the interactive visualization so the failure impact is visible
model.visualize("failure_scenario_visualization.html")
