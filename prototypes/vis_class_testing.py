import sys
sys.path.append('../')

from pyNTM import FlexModel
from pyNTM import make_visualization_beta

#
#
#
model = FlexModel.load_model_file('model_test_topology_multidigraph.csv')
model.update_simulation()

# vis = vu.make_visualization_beta(model)
make_visualization_beta(model, font_size="20px")

# wm = Weathermap(model)
# wm.create_visualization()



