from dataclasses import make_dataclass
import pandas as pd


Nodes_dataframe = make_dataclass("Nodes_dataframe", [
    ("name", str),
    ("_failed", bool),
    ("_lat", float),
    ("_lon", float),
    ("_srlgs", set),
    ("_igp_shortcuts_enabled", bool),
])

# Nodes_dataframe = pd.DataFrame(index=['name', '_failed', '_lat', '_lon',
#                                       '_srlgs', '_igp_shortcuts_enabled'])