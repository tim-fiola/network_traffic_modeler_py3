import sys
sys.path.append('../')

from pyNTM import FlexModel
from pyNTM.weathermap import WeatherMap

# TODO - do functional test for this model file?  Check for correct paths?
model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path_parallel_links.csv')

model.update_simulation()

wm = WeatherMap(model)

wm.create_weathermap()