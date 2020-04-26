import sys
sys.path.append('../')

import networkx as nx
import random

from pyNTM import Node
from pyNTM import Demand
from pyNTM import Parallel_Link_Model
from pyNTM import Interface
from pyNTM import RSVP_LSP


def _route_lsps(model, input_model):
    """Route the LSPs in the model
    1.  Get LSPs into groups with matching source/dest
    2.  Find all the demands that take the LSP group
    3.  Route the LSP group, one at a time
    :param input_model: Model object; this may have different parameters than 'self'
    :return: self, with updated LSP paths
    """

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

        res_bw_per_lsp = traff_on_each_group_lsp / num_lsps_in_group

        # # Now route each LSP in the group (first routing iteration)
        # for lsp in lsps:  # TODO - can this be optimized?
        #     # Route each LSP one at a time
        #     lsp.route_lsp(input_model, traff_on_each_group_lsp)


    #########################
        # Start with a new network graph with all RSVP enabled interfaces
        # G = model._make_weighted_network_graph_mdg(include_failed_circuits=False, rsvp_required=True)

        for lsp in lsps:
            lsp.path = {}

            G = model._make_weighted_network_graph_mdg(include_failed_circuits=False, rsvp_required=True,
                                                       needed_bw=res_bw_per_lsp)

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

            candidate_path_info = model._normalize_multidigraph_paths(all_paths)

            import pdb
            pdb.set_trace()

            # If multiple lowest_metric_paths, find those with fewest hops
            if len(candidate_path_info) > 1:
                fewest_hops = min([len(path['interfaces']) for path in candidate_path_info])
                lowest_hop_count_paths = [path for path in candidate_path_info if len(path['interfaces']) == fewest_hops]
                if len(lowest_hop_count_paths) > 1:
                    new_path = random.choice(lowest_hop_count_paths)
                else:
                    new_path = lowest_hop_count_paths[0]
            else:
                new_path = candidate_path_info[0]

            lsp.path = new_path



    ########################
        routed_lsps_in_group = [lsp for lsp in lsps if lsp.path != 'Unrouted']

        # ##### Optimize the LSP group reserved bandwidth #####
        # If not all the LSPs in the group can route at the lowest (initial)
        # setup bandwidth, determine which LSPs can signal and for how much traffic
        if len(routed_lsps_in_group) != len(lsps) and len(routed_lsps_in_group) > 0:
            model._optimize_parallel_lsp_group_res_bw(input_model, routed_lsps_in_group, traffic_in_demand_group)

        counter += 1

    return model


def _find_path_cost_and_headroom(lsp, candidate_paths):
    """
    Returns a list of dictionaries containing the path interfaces as
    well as the path cost and headroom available on the path.
    :param candidate_paths: list of lists of Interface objects
    :return: list of dictionaries of paths: {'interfaces': path,
                                             'path_cost': path_cost,
                                             'baseline_path_reservable_bw': baseline_path_reservable_bw}
    """

    # List to hold info on each candidate path
    candidate_path_info = []

    # Find the path cost and path headroom for each path candidate
    for path in candidate_paths['path']:
        path_cost = 0
        for interface in path:
            path_cost += interface.cost

        # baseline_path_reservable_bw is the max amount of traffic that the path
        # can handle without saturating a component interface
        baseline_path_reservable_bw = min([interface.reservable_bandwidth for interface in path])

        path_info = {'interfaces': path, 'path_cost': path_cost,
                     'baseline_path_reservable_bw': baseline_path_reservable_bw}

        candidate_path_info.append(path_info)

    return candidate_path_info


node_a = Node(name='nodeA', lat=0, lon=0)
node_b = Node(name='nodeB', lat=0, lon=0)
node_d = Node(name='nodeD')
interface_a = Interface(name='interfaceA-to-B', cost=4, capacity=100,
                        node_object=node_a, remote_node_object=node_b, circuit_id=1)
interface_b = Interface(name='interfaceB-to-A', cost=4, capacity=100,
                        node_object=node_b, remote_node_object=node_a, circuit_id=1)
dmd_a_b = Demand(node_a, node_b, traffic=10)

lsp_a_b_1 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_1')
lsp_a_b_2 = RSVP_LSP(source_node_object=node_a, dest_node_object=node_b, lsp_name='lsp_a_b_2')

model = Parallel_Link_Model(interface_objects=set([interface_a, interface_b]),
              node_objects=set([node_a, node_b, node_d]), demand_objects=set([dmd_a_b]),
              rsvp_lsp_objects=set([lsp_a_b_1, lsp_a_b_2]))

model.update_simulation()




# model.update_simulation()
#
# for lsp in model.rsvp_lsp_objects:
#     print(lsp.traffic_on_lsp(model))
