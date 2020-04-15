"""
This will be the common defs used by both model.py and parallel_link_model.py
TODO - move defs to here; create MasterModel parent class with these defs
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
simulation_diagnostics
"""
from .rsvp import RSVP_LSP

class MasterModel(object):
    """
    Parent class for Model and Parallel_Link_Model subclasses; holds common defs
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

    def simulation_diagnostics(self):  # TODO - make unit test for this
        """
        Analyzes simulation results and looks for the following:
        - Number of routed LSPs carrying Demands
        - Number of routed LSPs with no Demands
        - Number of Demands riding LSPs
        - Number of Demands not riding LSPs
        - Number of unrouted LSPs
        - Number of unrouted Demands

        :return: dict with the above as keys and the quantity of each for values and generators for
        routed LSPs with no Demands, routed LSPs carrying Demands, Demands riding LSPs

        This is not cached currently and my be expensive to (re)run on a very large model.  Current best
        practice is to assign the output of this to a variable:

        ex: sim_diag1 = model1.simulation_diagnostics()

        """

        simulation_data = {'Number of routed LSPs carrying Demands': 'TBD',
                           'Number of routed LSPs with no Demands': 'TBD',
                           'Number of Demands riding LSPs': 'TBD',
                           'Number of Demands not riding LSPs': 'TBD',
                           'Number of unrouted LSPs': 'TBD',
                           'Number of unrouted Demands': 'TBD',
                           'routed LSPs with no demands generator': 'TBD',
                           'routed LSPs with demands generator': 'TBD',
                           'demands riding LSPs generator': 'TBD'}

        # Find LSPs with and without demands
        lsps_routed_no_demands = [lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                  lsp.demands_on_lsp(self) == []]

        lsps_routed_with_demands = [lsp for lsp in self.rsvp_lsp_objects if lsp.path != 'Unrouted' and
                                    lsp.demands_on_lsp(self) != []]

        # Find demands riding LSPs
        dmds_riding_lsps = set()

        # Find unrouted LSPs
        for dmd in (dmd for dmd in self.demand_objects):
            for object in dmd.path:
                if isinstance(object, RSVP_LSP):
                    dmds_riding_lsps.add(dmd)
        unrouted_lsps = [lsp for lsp in self.rsvp_lsp_objects if lsp.path == 'Unrouted']

        # Update the quantities in simulation_data
        simulation_data['Number of routed LSPs carrying Demands'] = len(lsps_routed_with_demands)
        simulation_data['Number of routed LSPs with no Demands'] = len(lsps_routed_no_demands)
        simulation_data['Number of Demands riding LSPs'] = len(dmds_riding_lsps)
        simulation_data['Number of Demands not riding LSPs'] = len(self.demand_objects) - len(dmds_riding_lsps)
        simulation_data['Number of unrouted LSPs'] = len(unrouted_lsps)
        simulation_data['Number of unrouted Demands'] = len(self.get_unrouted_demand_objects())

        # Create generators to be returned
        dmds_riding_lsps_gen = (dmd for dmd in dmds_riding_lsps)
        lsps_routed_no_demands_gen = (lsp for lsp in lsps_routed_no_demands)
        lsps_routed_with_demands_gen = (lsp for lsp in lsps_routed_with_demands)

        # Update generators in simulation_data
        simulation_data['routed LSPs with no demands generator'] = lsps_routed_no_demands_gen
        simulation_data['routed LSPs with demands generator'] = lsps_routed_with_demands_gen
        simulation_data['demands riding LSPs generator'] = dmds_riding_lsps_gen

        return simulation_data
