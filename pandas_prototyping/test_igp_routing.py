# You have to be in this local directory (pandas_prototyping) to run this

import sys

sys.path.append("../")

from pprint import pprint

import pandas as pd
pd.options.display.max_colwidth = 170

from pyNTM import Model



model = Model.load_model_file("igp_routing_topology.csv")
model.converge_model()

print(model.interfaces_dataframe[['_traffic', '_demands_egressing']])
