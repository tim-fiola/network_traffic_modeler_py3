
## Focus on items where uniqueness is important (interfaces _key, node_name, lsp _key, demand, look at the model for uniqueness checks)

#  Add Circuit (2 interfaces)
def add_circuit(node1_name, node2_name, interface1_name, interface2_name, cost1, cost2, capacity, circuit_id,
                rsvp_enabled1=False, rsvp_enabled2=False, percent_reservable_bandwidth1=0, percent_reservable_bandwidth2=0, failed=False):
    """
    Adds a circuit between node1 and node2
    Args:
        node1_name: - required - string - name of node1
        node2_name: - required - string - name of node2
        interface1_name:  - required - string - name of interface1, which resides on node1
        interface2_name:  - required - string - name of interface2, which resides on node2
        cost1:  - required - float - IGP cost of interface1
        cost2:  - required - float - IGP cost of interface2
        capacity:  - required - float - capacity for circuit
        circuit_id:  - required - string - circuit ID - unique circuit identifier that each component interface
        will share
        rsvp_enabled1: - bool - is RSVP enabled on interface1
        rsvp_enabled2: - bool - is RSVP enabled on interface2
        percent_reservable_bandwidth1: - float - percentage of interface1 capacity that is configured to be available
        for RSVP reservations
        percent_reservable_bandwidth2: - float - percentage of interface1 capacity that is configured to be available
        for RSVP reservations
        failed: - bool - is circuit failed?

    Returns: model.interfaces_dataframe that has interface1 and interface2 with a common circuit_id

    """

    # TODO - try this with d = {'arg1': 'one', 'arg2': 'two', 'arg3': 'three'}
    #  then
    #  func(**d)
    #  # arg1 = one
    #  # arg2 = two
    #  # arg3 = three

    line_data1 = {
        'node_name': node1_name,
        'remote_node_name': node2_name,
        'name': interface1_name,
        'cost': interface2_name,
        'capacity': capacity,
        'circuit_id': circuit_id,
        'rsvp_enabled': rsvp_enabled1,
        'percent_reservable_bandwidth': percent_reservable_bandwidth1,
    }

    line_data2 = {
        'node_name': node2_name,
        'remote_node_name': node1_name,
        'name': interface2_name,
        'cost': interface1_name,
        'capacity': capacity,
        'circuit_id': circuit_id,
        'rsvp_enabled': rsvp_enabled2,
        'percent_reservable_bandwidth': percent_reservable_bandwidth2,
    }



# Delete Circuit



# Add LSP


# Remove Circuit


# Remove LSP


# Add demand


# Delete demand






