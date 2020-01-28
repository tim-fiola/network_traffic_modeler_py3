import sys
sys.path.append('../')
import numpy

from pprint import pprint

from pyNTM import Parallel_Link_Model

def normalize_multidigraph_paths(multidigraph_path_info):

    # This will be a list of path info that has
    normalized_paths = []
    for path in multidigraph_path_info['path']:
        # print("************** path {} *************".format(path))
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
            for hop_interface in hop:
                hop_interface_index = hop.index(hop_interface)

                for sub_path_num in range(len(sub_path_list)):

                    # pprint("sub_path = ")
                    # pprint(sub_path_list[sub_path_number])

                    # print()
                    # print("hop_interface_index is {}; sub_path_num is {}".format(hop_interface_index, sub_path_num))
                    # print("({} + {}) % {} = {}".format(hop_interface_index, sub_path_num, len(hop),
                    #                                    (hop_interface_index + sub_path_num) % len(hop)))

                    if (hop_interface_index + sub_path_num) % len(hop) == 0:
                        # print("hit {}".format(hop_interface))
                        sub_path_list[sub_path_num].append(hop_interface)
                        # pprint(sub_path_list[sub_path_num])

        normalized_paths.append(sub_path_list)

    return normalized_paths

model = Parallel_Link_Model.load_model_file_multidigraph('model_test_topology_multidigraph.csv')
model.validate_model()

a_d = model.get_shortest_path('A', 'D')

pprint(a_d)

# test = normalize_multiple_links(a_d)

##################### def prototyping #####################

normalized_paths = normalize_multidigraph_paths(a_d)

for path in normalized_paths:
    print(len(path))
    pprint(path)
    print()






