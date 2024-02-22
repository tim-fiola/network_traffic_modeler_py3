from .exceptions import ModelException
from .utilities import find_end_index

from collections import Counter

from dataclasses import dataclass

import itertools

import uuid

import numpy as np
import pandas as pd
import random

import networkx as nx
from networkx.algorithms.shortest_paths.generic import shortest_path
from networkx.classes.function import path_weight

'''
To set a value in a specific cell in a dataframe:
    model.interfaces_dataframe.at[1, '_reserved_bandwidth'] = 102
'''

# TODO - figure out if to_list() can be replaced with tolist() en masse; some of the tolist references
#  have to do with numpy, vs pandas, so replace the pandas tolists with to_list

@dataclass
class Model(object):
    interfaces_dataframe: pd.DataFrame
    nodes_dataframe: pd.DataFrame
    demands_dataframe: pd.DataFrame
    lsps_dataframe: pd.DataFrame

    def __repr__(self):
        return "DFModel(Interfaces: %s, Nodes: %s,)" % (
            len(self.interfaces_dataframe),
            len(self.nodes_dataframe),
        )

    @staticmethod
    def nodes_dataframe_column_names():
        return ["node_name", "node_uuid", "lon", "lat", "igp_shortcuts_enabled", "failed"]  # TODO - add srlg_group list

    @staticmethod
    def nodes_dataframe_dtypes():
        return {"node_name": "string",
                "node_uuid": "string",
                "lon": "float64",
                "lat": "float64",
                "igp_shortcuts_enabled": "bool",
                "failed": "bool"}  # TODO - add srlg_group list

    @staticmethod
    def lsp_column_names():
        return ['source', 'dest', 'name', '_key', 'configured_setup_bw', 'manual_metric']  # TODO make dtypes dict

    @staticmethod
    def lsps_dataframe_dtypes():
        return {"source": "string",
                "dest": "string",
                "name": "string",
                "_key": "string",
                "configured_setup_bw": "float64",
                "manual_metric": "float64"
                }

    @staticmethod
    def demand_column_names():
        return ['source', 'dest', 'traffic', 'name', '_key']

    @staticmethod
    def demand_dataframe_dtypes():
        return {"source": "string",
                "dest": "string",
                "traffic": "float64",
                "name": "string",
                "_key": "string"
                }

    @staticmethod
    def interface_dataframe_column_names():
        return ["node_name", "remote_node_name", "interface_name", "cost", "capacity", "circuit_id",
                "rsvp_enabled_bool", "percent_reservable_bandwidth", "interface_uuid", "_key",
                "failed", ]  # TODO - add srlg_group list

    @staticmethod
    def interface_dataframe_dtypes(self):
        return {
            "node_name": "string",
            "remote_node_name": "string",
            "interface_name": "string",
            "cost": "float64",
            "capacity": "float64",
            "circuit_id": "string",
            "rsvp_enabled_bool": "bool",
            "percent_reservable_bandwidth": "float64",
            "interface_uuid": "string",
            "_key": "string",
            "failed": "bool"}  # TODO - add srlg_group list

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

        interfaces_dataframe, nodes_dataframe = cls._extract_interface_data_and_implied_nodes(
            int_info_begin_index, int_info_end_index, lines
        )

        # Define the explicit nodes info from the file
        nodes_info_begin_index = lines.index("NODES_TABLE") + 2
        nodes_info_end_index = find_end_index(nodes_info_begin_index, lines)
        node_lines = lines[nodes_info_begin_index:nodes_info_end_index]

        nodes_dataframe = cls._add_nodes_from_data(
            node_lines, nodes_dataframe
        )

        # Populate demands_dataframe
        demands_info_begin_index = lines.index("DEMANDS_TABLE") + 2
        demands_info_end_index = find_end_index(demands_info_begin_index, lines)
        # There may or may not be LSPs in the model, so if there are not,
        # set the demands_info_end_index as the last line in the file
        if not demands_info_end_index:
            demands_info_end_index = len(lines)

        demands_lines = lines[demands_info_begin_index:demands_info_end_index]
        demands_dataframe = cls._add_demands_from_data(demands_lines).astype(dtype=cls.demand_dataframe_dtypes())

        # Populate lsps_dataframe (if LSPs are present)
        try:
            lsp_info_begin_index = lines.index("RSVP_LSP_TABLE") + 2
            lsp_lines = lines[lsp_info_begin_index:]
            lsps_dataframe = cls._add_lsps_from_data(lsp_lines, nodes_dataframe)
        except ValueError:
            print("RSVP_LSP_TABLE not in file; no LSPs added to model")
            lsps_dataframe = None
        except ModelException as e:
            err_msg = e.args[0]
            raise ModelException(err_msg)

        # Specify data types in each column for nodes_dataframe
        nodes_dataframe = nodes_dataframe.astype(dtype=cls.nodes_dataframe_dtypes())

        # Set the dataframe indices to the _key column (node_name is the key for nodes_dataframe)
        interfaces_dataframe = interfaces_dataframe.set_index('_key')
        nodes_dataframe = nodes_dataframe.set_index('node_name')
        demands_dataframe = demands_dataframe.set_index('_key')
        try:
            lsps_dataframe = lsps_dataframe.set_index('_key')
        except AttributeError:
            # Accounts for if model does not include an RSVP_LSP_TABLE
            pass

        return cls(interfaces_dataframe, nodes_dataframe, demands_dataframe, lsps_dataframe)

    @classmethod
    def _add_lsps_from_data(
            cls, lsp_lines, nodes_dataframe
    ):
        # List of LSP info to add to lsps_dataframe
        lsps_list = []

        for lsp_line in lsp_lines:
            lsp_info = lsp_line.split(',')

            # Verify that the source node is in the nodes_dataframe
            location = nodes_dataframe.loc[nodes_dataframe['node_name'] == lsp_info[0]]
            if location.empty:
                err_msg = "No Node with name {} in Model; {}".format(lsp_info[0], lsp_line)
                raise ModelException(err_msg)

            # Verify that the dest node is in the nodes_dataframe
            location = nodes_dataframe.loc[nodes_dataframe['node_name'] == lsp_info[1]]
            if location.empty:
                err_msg = "No Node with name {} in Model; {}".format(lsp_info[1], lsp_line)
                raise ModelException(err_msg)

            try:
                configured_setup_bw = float(lsp_info[3])
            except (IndexError, ModelException, ValueError):
                configured_setup_bw = None
            try:
                manual_metric = int(lsp_info[4])
            except (IndexError, ModelException, ValueError):
                manual_metric = None

            # Define a unique key for each LSP (source___dest___name)
            _key = lsp_info[0] + "___" + lsp_info[1] + "___" + lsp_info[2]
            lsp_entry = [lsp_info[0], lsp_info[1], lsp_info[2], _key, configured_setup_bw, manual_metric]
            lsps_list.append(lsp_entry)

        lsps_dataframe = pd.DataFrame(lsps_list, columns=cls.lsp_column_names()). \
            astype(dtype=cls.lsps_dataframe_dtypes())

        # Check for LSP _key uniqueness
        cls.uniqueness_check(lsps_dataframe, '_key', 'LSP')

        return lsps_dataframe

    @classmethod
    def uniqueness_check(cls, dataframe, column_name_to_check_for_duplicates, item_type_in_column):
        """
        Checks for duplication in a column (column_name_to_check_for_duplicates)
        Args:
            dataframe: dataframe to check
            column_name_to_check_for_duplicates: column name in which to check for duplicate values
            item_type_in_column: description of the type of object the dataframe describes (node, interface, etc)

            Raises exception if duplicate found
        """
        duplicate_item_check = dataframe[column_name_to_check_for_duplicates].duplicated()
        duplicate_indices = duplicate_item_check.index[duplicate_item_check == True]
        if len(duplicate_indices) != 0:
            # Query datafrome for duplicate items
            duplicate_item_list = []
            for index in duplicate_indices:
                duplicate_item_list.append(dataframe._get_value(index, column_name_to_check_for_duplicates))
            except_msg = "Duplicate {} {} found {}; check input data " \
                .format(item_type_in_column, column_name_to_check_for_duplicates, duplicate_item_list)
            raise ModelException(except_msg)

    @classmethod
    def _add_demands_from_data(
            cls, demands_lines
    ):
        demands_list = []
        for demand in demands_lines:
            dmd = demand.split(',')
            dmd.append(dmd[0] + '___' + dmd[1] + '___' + dmd[3])
            demands_list.append(dmd)

        demands_dataframe = pd.DataFrame(demands_list, columns=cls.demand_column_names())

        # Verify uniqueness of names
        cls.uniqueness_check(demands_dataframe, 'name', 'demand')
        cls.uniqueness_check(demands_dataframe, '_key', 'demand')

        return demands_dataframe

    @classmethod
    def _add_nodes_from_data(
            cls, node_lines, nodes_dataframe
    ):
        # Build a list of nodes that are not in nodes_dataframe already
        nodes_to_add = []

        for node_line in node_lines:

            # Build a list of lists, each list with name,node_lon,node_lat,igp_shortcuts_enabled
            node_info = node_line.split(",")
            node_name = node_info[0]
            # Set latitude
            try:
                node_lat = float(node_info[2])
            except (ValueError, IndexError):
                node_lat = 0
            # Set longitude
            try:
                node_lon = float(node_info[1])
            except (ValueError, IndexError):
                node_lon = 0

            # Set igp_shortcuts_enabled bool
            try:
                igp_shortcuts_enabled = node_info[3]
                if igp_shortcuts_enabled not in ["True", "False"]:
                    raise ModelException("igp_shortcuts_enabled must be 'True' or 'False'")
            except IndexError:
                igp_shortcuts_enabled = False

            node_info_list = [node_name, node_lon, node_lat, igp_shortcuts_enabled]

            # Check to see if node_name is already in nodes_dataframe
            location = nodes_dataframe.loc[nodes_dataframe['node_name'] == node_name]

            if not location.empty:  # Node is already in the nodes_dataframe
                # Node's index in nodes_dataframe
                location_index = location.index.values[0]
                # If so, check for lat,lon,igp_shortcuts_enabled values being present
                # '== None' is appropriate here; 'is None' provides different value
                lon_missing = location.lon.values == None
                lat_missing = location.lat.values == None
                igp_shortcuts_enabled_missing = location.igp_shortcuts_enabled.values == None

                if lon_missing:
                    nodes_dataframe.at[location_index, 'lon'] = node_lon
                if lat_missing:
                    nodes_dataframe.at[location_index, 'lat'] = node_lat
                if igp_shortcuts_enabled_missing:
                    nodes_dataframe.at[location_index, 'igp_shortcuts_enabled'] = igp_shortcuts_enabled

            else:  # Node is not already in nodes_dataframe and needs to be added
                # Insert the UUID in node_info_list
                node_info_list.insert(1, uuid.uuid4())

                # Add the node failure status (set to False)
                node_info_list.append(False)

                # Update the list that we will add to the nodes_dataframe at the end
                nodes_to_add.append(node_info_list)

                # Update srlg membership

        # Add nodes_to_add to nodes_dataframe
        if len(nodes_to_add) > 0:
            additional_nodes_dataframe = pd.DataFrame(nodes_to_add, columns=cls.nodes_dataframe_column_names())
            # Combine nodes_dataframe with the additional_nodes_dataframe
            nodes_dataframe = pd.concat([nodes_dataframe, additional_nodes_dataframe])
            # Reset the index
            nodes_dataframe = nodes_dataframe.reset_index(drop=True)

        # Check for duplicate node_names (nodes must be unique)
        duplicate_node_names_check = nodes_dataframe['node_name'].duplicated()
        duplicate_node_names_indices = duplicate_node_names_check.index[duplicate_node_names_check == True]

        if len(duplicate_node_names_indices) != 0:
            # Query nodes_datafrome for duplicate nodes
            duplicate_node_names_list = []
            for index in duplicate_node_names_indices:
                duplicate_node_names_list.append(nodes_dataframe._get_value(index, 'node_name'))
            except_msg = "Duplicate node names found {}; check input data in " \
                         "'INTERFACES_TABLE' and 'NODES_TABLE'".format(duplicate_node_names_list)
            raise ModelException(except_msg)

        # Specify data types in each column for nodes_dataframe
        nodes_dataframe = nodes_dataframe.astype(dtype=cls.nodes_dataframe_dtypes())

        return nodes_dataframe

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
            # Create Interface _key for uniqueness
            _key = node_name + '___' + name
            line_data.append(_key)
            line_data.append(False)  # Failed state defaults to false
            interface_list.append(line_data)

            # Derive Nodes from the Interface data
            if node_name not in node_set:
                node_set.add(node_name)
            if remote_node_name not in node_set:
                node_set.add(remote_node_name)

        # Convert the node_set to a list and add UUID to nodes
        # Must convert set to list because a set can't hold lists
        node_list = list(node_set)
        # Add UUID to each node for uniqueness; also add None placeholder for node lat and lon and
        # igp_shortcuts_enabled.  Also add a column for Failed state boolean
        node_list = [[node, uuid.uuid4(), None, None, None, False] for node in node_list]

        # Create the Node and Interface dataframes
        nodes_dataframe = pd.DataFrame(node_list, columns=cls.nodes_dataframe_column_names())
        # Check for duplicates in nodes_dataframe
        cls.uniqueness_check(nodes_dataframe, 'node_name', 'node')

        interfaces_dataframe = pd.DataFrame(interface_list, columns=cls.interface_dataframe_column_names())
        interfaces_dataframe = interfaces_dataframe.astype(dtype=cls.interface_dataframe_dtypes(cls))

        # Check for uniqueness in interfaces_dataframe
        cls.uniqueness_check(interfaces_dataframe, '_key', 'interface')

        return interfaces_dataframe, nodes_dataframe

    def _make_weighted_network_graph_mdg(self):
        """
        Returns a networkx weighted networkx multidigraph object from
        the input Model object for non-RSVP SPF path finding

        :return: networkx multidigraph with edges that conform to the
        rsvp_required parameters
        """

        G = nx.MultiDiGraph()

        # Get all the edges that meet failed=True/False criteria

        considered_interfaces = self.interfaces_dataframe.loc[self.interfaces_dataframe
                                                              ['_interface_failed'] == False]

        # Need to create edge_names in form (node_name, remote_node_name,
        # {"cost": cost,
        # "interface": interface_name,
        # "circuit_id": circuit_id,
        # "remaining_reservable_bw": _remaining_reservable_bandwidth })

        df = considered_interfaces
        edge_names = [(df.loc[x, 'node_name'], df.loc[x, 'remote_node_name'],
                       {"cost": df.loc[x, 'cost'],
                        "interface": df.loc[x, 'interface_name'],
                        "circuit_id": df.loc[x, "circuit_id"]})
                      for x in df.index.tolist()
                    ]
        # Add edges to networkx DiGraph
        G.add_edges_from(edge_names)

        # Add all the nodes
        G.add_nodes_from(considered_interfaces.index.tolist())

        return G

    def _make_weighted_network_graph_mdg_rsvp(
            self, required_reservable_bw=0
    ):
        """
        Returns a networkx weighted networkx multidigraph object from
        the input Model object for RSVP path finding

        # TODO - add param for the amount of reservable_bandwidth needed

        :return: networkx multidigraph with edges that conform to the
        rsvp_required parameters
        """

        G = nx.MultiDiGraph()

        # Get all the edges that meet failed=True/False criteria

        # TODO - only allow considered_interfaces to have interfaces with enough reservable_bandwidth
        considered_interfaces = self.interfaces_dataframe.loc[self.interfaces_dataframe['_interface_failed'] == False]

        # Find the rsvp_enabled interfaces that also have enough _remaining_reservable_bandwidth
        # TODO - look at making this a single query for both conditions
        df_rsvp = considered_interfaces.loc[considered_interfaces['rsvp_enabled_bool'] == True]
        df_res_bw = df_rsvp.loc[df_rsvp['_remaining_reservable_bandwidth'] >= required_reservable_bw]

        # Need to create edge_names in form (node_name, remote_node_name,
        # {"cost": cost,
        # "interface": interface_name,
        # "circuit_id": circuit_id,
        # "remaining_reservable_bw": _remaining_reservable_bandwidth })
        edge_names = [(df_res_bw.loc[x, 'node_name'], df_res_bw.loc[x, 'remote_node_name'],
                       {"cost": df_res_bw.loc[x, 'cost'],
                        "interface": df_res_bw.loc[x, 'interface_name'],
                        "circuit_id": df_res_bw.loc[x, "circuit_id"],
                        "remaining_reservable_bw": df_res_bw.loc[x, "_remaining_reservable_bandwidth"]})
                      for x in df_res_bw.index.tolist()
        ]

        # Add edges to networkx DiGraph
        G.add_edges_from(edge_names)

        # Add all the nodes
        G.add_nodes_from(considered_interfaces.index.tolist())

        return G

    def validated_circuit_ids(self):
        """

        Returns: A list of circuit IDs that have been verified to have exactly 2 occurrences in the
        interfaces_dataframe

        """

        # Get the circuit_ids from the dataframe
        circuit_ids = self.interfaces_dataframe['circuit_id'].to_list()
        # Count the occurrence of each circuit ID
        ckt_id_occurrences = Counter(circuit_ids)
        # Get the values the occurrences of each circuit_id
        unique_circuit_ids = ckt_id_occurrences.values()
        # The set of circuit_ids should be == {2} because each circuit_id maps to exactly two interfaces
        valid_id_matching = set(unique_circuit_ids) == {2}

        if valid_id_matching:
            return list(ckt_id_occurrences.keys())
        else:
            violations = {}
            for k, v in ckt_id_occurrences:
                if v != 2:
                    violations[k] = v
            except_msg = "The following circuit IDs appear, but not exactly two times. " \
                         "This dict has key, value = circuit_id, # of occurrences  {}".format(violations)
            raise ModelException(except_msg)

    def _circuit_ids_validated(self):
        """
        Validates the interfaces in a dataframe
        - each circuit ID is used exactly two interfaces

        Returns:
            Boolean True if the dataframe passes tests; raises ModelException if
            any circuit_id does not occur exactly twice

        """

        # Get the circuit_ids from the dataframe
        circuit_ids = self.interfaces_dataframe['circuit_id'].to_list()
        # Count the occurrence of each circuit ID
        ckt_id_occurrences = Counter(circuit_ids)
        # Get the values the occurrences of each circuit_id
        unique_circuit_ids = ckt_id_occurrences.values()
        # The set of circuit_ids should be == {2} because each circuit_id maps to exactly two interfaces
        valid_id_matching = set(unique_circuit_ids) == {2}

        if valid_id_matching:
            return True
        else:
            violations = {}
            for k, v in ckt_id_occurrences:
                if v != 2:
                    violations[k] = v
            except_msg = "The following circuit IDs appear, but not exactly two times. " \
                         "This dict has key, value = circuit_id, # of occurrences:  {}".format(violations)
            raise ModelException(except_msg)

    def mismatched_circuit_capacities(self):
        """
        Verify that the interface capacities that have a common circuit_id have matching capacities
        Verify that there are only 2 instances of a given circuit_id in the interfaces_dataframe
        Returns: A list of interfaces with common ciruit_id but whose capacities don't match

        """

        ckt_ids_w_mismatched_capacities = []

        # Query the interfaces for a given id to make sure the capacities match
        for ckt_id in self.validated_circuit_ids():  # TODO - see if we can get rid of the python iteration
            capacities = self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id]['capacity']
            # Verify that there are only 2 rows
            if len(capacities != 2):
                ckt_ids_w_mismatched_capacities.append(ckt_id)
                error_msg = "The circuit_id {} has {} entries in the interfaces_dataframe; there must be exactly 2" \
                            "entries with a given circuit_id.  Check input data". \
                    format(ckt_id, len(capacities))
                raise ModelException(error_msg)
            # Verify that the capacities match in the 2 rows with the common circuit_id
            if capacities.values[0] != capacities.values[1]:
                ckt_ids_w_mismatched_capacities.append(ckt_id)

        if len(ckt_ids_w_mismatched_capacities) > 0:
            error_msg = "The following circuit_id values have mismatched interface capacities: \n {}". \
                format(ckt_ids_w_mismatched_capacities)
            raise ModelException(error_msg)

    def _reserved_bw_error_checks(self):
        """
        Checks interface for the following:
        - Is reserved_bandwidth > capacity?
        - Does reserved_bandwidth for interface match the sum of the
        reserved_bandwidth for the LSPs egressing interface?
        """

        # Query the interfaces_dataframe for columns where _reserved_bandwidth > capacity
        res_bw_errors = self.interfaces_dataframe.loc[
            self.interfaces_dataframe['_reserved_bandwidth'] > self.interfaces_dataframe['capacity']]

        if len(res_bw_errors) > 0:
            error_msg = "There was an internal error: '_reserved_bandwidth > 'capacity' on these interfaces: \n {}" \
                .format(res_bw_errors)
            raise ModelException(error_msg)

    def validate_model(self):
        """
        Validates that data fed into the model creates a valid network model
        """
        # Verify no duplicate node names

        # Check for duplicates in nodes_dataframe
        self.uniqueness_check(self.nodes_dataframe, 'node_name', 'node')

        # Check for uniqueness for interface names in interfaces_dataframe
        self.uniqueness_check(self.interfaces_dataframe, '_key', 'interface')

        # Validate LSP name uniqueness check
        self.uniqueness_check(self.lsps_dataframe, 'name', 'lsp')

        # Verify that each circuit_id appears exactly twice
        circuit_ids_validated = self._circuit_ids_validated(self.interfaces_dataframe)

        # Verify circuit component interfaces have matching capacity
        self.mismatched_circuit_capacities()

        # Validate RSVP reserved bandwidth is not gt interface capacity
        self._reserved_bw_error_checks()

        # Verify no SRLG errors  # TODO - add this when srlgs are in model

    def _populate_lsp_src_dest_nodes(self):
        """
        Populates the _src_dest_nodes column in the lsps_dataframe

        """
        try:
            self.lsps_dataframe["_src_dest_nodes"] = self.lsps_dataframe['source'] + "___" + self.lsps_dataframe['dest']
        except TypeError:
            # Model may not have RSVP LSPs; so pass
            pass

    def _route_lsps(self):
        """
        Route LSPs in model

        """
        # Add column _routed to lsps_dataframe
        # NOTE - this 2 step method to add columns was needed to specify the dtype for the
        # column and to prevent a 'future warning' from pandas
        self.lsps_dataframe['_routed'] = None
        self.lsps_dataframe['_routed'].astype(bool)

        # Add column _path to lsps_dataframe
        self.lsps_dataframe['_path'] = None
        self.lsps_dataframe['_path'].astype(object)

        # Add column _reserved_bandwidth to lsps_dataframe
        self.lsps_dataframe['_reserved_bandwidth'] = None
        self.lsps_dataframe['_reserved_bandwidth'].astype(float)

        # Add column _shortest_path_cost to lsps_dataframe
        self.lsps_dataframe['_shortest_path_cost'] = None
        self.lsps_dataframe['_shortest_path_cost'].astype(float)

        # Add column _on_shortest_path to lsps_dataframe
        self.lsps_dataframe['_on_shortest_path'] = None
        self.lsps_dataframe['_on_shortest_path'].astype(bool)

        # Add column _effective_path_cost to lsps_dataframe; this column will either reflect
        # each LSP's manual_metric or its shortest_path_cost
        self.lsps_dataframe['_effective_path_cost'] = None
        self.lsps_dataframe['_effective_path_cost'].astype(float)

        # Add column _demands to hold a list of demands a given LSP carries
        self.lsps_dataframe['_demands'] = None
        self.lsps_dataframe['_demands'].astype(object)
        self.lsps_dataframe['_demands'] = np.empty((len(self.lsps_dataframe), 0)).tolist()

        # Get parallel LSP Groups
        parallel_lsp_groups = self.lsps_dataframe._src_dest_nodes.unique()

        # For each parallel LSP group, get the corresponding demand group
        for lsp_group in parallel_lsp_groups:
            demands = self.demands_dataframe[self.demands_dataframe['_src_dest_nodes'] == lsp_group]
            traffic = demands['traffic'].sum()

            # Find around of setup bandwidth each LSP needs
            self._determine_lsp_reserved_bw(lsp_group, traffic)

            # Determine specific paths for each LSP
            self._find_lsp_paths(lsp_group)

    def _recalculate_remaining_res_bw(self):
        """
        Recalculates the _remaining_reservable_bandwidth column for the interfaces_dataframe
        """
        self.interfaces_dataframe['_remaining_reservable_bandwidth'] = \
            round(self.interfaces_dataframe['capacity'] * self.interfaces_dataframe['percent_reservable_bandwidth'] \
            / 100 - self.interfaces_dataframe['_reserved_bandwidth'], 2)

    def _find_lsp_paths(self, lsp_group):
        """
        Determine paths for each LSP in lsps
        Args:
            lsp_group: Indicator consisting of (source node name)___(destination node name),
            which is also the lsp_group key in self.lsps_dataframe

        """

        source_node, dest_node = lsp_group.split('___')

        # ## Find path metric in networkx (zero required_reservable_bw since we want actual shortest path) ## #
        # Make a networkx graph
        G = self._make_weighted_network_graph_mdg_rsvp(
            required_reservable_bw=0
        )

        # Get the shortest paths in networkx multidigraph
        try:
            nx_sp = list(
                nx.all_shortest_paths(
                    G,
                    source_node,
                    dest_node,
                    weight="cost",
                )
            )
        except nx.exception.NetworkXNoPath:
            # There is no path.
            # Find the row of the lsp_group (_src_dest_nodes) in the lsps_dataframe and update the _path,
            # _routed, and _reserved_bandwidth cells
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group, '_routed'] = False
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group, '_path'] = np.nan
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group, '_reserved_bandwidth'] = np.nan
            return  # TODO - can/should continue work here instead?

        # Mark LSPs as _routed = True
        self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group, '_routed'] = True

        path = shortest_path(G, source_node, dest_node, weight='cost')
        lowest_metric = path_weight(G, path, weight="cost")

        # Populate the '_shortest_path_cost' for each LSP in lsp_group in lsps_dataframe
        self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] ==
                                lsp_group, '_shortest_path_cost'] = lowest_metric

        # Get the LSPs in the LSP group from the lsps_dataframe
        lsp_indices = (self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group]).index.to_list()

        for lsp_index in lsp_indices:
            self._find_lsp_path(source_node, dest_node, lsp_index, lsp_group, lowest_metric)

        # Assign the _effective_path_cost value to the manual_metric value if it's populated; otherwise
        # set it to the _shortest_path_cost
        self.lsps_dataframe['_effective_path_cost'] = self.lsps_dataframe['_shortest_path_cost']
        self.lsps_dataframe.loc[self.lsps_dataframe['manual_metric'].notnull(), '_effective_path_cost'] = \
            self.lsps_dataframe['manual_metric']

    def _find_lsp_path(self, source_node, dest_node, lsp_index, lsp_group, lowest_metric):
        """
        Calculates the path for the LSP with lsp_index and updates the _path value for the LSP.
        Also updates the following columns in the interfaces_dataframe for interfaces that are in the LSP's path:
        - _reserved_bandwidth
        - _reservable_bandwidth
        - _lsps_egressing
        - _remaining_reservable_bandwidth

        Args:
            source_node: LSP destination node
            dest_node: LSP destination node
            lsp_index: lsp_index from lsps_dataframe
            lsp_group: LSP's _srce_dest_nodes value
            lowest_metric: cost for the shortest path between source_node and dest_node
        """

        # Establish candidate paths with enough reservable bandwidth
        lsp_info = self.lsps_dataframe.loc[lsp_index]

        # Get the LSP's _reserved_bandwidth
        setup_bw = lsp_info['_reserved_bandwidth']

        # Find the paths that have _remaining_reservable_bandwidth >= setup_bw
        G = self._make_weighted_network_graph_mdg_rsvp(
            required_reservable_bw=setup_bw
        )
        # Get the shortest paths in networkx multidigraph
        try:
            nx_sp = list(
                nx.all_shortest_paths(
                    G,
                    source_node,
                    dest_node,
                    weight="cost",
                )
            )
        except nx.exception.NetworkXNoPath:
            # There is no path
            # Find the row of the lsp_group (_src_dest_nodes) in the lsps_dataframe and update the _path,
            # _routed, and _reserved_bandwidth cells
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] ==
                                    lsp_group, '_routed'] = False
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] ==
                                    lsp_group, '_path'] = np.nan
            self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] ==
                                    lsp_group, '_reserved_bandwidth'] = np.nan

        # Convert node hop by hop paths from G into Interface-based paths
        all_paths = self._get_all_paths_mdg(G, nx_sp, rsvp=True)
        # Make sure that each path in all_paths only has a single link between each node.  This is path normalization
        candidate_path_info = self._normalize_multidigraph_paths(all_paths)

        # Find path metrics
        paths_w_metrics = self.find_path_metrics(candidate_path_info)

        # If multiple paths_w_metrics, find those with the fewest hops
        if len(paths_w_metrics) > 1:
            # Find the path with the lowest path metric
            fewest_hops = min(
                len(path['path']) for path in paths_w_metrics
            )
            lowest_hop_count_paths = [
                path
                for path in paths_w_metrics
                if len(path['path']) == fewest_hops
            ]
            if len(lowest_hop_count_paths) > 1:
                lsp_path = random.choice(lowest_hop_count_paths)
            else:
                lsp_path = lowest_hop_count_paths[0]
        else:
            lsp_path = paths_w_metrics[0]

        # Remove the remaining_reservable_bw from the lsp_path interfaces since it's not useful anymore
        for interface in lsp_path['path']:
            del (interface['remaining_reservable_bw'])

        # Populate the lsp_path in the lsps_dataframe in a list
        self.lsps_dataframe.at[lsp_index, '_path'] = [lsp_path]

        # ## Update the interfaces dataframe ## #
        for interface in lsp_path['path']:
            _res_bw = self.lsps_dataframe.at[lsp_index, '_reserved_bandwidth']
            int_key = interface['current_node'] + "___" + interface['int_name']
            current_int_res_bw = self.interfaces_dataframe.at[int_key, '_reserved_bandwidth']
            # Update the _reserved_bandwidth for the interface
            self.interfaces_dataframe.at[int_key, '_reserved_bandwidth'] = current_int_res_bw + _res_bw
            # Update the _lsps_egressing for the interface
            self.interfaces_dataframe.at[int_key, '_lsps_egressing'].append(lsp_index)
            # Update the _remaining_reservable_bandwidth for the interface
            self.interfaces_dataframe.at[int_key, '_remaining_reservable_bandwidth'] = self.interfaces_dataframe.at[int_key,'capacity'] * self.interfaces_dataframe.at[int_key, 'percent_reservable_bandwidth'] - self.interfaces_dataframe.at[int_key, '_reserved_bandwidth']

        # Populate the _on_shortest_path value for the lsp with lsp_index  # TODO - maybe put if/then in the query
        if lsp_path['path_cost'] == lowest_metric:
            self.lsps_dataframe.at[lsp_index, '_on_shortest_path'] = True
        else:
            self.lsps_dataframe.at[lsp_index, '_on_shortest_path'] = False

    def find_path_metrics(self, path_info):
        """

        Args:
            path_info: list of paths with each path in the format shown in this example:
              [{'current_node': 'A',
              'int_cost': 4.0,
              'int_name': 'A-to-B_2',
              'remaining_reservable_bw': 50.0},
              {'current_node': 'B',
              'int_cost': 4.0,
              'int_name': 'B-to-D_2',
              'remaining_reservable_bw': 200.0}]

              This example above shows a path with 2 hops


        Returns: The path info # TODO - finish this description when you have an example

        """
        paths_w_metrics = []
        for path in path_info:
            path_cost = 0
            for hop in path:
                path_cost += hop['int_cost']
            paths_w_metrics.append({'path': path, 'path_cost': path_cost})
        return paths_w_metrics

    def _normalize_multidigraph_paths(self, path_info):  # TODO - static?
        """
        Takes the multidigraph_path_info and normalizes it to create all the
        path combos that only have one link between each node.

        :param path_info: List of of interface hops from a source
        node to a destination node.  Each hop in the path
        is a list of all the interfaces from the current node
        to the next node.

        :return: List of lists.  Each component list is a list with a unique
        Interface combination for the egress Interfaces from source to destination

        path_info example from source node 'B' to destination node 'D'.
        Example::

            [
                [[Interface(name = 'B-to-D', cost = 20, capacity = 125, node_object = Node('B'),
                        remote_node_object = Node('D'), circuit_id = '3')]], # there is 1 interface from B to D and a
                        complete path
                [[Interface(name = 'B-to-G_3', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '28'),
                  Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '8'),
                  Interface(name = 'B-to-G_2', cost = 10, capacity = 100, node_object = Node('B'),
                        remote_node_object = Node('G'), circuit_id = '18')], # there are 3 interfaces from B to G
                [Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                        remote_node_object = Node('D'), circuit_id = '9')]] # there is 1 int from G to D; end of path 2
            ]

        Example::

            [
                [Interface(name = 'B-to-D', cost = 20, capacity = 125, node_object = Node('B'),
                    remote_node_object = Node('D'), circuit_id = '3')], # this is a path with one hop
                [Interface(name = 'B-to-G_3', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '28'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')], # this is a path with 2 hops
                [Interface(name = 'B-to-G_2', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '18'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')], # this is a path with 2 hops
                [Interface(name = 'B-to-G', cost = 10, capacity = 100, node_object = Node('B'),
                    remote_node_object = Node('G'), circuit_id = '8'),
                 Interface(name = 'G-to-D', cost = 10, capacity = 100, node_object = Node('G'),
                    remote_node_object = Node('D'), circuit_id = '9')]  # this is a path with 2 hops
            ]

        """
        # List to hold unique path(s)
        path_list = []

        for path in path_info:
            path = list(itertools.product(*path))
            for path_option in path:
                path_list.append(list(path_option))

        return path_list

    def _get_all_paths_mdg(self, G, nx_sp, rsvp=False):
        """
        Examines hop-by-hop paths in G and determines specific
        edges transited from one hop to the next

        :param G:  networkx multidigraph object containing nx_sp, contains
        Interface objects in edge data
        :param nx_sp:  List of node paths in G

        Example::

            nx_sp from A to D in graph G::
             [['A', 'D'], ['A', 'B', 'D'], ['A', 'B', 'G', 'D']]

        :return:  List of lists of possible specific model paths from source to
        destination nodes.  Each 'hop' in a given path may include multiple possible
        Interfaces that could be transited from one node to the next adjacent node.

        Example return::

            all_paths from 'A' to 'D' is a list of lists; notice that there are
            two Interfaces that could be transited from Node 'B' to Node 'G' # TODO - update this example
            [[[Interface(name = 'A-to-D', cost = 40, capacity = 20.0, node_object = Node('A'),
                remote_node_object = Node('D'), circuit_id = 1)]],
            [[Interface(name = 'A-to-B', cost = 20, capacity = 125.0, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 2)],
             [Interface(name = 'B-to-D', cost = 20, capacity = 125.0, node_object = Node('B'),
                remote_node_object = Node('D'), circuit_id = 3)]],
            [[Interface(name = 'A-to-B', cost = 20, capacity = 125.0, node_object = Node('A'),
                remote_node_object = Node('B'), circuit_id = 4)],
             [Interface(name = 'B-to-G', cost = 10, capacity = 100.0, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 5),
              Interface(name = 'B-to-G_2', cost = 10, capacity = 50.0, node_object = Node('B'),
                remote_node_object = Node('G'), circuit_id = 6)],
            [Interface(name = 'G-to-D', cost = 10, capacity = 100.0, node_object = Node('G'),
                remote_node_object = Node('D'), circuit_id = 7)]]]

        """

        all_paths = []
        for path in nx_sp:
            current_hop = path[0]
            this_path = []
            for next_hop in path[1:]:
                this_hop = []
                values_source_hop = G[current_hop][next_hop].values()
                min_weight = min(d["cost"] for d in values_source_hop)
                ecmp_links = [
                    interface_index
                    for interface_index, interface_item in G[current_hop][next_hop].items()
                    if interface_item["cost"] == min_weight
                ]

                # Add Interface(s) to this_hop list
                for link_index in ecmp_links:
                    hop_data = {"current_node": current_hop,
                                "int_name": G[current_hop][next_hop][link_index]["interface"],
                                "int_cost": G[current_hop][next_hop][link_index]["cost"]
                                }
                    if rsvp is True:
                        hop_data["remaining_reservable_bw"] = G[current_hop][next_hop][link_index]["remaining_reservable_bw"],
                    this_hop.append(hop_data)
                this_path.append(this_hop)
                current_hop = next_hop

            all_paths.append(this_path)
        return all_paths

    def _determine_lsp_reserved_bw(self, lsp_group, traffic):
        """
        Determine reserved bandwidth for each LSP

        Args:
            lsp_group: name of grouping for LPSs with common source and destination
            traffic: amount of traffic to be added to parallel LSPs
        """

        # Get the LSPs in the LSP group from the lsps_dataframe
        lsps = self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] == lsp_group]

        # Update the _reserved_bandwidth for the LSPs in lsp_group
        self.lsps_dataframe.loc[self.lsps_dataframe['_src_dest_nodes'] ==
                                lsp_group, ['_reserved_bandwidth']] = round(float(traffic) / len(lsps), 2)

        # Check to see if configured_setup_bw is set; if so, set
        # _reserved_bandwidth to configured_setup_bandwidth value
        self.lsps_dataframe.loc[self.lsps_dataframe['configured_setup_bw'].notnull(),
                                '_reserved_bandwidth'] = self.lsps_dataframe['configured_setup_bw']

    def _populate_dmd_src_dest_nodes(self):
        """
        Populates the _src_dest_nodes column in the demands_dataframe

        """

        self.demands_dataframe["_src_dest_nodes"] = self.demands_dataframe['source'] + "___" \
                                                    + self.demands_dataframe['dest']

    # def _populate_dmd_src_dest_agg_traffic(self):  # TODO - this may not be needed; remove if so
    #     """
    #     Populates the sum of the 'traffic' values for demands with common _src_dest_nodes
    #     value.  Adds this sum in a _src_dest_nodes_agg_traffic column
    #
    #     """
    #
    #     # Find the unique demand groups
    #     unique_dmd_groups = self.demands_dataframe._src_dest_nodes.unique()
    #
    #     for dmd_group in unique_dmd_groups:  # TODO - can this be done without a python iteration?
    #         # Sum up the traffic for each unique demand group
    #         traff_sum = self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes']
    #                                                == dmd_group, 'traffic'].sum()
    #
    #         # Populate traffic sum for each demand group in a new _src_dest_nodes_agg_traffic column
    #         self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes'] ==
    #                                    dmd_group, '_src_dest_nodes_agg_traffic'] = traff_sum

    def converge_model(self):
        """
        Updates the simulation state; this needs to be run any time there is
        a change to the state of the Model, such as failing an interface, adding
        a Demand, adding/removing and LSP, etc.

        This call does not carry forward any state from the previous simulation
        results.
        """

        # Populate _src_dest_nodes column in lsps_dataframe
        self._populate_lsp_src_dest_nodes()

        # Populate _src_dest_nodes column in demands_dataframe
        self._populate_dmd_src_dest_nodes()

        # Add an empty _path column in the demands_dataframe
        self.demands_dataframe['_path'] = None
        self.demands_dataframe['_path'].astype(object)
        self.demands_dataframe['_path'] = np.empty((len(self.demands_dataframe), 0)).tolist()


        # Add a _reserved_bandwidth column that will reflect how much bandwidth is
        # reserved by LSPs and baseline it to 0
        self.interfaces_dataframe['_reserved_bandwidth'] = None
        self.interfaces_dataframe['_reserved_bandwidth'].astype(float)
        self.interfaces_dataframe['_reserved_bandwidth'] = 0.0

        # Add a _remaining_reservable_bandwidth column that will reflect how much
        # bandwidth is left to be reserved by LSPs
        self.interfaces_dataframe['_remaining_reservable_bandwidth'] = None
        self.interfaces_dataframe['_remaining_reservable_bandwidth'].astype(float)
        self._recalculate_remaining_res_bw()  # TODO - can this be moved/removed?

        # Add a _lsps_egressing column that will hold a list of LSPs that egress that interface
        self.interfaces_dataframe['_lsps_egressing'] = None
        self.interfaces_dataframe['_lsps_egressing'].astype(object)
        self.interfaces_dataframe['_lsps_egressing'] = np.empty((len(self.interfaces_dataframe), 0)).tolist()

        # Add a _demands_egressing column that will hold a list of demands that egress that interface
        self.interfaces_dataframe['_demands_egressing'] = None
        self.interfaces_dataframe['_demands_egressing'].astype(object)
        self.interfaces_dataframe['_demands_egressing'] = np.empty((len(self.interfaces_dataframe), 0)).tolist()

        # Add _circuit_failed and _interface_failed status columns and compute values of each
        self._set_circuit_and_int_status()

        # Route the LSPs, if present
        try:
            self._route_lsps()
        except TypeError:
            pass

        # Route the Demands
        self._route_demands()

    def _route_demands(self):
        """
        Route the traffic demands in the demands_dataframe
        """

        # Add an empty _pct_utilization column in the interfaces_dataframe; this will be utilization in pct
        self.interfaces_dataframe['_pct_utilization'] = None
        self.interfaces_dataframe['_pct_utilization'].astype(float)
        self.interfaces_dataframe['_pct_utilization'] = 0.0

        # Add an empty _traffic column in the interfaces_dataframe
        self.interfaces_dataframe['_traffic'] = None
        self.interfaces_dataframe['_traffic'].astype(float)
        self.interfaces_dataframe['_traffic'] = 0.0

        # Graph for routing demands via SPF
        G = self._make_weighted_network_graph_mdg()

        # Find the unique _src_dest_nodes values in demands_dataframe
        src_dest_groups = self.demands_dataframe['_src_dest_nodes'].unique().tolist()

        for src_dest_group in src_dest_groups:
            # Find the aggregate traffic for all the demands in the src_dest_group
            demands = self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes'] == src_dest_group]
            agg_traffic = round(demands['traffic'].sum(), 2)

            # Find all LSPs that can carry the agg_traffic from source to destination (matching src_dest_group)
            if self.lsps_dataframe:
                lsps_src_dest = self.lsps_dataframe[self.lsps_dataframe['_src_dest_nodes'] == src_dest_group]
                if lsps_src_dest.empty:
                    self._route_demands_via_spf(G, agg_traffic, demands, src_dest_group)
                else:
                    self._route_demands_via_source_dest_lsps(agg_traffic, demands, lsps_src_dest)
            else:
                self._route_demands_via_spf(G, agg_traffic, demands, src_dest_group)

    def _route_demands_via_spf(self, G, agg_traffic, demands, src_dest_group):
        # There are no LSPs that can carry the demand(s) from source to destination
        # Route the demands in src_dest_group via SPF
        node_info = src_dest_group.split('___')
        source_node = node_info[0]
        dest_node = node_info[1]
        try:
            nx_sp = list(
                nx.all_shortest_paths(
                    G,
                    source_node,
                    dest_node,
                    weight="cost",
                )
            )
        except nx.exception.NetworkXNoPath:
            # There is no path.
            # Find the row of the lsp_group (_src_dest_nodes) in the lsps_dataframe and update the _path,
            # _routed, and _reserved_bandwidth cells
            self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes'] == src_dest_group, '_routed'] = False
            self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes'] == src_dest_group, '_path'] = np.nan
            return  # TODO - can/should continue work here instead?
        # Mark demands as _routed = True
        self.demands_dataframe.loc[self.demands_dataframe['_src_dest_nodes'] == src_dest_group, '_routed'] = True
        # Convert node hop by hop paths from G into Interface-based paths
        all_paths = self._get_all_paths_mdg(G, nx_sp)
        # Make sure that each path in all_paths only has a single link between
        # each node.  This is path normalization
        candidate_path_info = self._normalize_multidigraph_paths(all_paths)
        # Find path metrics
        paths_w_metrics = self.find_path_metrics(candidate_path_info)  # TODO - get this to have remote node name as well??

        # ## This next part is designed to get the amount of splits that the demand(s) will hit at    ## #
        # ## each node.  This is important to understand in order to allocate each unique demand path ## #
        # ## the correct amount of traffic.  This is needed to simulate how per-hop ECMP works.       ## #
        # ## There is likely an elegant solution to this problem; I'm not sure that the below is that ## #
        # ## specific elegant solution, but it does work properly.                                    ## #

        # Get all pairs of nodes and each of the next hop nodes for that node in a dict
        # Ex: {'A_D': 2, 'D_F': 1, 'A_B': 1, 'B_D': 1, 'B_G': 1, 'G_D': 1}
        next_hop_dict = {}
        # Get a set of all nodes in the path, except the destination node
        # Ex: {'B', 'G', 'A', 'D'}
        node_set = set()

        # Populate the next_hop_dict; initialize all keys to 0
        for nx_sp_path in nx_sp:
            for x in range(0, len(nx_sp_path)-1):
                next_hop_pair = nx_sp_path[x]+'_'+nx_sp_path[x+1]
                next_hop_dict[next_hop_pair] = 0
                node_set.add(nx_sp_path[x])

        # Populate the amount of links between each node pair key in next_hop_dict
        for node_pair in next_hop_dict:
            source, dest = node_pair.split('_')
            df_query = "node_name == '{}' and remote_node_name == '{}'".format(source, dest)
            node_splits = len(self.interfaces_dataframe.query(df_query))
            next_hop_dict[node_pair] += node_splits

        # Make a dict that has the nodes as keys and the total amount of next hop interfaces as values
        node_split_dict = dict.fromkeys(node_set, 0)

        # Parse the next_hop_dict for total splits at each node
        # We want a final node_split_dict that looks like this: {'A': 3, 'B': 2, 'D': 1, 'G': 1}
        for node_pair, next_hop_count in next_hop_dict.items():
            current_node = node_pair.split('_')[0]
            node_split_dict[current_node] += next_hop_count

        # Iterate over the demands to fill in the interfaces and demands dataframes
        for demand in demands.index.to_list():
            # ## Update the interfaces dataframe # ##
            for path in paths_w_metrics:
                # Craft the interface key for each hop

                # ## Define cumulative splits for the entire path; this is the crucial part in ensuring            ## #
                # ## that we model per-hop load balancing, which is what ECMP does, versus per-path load balancing ## #
                cumulative_splits_for_path = 1
                # Craft the node path from the path
                nodes_on_path = [hop['current_node'] for hop in path['path']]
                # Use the node_split_dict to calculate the total times the demand is split on the given path
                for node in nodes_on_path:
                    cumulative_splits_for_path *= node_split_dict[node]

                for hop in path['path']:
                    interface_key = hop['current_node'] + "___" + hop['int_name']

                    # Update each interface in the demand path(s) for _traffic
                    self.interfaces_dataframe.at[interface_key, '_traffic'] = \
                        self.interfaces_dataframe.at[interface_key, '_traffic'] + \
                        round(agg_traffic / cumulative_splits_for_path, 2)  # TODO - update this with demand traffic

                    # Update each interface in the demand path(s) for _demands_egressing
                    for demand_index in demands.index.to_list():
                        self.interfaces_dataframe.at[interface_key, '_demands_egressing'].append(
                            {'demand': demand_index, 'traffic': round(agg_traffic / cumulative_splits_for_path, 2)}  # TODO - update this with demand traffic
                        )

                    # Update each interface in the demand path(s) for the _pct_utilization
                    self.interfaces_dataframe.at[interface_key, '_pct_utilization'] = \
                        round(self.interfaces_dataframe.at[interface_key, '_traffic'] / \
                              self.interfaces_dataframe.at[interface_key, 'capacity'], 2)

                import pdb
                pdb.set_trace()
                # Update the demand with the path info, including the traffic on each ECMP path
                path_w_traffic = path['traffic_on_path'] = round(agg_traffic / cumulative_splits_for_path, 2)
                self.demands_dataframe.at[interface_key, '_path'].append(path_w_traffic)

    # # Append the SPF paths to the demands _path columns
    # for path in paths_w_metrics:
    #     for demand_key in demands.index.to_list():
    #         self.demands_dataframe.at[demand_key, '_path'].append(path)

    def _route_demands_via_source_dest_lsps(self, agg_traffic, demands, lsps_src_dest):
        """
        Routes the demands in demands over the LSPs in lsps_src_dest
        Args:
            agg_traffic: sum of traffic in demands
            demands: demands from model that have same _src_dest_nodes value as lsps_src_dest
            lsps_src_dest: LSPs from model that have same _src_dest_nodes value as demands

        """
        # Find the lowest metric for the LSPs in lsps_src_dest
        lowest_metric = min(lsps_src_dest['_effective_path_cost'].to_list())
        # Get all the LSPs in lsps_src_dest with the lowest_metric
        lowest_metric_lsps = lsps_src_dest.loc[lsps_src_dest['_effective_path_cost'] == lowest_metric]
        # ## Route the demands across the lowest_metric_lsps ## #
        # Update the demand path(s) to the LSPs in lowest_metric_lsps for each of the lsps in ls
        for demand in demands.index.to_list():  # TODO - get the demand indices separated; they are used like 4 times here
            self.demands_dataframe.at[demand, '_path'] = lowest_metric_lsps.index.to_list()
            # Mark the demand as routed
            self.demands_dataframe.at[demand, '_routed'] = True
        # Update the interfaces dataframe
        for lsp in lowest_metric_lsps.index.to_list():
            # Get the interfaces in the lsp's _path, which is a list that holds a dict
            path_interfaces = lsps_src_dest.at[lsp, '_path'][0]['path']

            # Craft the keys for each interface in path_interfaces
            interface_key_list = [interface['current_node'] + "___" + interface['int_name'] for
                                  interface in path_interfaces]

            for interface in interface_key_list:
                # Update the _traffic column for the interfaces that the lsp(s) ride
                self.interfaces_dataframe.at[interface, '_traffic'] = \
                    self.interfaces_dataframe.at[interface, '_traffic'] + round(agg_traffic / len(lowest_metric_lsps), 2)

                # Update _pct_utlization for the interfaces that the demand(s) egress
                self.interfaces_dataframe.at[interface, '_pct_utilization'] = \
                    round(self.interfaces_dataframe.at[interface, '_traffic'] / \
                    self.interfaces_dataframe.at[interface, 'capacity'], 2)

                # Update the _demands_egressing column for the interfaces that the demand(s) egress
                for demand_index in demands.index.to_list():
                    demand_traffic = self.demands_dataframe.at[demand_index, 'traffic']
                    self.interfaces_dataframe.at[interface, '_demands_egressing']. \
                        append({'demand': demand_index, 'traffic': round(demand_traffic / len(lowest_metric_lsps), 2)})

            # Update the list of demands the lsp carries
            for demand in demands.index.to_list():
                traffic = round(agg_traffic/len(demands.index.to_list()), 2)
                self.lsps_dataframe.at[lsp, '_demands'].append({'demand': demand, 'traffic': traffic})

    def _set_circuit_and_int_status(self):

        """
        Read the interface for each circuit_id and make _circuit_failed and _interface_failed columns.
        If one or both of the two interfaces is failed=True, then the _circuit_failed and _interface_failed
        columns will read True; otherwise they will be False
        """

        ckt_ids = self.validated_circuit_ids()

        # Add a new column _circuit_failed to interfaces_dataframe with dtype bool
        self.interfaces_dataframe['_circuit_failed'] = None
        self.interfaces_dataframe['_circuit_failed'].astype(bool)

        # Add a new column _interface_failed to interfaces_dataframe with dtype bool
        self.interfaces_dataframe['_interface_failed'] = None
        self.interfaces_dataframe['_interface_failed'].astype(bool)

        for ckt_id in ckt_ids:  # TODO - is there a way to avoid doing a python iteration?
            ckt_ints = self.interfaces_dataframe[self.interfaces_dataframe['circuit_id'] == ckt_id]

            # Check to see if either of the two interfaces if failed = True
            # circuit_ids = self.interfaces_dataframe['circuit_id'].to_list()
            circuit_status = ckt_ints['failed'].unique().tolist()
            if True in circuit_status:
                self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id,
                                              ['_circuit_failed']] = True
                self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id,
                                              ['_interface_failed']] = True
            elif circuit_status == [False]:
                self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id,
                                              ['_circuit_failed']] = False
                self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id,
                                              ['_interface_failed']] = False
            else:
                # Raise exception for non-boolean in 'failed' column
                raise ModelException("Unexpected value in 'failed' column: {}".format(circuit_status))