import sys
sys.path.append('../')

from pyNTM import FlexModel
from pyNTM.weathermap import Weathermap


model = FlexModel.load_model_file('igp_shortcuts_model.csv')
model.update_simulation()

wm = Weathermap(model)

wm.create_visualization()

