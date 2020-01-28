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
        for hop_number in range(max_hop):
            print("hop_number is {}".format(hop_number))
            hop = path[hop_number]
            print("hop is {}".format(hop))

            if len(hop) == 1:
                # There is only one Interface in the hop list; use that interface
                # Add that single interface to hop hop_number in each sub_path in sub_path_list
                for sub_path_number in range(len(sub_path_list)):
                    sub_path_list[sub_path_number].append(hop)
            elif len(hop) > 1:
                # Examine interface cost
                min_cost = min([interface.cost for interface in hop])
                hop = [interface for interface in hop if interface.cost == min_cost]
                if len(hop) == 1:
                    # There is only one Interface in the hop list; use that interface
                    # Add that single interface to hop hop_number in each sub_path in sub_path_list
                    for sub_path_number in range(len(sub_path_list)):
                        sub_path_list[sub_path_number].append(hop[0])
                else:
                    # If there is more that one single interface with the min metric, add
                    # those interfaces as hops at position hop_number in len(sub_path_list)/len(hop)
                    num_sub_paths_with_each_interface_in_hop = int(len(sub_path_list)/len(hop))

                    # Each interface will be in len(sub_path_list)/len(hop[hop_number]) sub-paths at hop[hop_number]
                    num_interface_appearances = len(hop)

                    for sub_path_num in range(num_sub_paths_with_each_interface_in_hop):
                        for interface_appearance in range(num_interface_appearances):
                            print("sub_path_list is {}".format(sub_path_list))
                            sub_path_list[sub_path_num].append(hop[interface_appearance])

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
    print("************** path {} *************".format(path))
    interfaces_in_each_hop = [len(hop) for hop in path]
    max_sub_paths = numpy.prod(interfaces_in_each_hop)

    # This is a list of all the created sub-paths
    sub_path_list = []
    for sub_path_number in range(max_sub_paths):
        sub_path_list.append([])

    # This is the max length of any possible sub-path
    max_hops = len(path)

    # EXAMPLE
    # [[Interface(name='A-to-B_2', cost=20, capacity=150, node_object=Node('A'), remote_node_object=Node('B'),
    #             address='2'),
    #   Interface(name='A-to-B', cost=20, capacity=125, node_object=Node('A'), remote_node_object=Node('B'),
    #             address='1')],

    # for hop in path:
    #     for hop_interface in hop:
    #         if hop.index(hop_interface)%max_sub_paths == 0:
    #             sub_path_list.index()



    for hop in path:
        for hop_interface in hop:  # 0, 1, 2
            hop_interface_index = hop.index(hop_interface)

            for sub_path_num in range(len(sub_path_list)):


                # pprint("sub_path = ")
                # pprint(sub_path_list[sub_path_number])

                # TODO - this is the messed up part - finds the first sub path that matches!  not what we want
                #sub_path_index = sub_path_list.index(sub_path)  # 0, 1, 2, 3, 4, 5
                # print("({} + {}) % {} = {}".format(hop_interface_index, sub_path_index, len(hop),
                #                                    ((hop_interface_index + sub_path_index) % len(hop))))





                print()
                print("hop_interface_index is {}; sub_path_num is {}".format(hop_interface_index, sub_path_num))
                print("({} + {}) % {} = {}".format(hop_interface_index, sub_path_num, len(hop),
                                                   (hop_interface_index + sub_path_num) % len(hop)))

                if (hop_interface_index + sub_path_num) % len(hop) == 0:
                    # print("hop_interface_index = {}, sub_path_index = {}".format(hop_interface_index, sub_path_index))
                    # print("hop = {}".format(hop))
                    # print("hop_interface = {}".format(hop_interface))
                    # print("sub_path = {}".format(sub_path))
                    # 0, 0
                    # 1, 2, 3     1, 2, 3, 4, 5, 6

                    print("hit {}".format(hop_interface))
                    sub_path_list[sub_path_num].append(hop_interface)
                    pprint(sub_path_list[sub_path_num])

                    # print("appending {} to {}".format(hop_interface, sub_path_list[sub_path_number]))
                    # sub_path_list[sub_path_number].append(hop_interface)
                    # print()
                    # print()

    normalized_paths.append(sub_path_list)







