RSVP LSP
=========

A class to represent an RSVP label-switched-path in the network model

    **source_node_object**: Node where LSP ingresses the network (LSP starts here)

    **dest_node_object**: Node where LSP egresses the network (LSP ends here)

    **lsp_name**: name of LSP

    **path**::

        will either be 'Unrouted' or be a dict containing the following -
        - interfaces: list of interfaces that LSP egresses in the order it
            egresses them
        - path_cost: sum of costs of the interfaces
        - baseline_path_reservable_bw: the amount of reservable bandwidth
            available on the LSP's path when the LSP was signaled, not inclusive
            of the bandwidth already reserved by this LSP on that path (if any)

    **reserved_bandwidth**: amount of bandwidth reserved by this LSP

    **setup_bandwidth**: amount of bandwidth this LSP attempts to signal for when it sets up

    **manual_metric**: manual metric for LSP.
    If set, this value will override the default (shortest path) metric for effective_metric.
    This value must be a positive integer.
    To restore the LSP's default metric (that of the shortest IGP path) in a live simulation,
    set this value to -1.

For more information on the capabilities of RSVP LSPs, see the `RSVP LSP docstrings`_.

.. _RSVP LSP docstrings: ./api.html#rsvp-lsp

