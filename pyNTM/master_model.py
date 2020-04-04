"""
This will be the common defs used by both model.py and parallel_link_model.py
TODO - move defs to here
Common defs - use parallel_link_model versions

__repr__
_make_int_info_dict
_validate_circuit_interface_capacity
_reserved_bw_error_checks
_demand_traffic_per_int
_update_interface_utilization
_route_demands
_route_lsps
_optimize_parallel_lsp_group_res_bw
parallel_lsp_groups
parallel_demand_groups
update_simulation
_unique_interface_per_node
all_interface_circuit_ids


add_circuit - use parallel_link_model version
add_demand - use parallel_link_model version
get_all_paths_reservable_bw
_add_lsp_from_data
_add_demand_from_data
"""

class MasterModel(object):
    """
    An object to hold common defs for all MasterModel subclasses
    """

    def __init__(self, interface_objects=set(), node_objects=set(),
                 demand_objects=set(), rsvp_lsp_objects=set()):
        self.interface_objects = interface_objects
        self.node_objects = node_objects
        self.demand_objects = demand_objects
        self.circuit_objects = set()
        self.rsvp_lsp_objects = rsvp_lsp_objects
        self.srlg_objects = set()
        self._parallel_lsp_groups = {}

    def simulation_diagnostics(self):
        """
        Returns status on demands and RSVP LSPs in the simulation

        :return: dict with the following keys; the values are returned as
        generators which contain the objects

        model_diagnostic_info['Demands on LSPs']
        model_diagnostic_info['Routed LSPs with no demands']
        model_diagnostic_info['Routed LSPs with demands']s
        model_diagnostic_info['Unrouted LSPs']
        model_diagnostic_info['Unrouted Demands']

        """
        lsps_routed_no_demands = (lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                  lsp.demands_on_lsp(self) == [])

        lsps_routed_with_demands = (lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                    lsp.demands_on_lsp(self) != [])

        print("There are {} LSPs that are routed but have no demands".format(len(lsps_routed_no_demands)))
        print("There are {} LSPs that are routed and carry demands".format(len(lsps_routed_with_demands)))

        # Find the source/dest nodes for each LSP
        lsp_source_dest_pairs = (set([(lsp.source_node_object.name,
                                      lsp.dest_node_object.name) for lsp in self.rsvp_lsp_objects]))

        # Find the source/dest nodes for each demand
        dmd_source_dest_pairs = (set([(dmd.source_node_object.name,
                                      dmd.dest_node_object.name) for dmd in self.demand_objects]))

        dmds_paired_with_lsps = []
        for dmd_info in dmd_source_dest_pairs:
            for lsp_info in lsp_source_dest_pairs:
                if dmd_info == lsp_info:
                    dmds_paired_with_lsps.append(dmd_info)

        dmds_paired_with_lsps = (set(dmds_paired_with_lsps))

        print("{} of the demands ride LSPs".format(len(dmds_paired_with_lsps)))

        unrouted_lsps = [lsp for lsp in self.rsvp_lsp_objects if lsp.path == 'Unrouted']

        print("There are {} unrouted LSPs".format(len(unrouted_lsps)))

        unrouted_demands = self.get_unrouted_demand_objects()
        print("There are {} unrouted demands".format(len(unrouted_demands)))

        model_diagnostic_info = {}

        model_diagnostic_info['Demands on LSPs'] = dmds_paired_with_lsps
        model_diagnostic_info['Routed LSPs with no demands'] = lsps_routed_no_demands
        model_diagnostic_info['Routed LSPs with demands'] = lsps_routed_with_demands
        model_diagnostic_info['Unrouted LSPs'] = unrouted_lsps
        model_diagnostic_info['Unrouted Demands'] = unrouted_demands

        return model_diagnostic_info
