from .exceptions import ModelException
from .utilities import find_end_index

from collections import Counter

from dataclasses import dataclass
from dataclasses import Field

import uuid
import pandas as pd

import networkx as nx

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
        return ["node_name", "node_uuid", "lon", "lat", "igp_shortcuts_enabled", "failed"]

    @staticmethod
    def nodes_dataframe_dtypes(self):
        return {"node_name": "string",
                "node_uuid": "string",
                "lon": "float64",
                "lat": "float64",
                "igp_shortcuts_enabled": "bool",
                "failed": "bool"}

    @staticmethod
    def lsp_column_names():
        return ['source', 'dest', 'name', '_key', 'configured_setup_bw', 'manual_metric']

    @staticmethod
    def demand_column_names():
        return ['source', 'dest', 'traffic', 'name', '_key']

    @staticmethod
    def interface_dataframe_column_names():
        return ["node_name", "remote_node_name", "interface_name", "cost", "capacity", "circuit_id",
                "rsvp_enabled_bool", "percent_reservable_bandwidth", "interface_uuid", "_key",
                "failed", "_percent_reserved_bandwidth"]


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
        demands_dataframe = cls._add_demands_from_data(demands_lines)

        # Populate lsps_dataframe (if LSPs are present)
        try:
            lsp_info_begin_index = lines.index("RSVP_LSP_TABLE") + 2
            lsp_lines = lines[lsp_info_begin_index:]
            lsps_dataframe = cls._add_lsps_from_data(lsp_lines, nodes_dataframe)
        except ValueError:
            print("RSVP_LSP_TABLE not in file; no LSPs added to model")
            lsps_dataframe = pd.DataFrame
        except ModelException as e:
            err_msg = e.args[0]
            raise ModelException(err_msg)

        # Specify data types in each column for nodes_dataframe
        nodes_dataframe = nodes_dataframe.astype(dtype=cls.nodes_dataframe_dtypes(cls))

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

            # Define a unique key for each LSP (source__dest__name)
            _key = lsp_info[0]+"__"+lsp_info[1]+"__"+lsp_info[2]
            lsp_entry = [lsp_info[0], lsp_info[1], lsp_info[2], _key,configured_setup_bw, manual_metric]
            lsps_list.append(lsp_entry)

        lsps_dataframe = pd.DataFrame(lsps_list, columns=cls.lsp_column_names())

        # Check for LSP _key uniqueness
        cls.uniqueness_check(lsps_dataframe, '_key', 'LSP')

        return lsps_dataframe

    @classmethod
    def uniqueness_check(cls, dataframe, column_name_to_check_for_duplicates, item_type_in_column):
        duplicate_item_check = dataframe[column_name_to_check_for_duplicates].duplicated()
        duplicate_indices = duplicate_item_check.index[duplicate_item_check == True]
        if len(duplicate_indices) != 0:
            # Query datafrome for duplicate items
            duplicate_item_list = []
            for index in duplicate_indices:
                duplicate_item_list.append(dataframe._get_value(index, column_name_to_check_for_duplicates))
            except_msg = "Duplicate {} {} found {}; check input data "\
                .format(item_type_in_column, column_name_to_check_for_duplicates, duplicate_item_list)
            raise ModelException(except_msg)

    @classmethod
    def _add_demands_from_data(
            cls, demands_lines
    ):
        demands_list = []
        for demand in demands_lines:
            dmd = demand.split(',')
            dmd.append(dmd[0]+'__'+dmd[1]+'__'+dmd[3])
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
        nodes_dataframe = nodes_dataframe.astype(dtype=cls.nodes_dataframe_dtypes(cls))

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
            _key = node_name+'__'+name
            line_data.append(_key)
            line_data.append(False)  # Failed state defaults to false
            line_data.append(0)  # Percent reserved bandwidth is computed during convergence
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
        node_list = [[node, uuid.uuid4(), None, None, None, False ] for node in node_list]

        # Create the Node and Interface dataframes
        nodes_dataframe = pd.DataFrame(node_list, columns=cls.nodes_dataframe_column_names())
        # Check for duplicates in nodes_dataframe
        cls.uniqueness_check(nodes_dataframe, 'node_name', 'node')

        interface_dataframe_columns = ["node_name", "remote_node_name", "interface_name", "cost", "capacity", "circuit_id",
                                   "rsvp_enabled_bool", "percent_reservable_bandwidth", "interface_uuid", "_key",
                                   "failed", "_percent_reserved_bandwidth"]
        interfaces_dataframe = pd.DataFrame(interface_list, columns=cls.interface_dataframe_column_names())
        # Check for uniqueness in interfaces_dataframe
        cls.uniqueness_check(interfaces_dataframe, '_key', 'interface')

        return interfaces_dataframe, nodes_dataframe

    def _make_weighted_network_graph_mdg(
        self, include_failed_circuits=True, needed_bw=0, rsvp_required=False
    ):
        """
        Returns a networkx weighted networkx multidigraph object from
        the input Model object

        :param include_failed_circuits: include interfaces from currently failed
        circuits in the graph?
        :param needed_bw: how much reservable_bandwidth is required?
        :param rsvp_required: True|False; only consider rsvp_enabled interfaces?

        :return: networkx multidigraph with edges that conform to the needed_bw and
        rsvp_required parameters
        """

        G = nx.MultiDiGraph()

        # Get all the edges that meet 'failed' and 'reservable_bw' criteria
        if include_failed_circuits is False:
            considered_interfaces = (
                interface
                for interface in self.interface_objects
                if (
                    interface.failed is False
                    and interface.reservable_bandwidth >= needed_bw
                )
            )


        elif include_failed_circuits is True:
            considered_interfaces = (
                interface
                for interface in self.interface_objects
                if interface.reservable_bandwidth >= needed_bw
            )

        if rsvp_required is True:
            edge_names = (
                (
                    interface.node_object.name,
                    interface.remote_node_object.name,
                    {
                        "cost": interface.cost,
                        "interface": interface,
                        "circuit_id": interface.circuit_id,
                    },
                )
                for interface in considered_interfaces
                if interface.rsvp_enabled is True
            )
        else:
            edge_names = (
                (
                    interface.node_object.name,
                    interface.remote_node_object.name,
                    {
                        "cost": interface.cost,
                        "interface": interface,
                        "circuit_id": interface.circuit_id,
                    },
                )
                for interface in considered_interfaces
            )

        # Add edges to networkx DiGraph
        G.add_edges_from(edge_names)

        # Add all the nodes
        node_name_iterator = (node.name for node in self.node_objects)
        G.add_nodes_from(node_name_iterator)

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
            for k,v in ckt_id_occurrences:
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
            for k,v in ckt_id_occurrences:
                if v != 2:
                    violations[k] = v
            except_msg = "The following circuit IDs appear, but not exactly two times. " \
                         "This dict has key, value = circuit_id, # of occurrences:  {}".format(violations)
            raise ModelException(except_msg)

    def validate_circuit_capacities(self):
        """
        Verify that the interface capacities that have a common circuit_id have matching capacities
        Verify that there are only 2 instances of a given circuit_id in the interfaces_dataframe
        Returns: A list of interfaces with common ciruit_id but whose capacities don't match

        """

        # Query the interfaces for a given id to make sure the capacities match
        for ckt_id in self.validated_circuit_ids():
            capacities = self.interfaces_dataframe.loc[self.interfaces_dataframe['circuit_id'] == ckt_id]['capacity']
            # Verify that there are only 2 rows
            if len(capacities != 2):
                error_msg = "The circuit_id {} has {} entries in the interfaces_dataframe; check input data".\
                    format(ckt_id, len(capacities))
                raise ModelException(error_msg)
            # Verify that the capacities match in the 2 rows with the common circuit_id
            if capacities.values[0] != capacities.values[1]:
                error_msg = "The circuit_id {} has mismatching capacity values on the interface objects".format(ckt_id)
                raise ModelException(error_msg)






    def validate_model(self):
        """
        Validates that data fed into the model creates a valid network model
        """

        # Verify that each circuit_id appears exactly twice
        circuit_ids_validated = self._circuit_ids_validated(self.interfaces_dataframe)

        # Verify circuit component interface matching capacity



# TODO - validate_model
# TODO - update_simulation (rename to converge_model)
