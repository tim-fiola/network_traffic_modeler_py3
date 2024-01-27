from .exceptions import ModelException
from .utilities import find_end_index

from dataclasses import dataclass
import uuid
import pandas as pd
from pandas import DataFrame



@dataclass
class Model(object):
    Interfaces_DataFrame: pd.DataFrame
    Nodes_DataFrame: pd.DataFrame

    def __repr__(self):
        return "DFModel(Interfaces: %s, Nodes: %s,)" % (
            len(self.Interfaces_DataFrame),
            len(self.Nodes_DataFrame),
        )

    @classmethod
    def load_model_file(cls, data_file):

        # Open the file with the data, read it, and split it into lines
        with open(data_file, "r", encoding="utf-8-sig") as f:
            data = f.read()

        lines = data.splitlines()

        # Define the Interfaces from the data and extract the presence of
        # Nodes from the Interface data
        int_info_begin_index = lines.index("INTERFACES_TABLE") + 2
        int_info_end_index = find_end_index(int_info_begin_index, lines)

        # Check that each circuit_id appears exactly 2 times
        circuit_id_list = []
        for line in lines[int_info_begin_index:int_info_end_index]:
            try:
                circuit_id_item = line.split(",")[5]
                circuit_id_list.append(circuit_id_item)
            except IndexError:
                pass

        bad_circuit_ids = [
            {"circuit_id": item, "appearances": circuit_id_list.count(item)}
            for item in set(circuit_id_list)
            if circuit_id_list.count(item) != 2
        ]

        if len(bad_circuit_ids) != 0:
            msg = (
                "Each circuit_id value must appear exactly twice; the following circuit_id values "
                "do not meet that criteria: {}".format(bad_circuit_ids)
            )
            raise ModelException(msg)

        # TODO - add check for node uniqueness? or is this done later on already?

        interfaces_dataframe, nodes_dataframe = cls._extract_interface_data_and_implied_nodes(
            int_info_begin_index, int_info_end_index, lines
        )

        return cls(interfaces_dataframe, nodes_dataframe)

    @classmethod
    def _extract_interface_data_and_implied_nodes(
        cls, int_info_begin_index, int_info_end_index, lines
    ):
        """
        Extracts interface data from lines and adds Interface objects to a set.
        Also extracts the implied Nodes from the Interfaces and adds those Nodes to a set.

        :param int_info_begin_index: Index position in lines where interface info begins
        :param int_info_end_index:  Index position in lines where interface info ends
        :param lines: lines of data describing a Model objects
        :return: set of Interface objects, set of Node objects created from lines
        """

        interface_list = []
        node_set = set()
        interface_lines = lines[int_info_begin_index:int_info_end_index]
        # Add the Interfaces to a set
        for interface_line in interface_lines:
            # Read interface characteristics
            if len(interface_line.split(",")) == 6:
                line_data = [
                    node_name,
                    remote_node_name,
                    name,
                    cost,
                    capacity,
                    circuit_id,
                ] = interface_line.split(",")
                rsvp_enabled_bool = True  # TODO - change this to False?  Why are we defaulting to True?
                percent_reservable_bandwidth = 100  # TODO - change this to 0?
            elif len(interface_line.split(",")) == 7:
                line_data = [
                    node_name,
                    remote_node_name,
                    name,
                    cost,
                    capacity,
                    circuit_id,
                    rsvp_enabled,
                ] = interface_line.split(",")
                if rsvp_enabled in [True, "T", "True", "true"]:
                    rsvp_enabled_bool = True
                else:
                    rsvp_enabled_bool = False
                percent_reservable_bandwidth = 100
            elif len(interface_line.split(",")) >= 8:
                line_data = [
                    node_name,
                    remote_node_name,
                    name,
                    cost,
                    capacity,
                    circuit_id,
                    rsvp_enabled,
                    percent_reservable_bandwidth,
                ] = interface_line.split(",")
                if rsvp_enabled in [True, "T", "True", "true"]:
                    rsvp_enabled_bool = True
                else:
                    rsvp_enabled_bool = False
            else:
                msg = (
                    "node_name, remote_node_name, name, cost, capacity, circuit_id "
                    "must be defined for line {}, line index {}".format(
                        interface_line, lines.index(interface_line)
                    )
                )
                raise ModelException(msg)
            line_data.append(rsvp_enabled_bool)
            line_data.append(percent_reservable_bandwidth)
            # Add uuid to the interface
            line_data.append(uuid.uuid4())

            # Add node name to node_set
            node_set.add(node_name)
            node_set.add(remote_node_name)

            # See if the interface already exists, if not, add to interface_list
            if (node_name, name)not in {
                (line[0], line[2]) for line in interface_list
            }:
                interface_list.append(line_data)
            else:
                print(
                    "{} combo already exists in model; disregarding line {}".format(
                       (node_name, name), lines.index(interface_line)
                    )
                )

            # Derive Nodes from the Interface data
            if node_name not in node_set:
                node_set.add(node_name)
            if remote_node_name not in node_set:
                node_set.add(remote_node_name)

        # Convert the node_set to a list and add UUID to nodes
        # Must convert set to list because a set can't hold lists
        node_list = list(node_set)
        # Add UUID to each node for uniqueness
        node_list = [[node, uuid.uuid4()] for node in node_list]

        # Create the Node and Interface dataframes
        Nodes_Dataframe = pd.DataFrame(node_list, columns=['node_name', 'node_uuid'])
        interface_table_columns = ["node_name", "remote_node_name", "interface_name", "cost", "capacity", "circuit_id",
                                   "rsvp_enabled_bool", "percent_reservable_bandwidth", "interface_uuid"]
        Interfaces_Dataframe = pd.DataFrame(interface_list, columns=interface_table_columns )

        return Interfaces_Dataframe, Nodes_Dataframe
