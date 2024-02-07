# You have to be in this local directory (pandas_prototyping) to run this

import sys

from pprint import pprint

sys.path.append("../")

from pyNTM import Model

model = Model.load_model_file("csv_flex_model_parallel_source_dest_lsps.csv")
model.converge_model()

df = model.interfaces_dataframe


d = model.interfaces_dataframe.to_dict()

# Need to create edge_names in form (node_name, remote_node_name, {"cost": cost,
#                                                                  "interface": interface_name,
#                                                                  "circuit_id": circuit_id})

edges = []

for x in range(len(model.interfaces_dataframe)):
    edge = (d['node_name'][x], d['remote_node_name'][x], {"cost": d['cost'][x], "interface": d['interface_name'][x],
                                                          "circuit_id": d["circuit_id"][x]})
    edges.append(edge)

edges_2 = []

for x in range(len(model.interfaces_dataframe)):
    edge = (df.loc[x, 'node_name'], df.loc[x, 'remote_node_name'], {"cost": df.loc[x, 'cost'],
                                                                    "interface": df.loc[x, 'interface_name'],
                                                                    "circuit_id": df.loc[x, "circuit_id"]})
    edges_2.append(edge)

edges_3 = [(df.loc[x, 'node_name'], df.loc[x, 'remote_node_name'], {"cost": df.loc[x, 'cost'],
                                                                    "interface": df.loc[x, 'interface_name'],
                                                                    "circuit_id": df.loc[x, "circuit_id"]})
           for x in range(len(model.interfaces_dataframe))

]


