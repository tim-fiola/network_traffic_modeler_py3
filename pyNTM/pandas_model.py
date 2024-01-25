
from .exceptions import ModelException
from .utilities import find_end_index

from .pandas_node import Node
from .pandas_interface import Interface

from dataclasses import dataclass


@dataclass
class Model(object):
    interface_set: set
    node_set: set
    # demand_set: set
    # lsp_set: set

    def __repr__(self):
        return "FlexModel(Interfaces: %s, Nodes: %s,)" % (
            len(self.interface_set),
            len(self.node_set),
        )

    @classmethod
    def load_model_file(cls, data_file):

        node_set = set()

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

        interface_set, node_set = cls._extract_interface_data_and_implied_nodes(
            int_info_begin_index, int_info_end_index, lines
        )

        return cls(interface_set, node_set)

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

        interface_set = set()
        node_set = set()
        interface_lines = lines[int_info_begin_index:int_info_end_index]
        # Add the Interfaces to a set
        for interface_line in interface_lines:
            # Read interface characteristics
            if len(interface_line.split(",")) == 6:
                [
                    node_name,
                    remote_node_name,
                    name,
                    cost,
                    capacity,
                    circuit_id,
                ] = interface_line.split(",")
                rsvp_enabled_bool = True
                percent_reservable_bandwidth = 100
            elif len(interface_line.split(",")) == 7:
                [
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
                [
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

            node_names = [node.name for node in node_set]

            if node_name in node_names:
                node_object = [node for node in node_set if node.name == node_name][0]
            else:
                node_object = Node(node_name)

            if remote_node_name in node_names:
                remote_node_object = [
                    node for node in node_set if node.name == remote_node_name
                ][0]
            else:
                remote_node_object = Node(remote_node_name)

            new_interface = Interface(
                name,
                cost,
                capacity,
                node_object,
                remote_node_object,
                circuit_id,
                rsvp_enabled_bool,
                percent_reservable_bandwidth,
            )

            if new_interface._key not in {
                interface._key for interface in interface_set
            }:
                interface_set.add(new_interface)
            else:
                print(
                    "{} already exists in model; disregarding line {}".format(
                        new_interface, lines.index(interface_line)
                    )
                )

            # Derive Nodes from the Interface data
            if node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.node_object)
            if remote_node_name not in {node.name for node in node_set}:
                node_set.add(new_interface.remote_node_object)

        return interface_set, node_set
