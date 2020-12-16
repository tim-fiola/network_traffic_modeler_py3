import sys
sys.path.append('../')

from pyNTM import FlexModel
from visualization_testing_3 import make_visualization
from pyNTM import visualization_utility as vu
from pyNTM.weathermap_class import Weathermap
#
#
#
model = FlexModel.load_model_file('igp_shortcuts_model.csv')
model.update_simulation()

# vis = vu.make_visualization(model)
# make_visualization(model)

wm = Weathermap(model)
wm.create_visualization()



