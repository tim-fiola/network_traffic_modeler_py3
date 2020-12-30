import sys
sys.path.append('../')

from pyNTM import PerformanceModel
from pyNTM import FlexModel
from pyNTM import WeatherMap
from pprint import pprint
#
#
#
model = PerformanceModel.load_model_file('sample_network_model_file.csv')
# model = FlexModel.load_model_file('igp_shortcuts_model.csv')
model.update_simulation()
model.fail_node('A')
model.fail_node('B')

model.update_simulation()

wm = WeatherMap(model)

wm.create_weathermap()