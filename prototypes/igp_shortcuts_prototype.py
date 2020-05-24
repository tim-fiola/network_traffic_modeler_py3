import sys
sys.path.append('../')

from pprint import pprint

from pyNTM import FlexModel

# Make the Parallel_Link_Model
model = FlexModel.load_model_file('igp_shortcuts_model.csv')
model.update_simulation()

