# You have to be in this local directory (pandas_prototyping) to run this

import sys

sys.path.append("../")

from pyNTM import Model



model = Model.load_model_file("csv_flex_model_parallel_source_dest_lsps.csv")
model.converge_model()


