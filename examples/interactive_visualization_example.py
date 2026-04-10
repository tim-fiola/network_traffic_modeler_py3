"""
Example: Interactive network visualization with pyNTM.

This script loads a network model, runs the simulation, and opens an
interactive visualization in the browser where you can:

  - Drag nodes to rearrange the topology
  - Hover over edges to see interface utilization details
  - Select demands and LSPs to trace their paths
  - Select interfaces by node to see demands and LSPs
  - Toggle utilization ranges on/off in the legend
  - See each interface direction color-coded by utilization

Requirements:
    - sample_network_model_file.csv in the same directory
"""

import sys

sys.path.append("../")  # noqa

from pyNTM import Model


# Load the model and run the simulation
model = Model.load_model_file("sample_network_model_file.csv")
model.update_simulation()

# Print baseline utilization so you can compare with the visualization
print("Interface utilization (baseline):")
model.display_interfaces_traffic()
print()

# Open the interactive visualization in the browser
model.visualize("network_visualization.html")
