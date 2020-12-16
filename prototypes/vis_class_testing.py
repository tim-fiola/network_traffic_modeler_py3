import sys
sys.path.append('../')

from pyNTM import FlexModel
from pyNTM.visualization_utility import make_visualization

#
#
#
model = FlexModel.load_model_file('model_test_topology_multidigraph.csv')
model.update_simulation()

# vis = vu.make_visualization(model)
make_visualization(model, font_size="20px")

# wm = Weathermap(model)
# wm.create_visualization()



