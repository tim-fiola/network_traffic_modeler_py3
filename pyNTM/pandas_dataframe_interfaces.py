from dataclasses import make_dataclass

Interfaces_dataframe = make_dataclass("Interfaces", [
    ("name", str),
    ("_failed", bool),
    ("_lat", float),
    ("_lon", float),
    ("_srlgs", set),
    ("_igp_shortcuts_enabled", bool)
])

