import sys
sys.path.append('../')

import networkx as nx
import random

from pyNTM import Node
from pyNTM import Demand
from pyNTM import PerformanceModel
from pyNTM import FlexModel
from pyNTM import Interface
from pyNTM import RSVP_LSP

from datetime import datetime

from pprint import pprint

def _route_lsps(model):
    """Route the LSPs in the model
    1.  Get LSPs into groups with matching source/dest
    2.  Find all the demands that take the LSP group
    3.  Route the LSP group, one at a time
    :param input_model: Model object; this may have different parameters than 'self'
    :return: self, with updated LSP paths
    """

    for interface in model.interface_objects:
        interface.reserved_bandwidth = 0


    # Find parallel LSP groups
    parallel_lsp_groups = model.parallel_lsp_groups()  # TODO - can this be optimized?

    # Find all the parallel demand groups
    parallel_demand_groups = model.parallel_demand_groups()  # TODO - can this be optimized?

    # Find the amount of bandwidth each LSP in each parallel group will carry
    counter = 1

    for group, lsps in parallel_lsp_groups.items():

        num_lsps_in_group = len(lsps)

        print("Routing {} LSPs in parallel LSP group {}; {}/{}".format(num_lsps_in_group, group, counter,
                                                                       len(parallel_lsp_groups)))
        # Traffic each LSP in a parallel LSP group will carry; initialize
        traffic_in_demand_group = 0
        traff_on_each_group_lsp = 0

        try:
            # Get all demands that would ride the parallel LSP group
            dmds_on_lsp_group = parallel_demand_groups[group]

            traffic_in_demand_group = sum([dmd.traffic for dmd in dmds_on_lsp_group])
            if traffic_in_demand_group > 0:
                traff_on_each_group_lsp = traffic_in_demand_group / len(lsps)
        except KeyError:
            # LSPs with no demands will cause a KeyError in parallel_demand_groups[group]
            # since parallel_demand_group will have no entry for 'group'
            pass

        # # Now route each LSP in the group (first routing iteration)
        # for lsp in lsps:  # TODO - can this be optimized?
        #     # Route each LSP one at a time
        #     lsp.route_lsp(input_model, traff_on_each_group_lsp)


    #########################
        # Start with a new network graph with all RSVP enabled interfaces
        # G = model._make_weighted_network_graph_mdg(include_failed_circuits=False, rsvp_required=True)

        for lsp in lsps:

            G = model._make_weighted_network_graph(include_failed_circuits=False, rsvp_required=True,
                                                   needed_bw=traffic_in_demand_group)

            lsp.path = {}
            lsp.reserved_bandwidth = traff_on_each_group_lsp

            # Shortest path in networkx multidigraph
            try:
                nx_sp = list(nx.all_shortest_paths(G, lsp.source_node_object.name, lsp.dest_node_object.name,
                                                   weight='cost'))
            except nx.exception.NetworkXNoPath:
                # There is no path, demand.path = 'Unrouted'
                lsp.path = 'Unrouted'
                continue

            # all_paths is list of paths from source to destination; these paths
            # may include paths that have multiple links between nodes
            all_paths = []

            for path in nx_sp:
                current_hop = path[0]
                this_path = []
                for next_hop in path[1:]:
                    this_hop = []
                    values_source_hop = G[current_hop][next_hop].values()
                    min_weight = min(d['cost'] for d in values_source_hop)
                    ecmp_links = [interface_index for interface_index, interface_item in
                                  G[current_hop][next_hop].items() if
                                  interface_item['cost'] == min_weight]

                    # Add Interface(s) to this_hop list and add traffic to Interfaces
                    for link_index in ecmp_links:
                        this_hop.append(G[current_hop][next_hop][link_index]['interface'])
                    this_path.append(this_hop)
                    current_hop = next_hop
                all_paths.append(this_path)

            candidate_path_info = model._normalize_multigraph_paths(all_paths)

            # Candidate paths with enough reservable bandwidth
            candidate_path_info_w_reservable_bw = []

            for path in candidate_path_info:
                if min([interface.reservable_bandwidth for interface in path]) >= traff_on_each_group_lsp:
                    candidate_path_info_w_reservable_bw.append(path)

            # If multiple lowest_metric_paths, find those with fewest hops
            if len(candidate_path_info_w_reservable_bw) == 0:
                lsp.path = 'Unrouted'
                continue

            elif len(candidate_path_info_w_reservable_bw) > 1:
                fewest_hops = min([len(path) for path in candidate_path_info_w_reservable_bw])
                lowest_hop_count_paths = [path for path in candidate_path_info_w_reservable_bw
                                          if len(path) == fewest_hops]
                if len(lowest_hop_count_paths) > 1:
                    new_path = random.choice(lowest_hop_count_paths)
                else:
                    new_path = lowest_hop_count_paths[0]
            else:
                new_path = candidate_path_info_w_reservable_bw[0]

            # Change LSP path into more verbose form
            path_cost = sum([interface.cost for interface in new_path])
            baseline_path_reservable_bw = min([interface.reservable_bandwidth for interface in new_path])
            lsp.path = {'interfaces': new_path,
                        'path_cost': path_cost,
                        'baseline_path_reservable_bw': baseline_path_reservable_bw}

            for interface in [interface for interface in lsp.path['interfaces'] if lsp.path != 'Unrouted']:
                interface.reserved_bandwidth += lsp.reserved_bandwidth

            # TODO - get lsp.path in normal format?
            #  {'interfaces': [Interface(name = 'interfaceA-to-B', cost = 4, capacity = 100,
            #  node_object = Node('nodeA'), remote_node_object = Node('nodeB'), circuit_id = 1)],
            #  'path_cost': 4, 'baseline_path_reservable_bw': 100.0}

    ########################
        routed_lsps_in_group = [lsp for lsp in lsps if lsp.path != 'Unrouted']

        # ##### Optimize the LSP group reserved bandwidth #####
        # If not all the LSPs in the group can route at the lowest (initial)
        # setup bandwidth, determine which LSPs can signal and for how much traffic
        if len(routed_lsps_in_group) != len(lsps) and len(routed_lsps_in_group) > 0:
            model._optimize_parallel_lsp_group_res_bw(input_model, routed_lsps_in_group, traffic_in_demand_group)

        counter += 1

    return model

    # TODO - replace the above in model object

# node_a = Node(name='nodeA', lat=0, lon=0)
# node_b = Node(name='nodeB', lat=0, lon=0)
# node_d = Node(name='nodeD')
# interface_a = Interface(name='interfaceA-to-B', cost=4, capacity=100,
#                         node_object=node_a, remote_node_object=node_b, circuit_id=1)
# interface_b = Interface(name='interfaceB-to-A', cost=4, capacity=100,
#                         node_object=node_b, remote_node_object=node_a, circuit_id=1)
# dmd_a_b = Demand(node_a, node_b, traffic=10)
#
# lsp_a_b_1 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_1')
# lsp_a_b_2 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_2')
#
# model = Parallel_Link_Model(interface_objects=set([interface_a, interface_b]),
#               node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_b]),
#               rsvp_lsp_objects=set([lsp_a_b_1, lsp_a_b_2]))


# ## BIG MODEL LOAD ## #
# model = Parallel_Link_Model.load_model_file('big_model_multi_digraph_file.txt')
# model = Parallel_Link_Model.load_model_file('parallel_link_model_test_topology_2.csv')
# model.update_simulation()
# pre_lsp_route_time = datetime.now()
# model = _route_lsps(model)
# post_lsp_route_time = datetime.now()
#
# model = model._route_demands(model)
# post_demand_time = datetime.now()
#
# lsp_time = post_lsp_route_time - pre_lsp_route_time
# dmd_time = post_demand_time - post_lsp_route_time
# print("lsp_time = {}".format(lsp_time))
# print("dmd_time = {}".format(dmd_time))

# ## END BIG MODEL LOAD ## #

# for lsp in model.rsvp_lsp_objects:
#     pprint([lsp, lsp.reserved_bandwidth, lsp.path])


# model.update_simulation()
#
# for lsp in model.rsvp_lsp_objects:
#     print(lsp.traffic_on_lsp(model))

# model2 = Model.load_model_file('../test/model_test_topology_2.csv')
# model2.update_simulation()
#
# model3 = Model.load_model_file('../test/model_test_topology.csv')
# model3.update_simulation()
# sim_diag = model3.simulation_diagnostics()
# pprint(sim_diag)
#
# lsp_a_d_1 = model3.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
# lsp_a_d_2 = model3.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')

model = PerformanceModel.load_model_file('../test/lsp_configured_setup_bw_model.csv')
lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')
lsp_a_d_3 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_3')

model.update_simulation()

