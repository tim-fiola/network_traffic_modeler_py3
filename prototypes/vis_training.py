import sys
sys.path.append('../')

from pprint import pprint
from pyNTM import FlexModel
from pyNTM.weathermap import WeatherMap

# TODO - do functional test for this model file?  Check for correct paths?
model = FlexModel.load_model_file('igp_shortcuts_model_mult_lsps_in_path_parallel_links.csv')


model.update_simulation()

sp_a_f = model.get_shortest_path('A', 'F')
print("shortest path from A to F is:")
pprint(sp_a_f)
print()
dmd_a_f = model.get_demand_object('A', 'F', 'dmd_a_f_1')
print("dmd_a_f_1 path is:")
pprint(dmd_a_f.path)


wm = WeatherMap(model)

wm.create_weathermap()