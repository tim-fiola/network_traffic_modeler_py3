import sys
sys.path.append('../')

from pprint import pprint

from pyNTM import Model

model = Model.load_model_file('traffic_eng_example_model.csv')
