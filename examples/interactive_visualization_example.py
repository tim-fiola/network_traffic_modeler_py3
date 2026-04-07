"""
Example: Interactive network visualization with pyNTM.

This script loads a network model, runs the simulation, and opens an
interactive visualization in the browser where you can:

  - Drag nodes to rearrange the topology
  - Hover over edges to see interface utilization details
  - Click nodes/edges for a persistent info panel
  - Toggle physics simulation for auto-layout
  - See each interface direction color-coded by utilization

Requirements:
    - sample_network_model_file.csv in the same directory
"""

import sys

sys.path.append("../")  # noqa

from pyNTM import PerformanceModel
from pyNTM.interactive_visualization import InteractiveVisualization


# Load the model and run the simulation
model = PerformanceModel.load_model_file("sample_network_model_file.csv")
model.update_simulation()

# Print baseline utilization so you can compare with the visualization
print("Interface utilization (baseline):")
model.display_interfaces_traffic()
print()

# Create the interactive visualization
vis = InteractiveVisualization(model)

# Optional: customize before generating
# vis.spacing_factor = 8          # spread nodes further apart
# vis.node_size = 30              # bigger nodes
# vis.edge_width = 4              # thicker edges

# Generate and open in browser
# Pass a filename to save to a specific path, or omit for a temp file
vis.create_visualization("network_visualization.html")
