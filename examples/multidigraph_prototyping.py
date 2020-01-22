import sys
sys.path.append('../')
import numpy

from pprint import pprint

from pyNTM import Parallel_Link_Model


def normalize_multiple_links(path_info):

    # This will be a list of path info that has
    normalized_paths = []

    for path in path_info['path']:

        # Each path may expand out into multiple paths if the path
        # has multiple interfaces listed at each hop.
        # Find the max amount of possible sub-paths
        interfaces_in_each_hop = [len(hop) for hop in path]
        max_sub_paths = numpy.prod(interfaces_in_each_hop)

        # This is a list of all the created sub-paths
        sub_path_list = []
        for x in range(max_sub_paths):
            sub_path_list.append([])

        # This is the max length of any possible sub-path
        max_hop = len(path)

        # Each 'hop' is a list of Interfaces from one adjacent node to the
        # next; there may be multiple Interfaces in that list
        for i in range(max_hop):
            print("i is {}".format(i))
            hop = path[i]
            print("hop is {}".format(hop))


            if len(hop) == 1:
                # There is only one Interface in the hop list; use that interface
                # Add that single interface to hop i in each sub_path in sub_path_list
                for j in range(len(sub_path_list)):
                    sub_path_list[j].append(hop)
            elif len(hop) > 1:
                # Examine interface cost
                min_cost = min([interface.cost for interface in hop])
                hop = [interface for interface in hop if interface.cost == min_cost]
                if len(hop) == 1:
                    # There is only one Interface in the hop list; use that interface
                    # Add that single interface to hop i in each sub_path in sub_path_list
                    for j in range(len(sub_path_list)):
                        sub_path_list[j].append(hop[0])
                else:
                    # If there is more that one single interface with the min metric, add
                    # those interfaces as hops at position i in len(sub_path_list)/len(hop)
                    num_sub_paths_with_each_interface_in_hop = int(len(sub_path_list)/len(hop))

                    # Each interface will be in len(sub_path_list)/len(hop[i]) sub-paths at hop[i]
                    num_interface_appearances = len(hop)

                    for sub_path_num in range(num_sub_paths_with_each_interface_in_hop):
                        for interface_appearance in range(num_interface_appearances):
                            print("sub_path_list is {}".format(sub_path_list))
                            sub_path_list[sub_path_num][i].append(hop[interface_appearance])

        normalized_paths.append(sub_path_list)

    return normalized_paths


model = Parallel_Link_Model.load_model_file_multidigraph('model_test_topology_multidigraph.csv')
model.validate_model()

a_d = model.get_shortest_path('A', 'D')

pprint(a_d)

# test = normalize_multiple_links(a_d)

##################### def prototyping #####################

# This will be a list of path info that has
normalized_paths = []

for path in a_d['path']:

    # Each path may expand out into multiple paths if the path
    # has multiple interfaces listed at each hop.
    # Find the max amount of possible sub-paths
    interfaces_in_each_hop = [len(hop) for hop in path]
    max_sub_paths = numpy.prod(interfaces_in_each_hop)

    # This is a list of all the created sub-paths
    sub_path_list = []
    for x in range(max_sub_paths):
        sub_path_list.append([])

    # This is the max length of any possible sub-path
    max_hop = len(path)

    # Each 'hop' is a list of Interfaces from one adjacent node to the
    # next; there may be multiple Interfaces in that list
    for i in range(max_hop):
        print("i is {}".format(i))
        hop = path[i]
        print("hop is {}".format(hop))

        if len(hop) == 1:
            # There is only one Interface in the hop list; use that interface
            # Add that single interface to hop i in each sub_path in sub_path_list
            for j in range(len(sub_path_list)):
                sub_path_list[j].append(hop)
        elif len(hop) > 1:
            # Examine interface cost
            min_cost = min([interface.cost for interface in hop])
            hop = [interface for interface in hop if interface.cost == min_cost]
            if len(hop) == 1:
                # There is only one Interface in the hop list; use that interface
                # Add that single interface to hop i in each sub_path in sub_path_list
                for j in range(len(sub_path_list)):
                    sub_path_list[j].append(hop[0])
            else:
                # If there is more that one single interface with the min metric, add
                # those interfaces as hops at position i in len(sub_path_list)/len(hop)
                num_sub_paths_with_each_interface_in_hop = int(len(sub_path_list) / len(hop))

                # Each interface will be in len(sub_path_list)/len(hop[i]) sub-paths at hop[i]
                num_interface_appearances = len(hop)

                for sub_path_num in range(num_sub_paths_with_each_interface_in_hop):
                    for interface_appearance in range(num_interface_appearances):
                        print("sub_path_list is {}".format(sub_path_list))
                        sub_path_list[sub_path_num][i].append(hop[interface_appearance])

    normalized_paths.append(sub_path_list)



