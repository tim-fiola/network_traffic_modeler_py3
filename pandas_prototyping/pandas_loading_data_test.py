# You have to be in this local directory (pandas_prototyping) to run this

import sys

sys.path.append("../")

from pprint import pprint

import pandas as pd
pd.options.display.max_colwidth = 170

from pyNTM import Model



model = Model.load_model_file("parallel_link_model_test_topology.csv")
model.converge_model()


print(model.interfaces_dataframe[['_demands_egressing', '_traffic', 'capacity', '_pct_utilization']])



