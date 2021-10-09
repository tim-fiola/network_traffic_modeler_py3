Visualization
=============

PyNTM has a visualization feature that produces an interactive visualization of the network.

More info on the visualization and how to use it can be found in the pyNTM training repository `visualization training module <https://github.com/tim-fiola/TRAINING---network_traffic_modeler_py3-pyNTM-/blob/master/pyNTM_visualization_training.pdf>`_.

Visualization Demo Script
-------------------------

The ``examples/vis_training.py`` example script showcases the visualization module, which is current beta feature.

To run this script, install the packages in ``requirements_visualization.txt`` file::

    (venv) % pip3 install -r requirements_visualization.txt

Once you've installed the requirements, run the script.

You will see some simulation activities and info and then a visualization::

    (venv) % python3 -i vis_training.py
    Routing the LSPs . . .
    Routing 1 LSPs in parallel LSP group C-E; 1/3
    Routing 1 LSPs in parallel LSP group D-F; 2/3
    Routing 2 LSPs in parallel LSP group B-D; 3/3
    LSPs routed (if present) in 0:00:00.001134; routing demands now . . .
    Demands routed in 0:00:00.003497; validating model . . .
    shortest path from A to F is:
    {'cost': 50,
     'path': [[Interface(name = 'A-G', cost = 25, capacity = 100, node_object = Node('A'), remote_node_object = Node('G'), circuit_id = '6'),
               Interface(name = 'G-F', cost = 25, capacity = 100, node_object = Node('G'), remote_node_object = Node('F'), circuit_id = '7')],
              [Interface(name = 'A-G', cost = 25, capacity = 100, node_object = Node('A'), remote_node_object = Node('G'), circuit_id = '6'),
               Interface(name = 'G-F_2', cost = 25, capacity = 100, node_object = Node('G'), remote_node_object = Node('F'), circuit_id = '8')],
              [Interface(name = 'A-B', cost = 10, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1'),
               Interface(name = 'B-C', cost = 10, capacity = 100, node_object = Node('B'), remote_node_object = Node('C'), circuit_id = '2'),
               Interface(name = 'C-D', cost = 10, capacity = 100, node_object = Node('C'), remote_node_object = Node('D'), circuit_id = '3'),
               Interface(name = 'D-E', cost = 10, capacity = 100, node_object = Node('D'), remote_node_object = Node('E'), circuit_id = '4'),
               Interface(name = 'E-F', cost = 10, capacity = 100, node_object = Node('E'), remote_node_object = Node('F'), circuit_id = '5')],
              [Interface(name = 'A-B', cost = 10, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1'),
               Interface(name = 'B-C_2', cost = 10, capacity = 100, node_object = Node('B'), remote_node_object = Node('C'), circuit_id = '9'),
               Interface(name = 'C-D', cost = 10, capacity = 100, node_object = Node('C'), remote_node_object = Node('D'), circuit_id = '3'),
               Interface(name = 'D-E', cost = 10, capacity = 100, node_object = Node('D'), remote_node_object = Node('E'), circuit_id = '4'),
               Interface(name = 'E-F', cost = 10, capacity = 100, node_object = Node('E'), remote_node_object = Node('F'), circuit_id = '5')]]}

    dmd_a_f_1 path is:
    [[Interface(name = 'A-G', cost = 25, capacity = 100, node_object = Node('A'), remote_node_object = Node('G'), circuit_id = '6'),
      Interface(name = 'G-F', cost = 25, capacity = 100, node_object = Node('G'), remote_node_object = Node('F'), circuit_id = '7')],
     [Interface(name = 'A-G', cost = 25, capacity = 100, node_object = Node('A'), remote_node_object = Node('G'), circuit_id = '6'),
      Interface(name = 'G-F_2', cost = 25, capacity = 100, node_object = Node('G'), remote_node_object = Node('F'), circuit_id = '8')],
     [Interface(name = 'A-B', cost = 10, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1'),
      RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_1'),
      RSVP_LSP(source = D, dest = F, lsp_name = 'lsp_d_f_1')],
     [Interface(name = 'A-B', cost = 10, capacity = 100, node_object = Node('A'), remote_node_object = Node('B'), circuit_id = '1'),
      RSVP_LSP(source = B, dest = D, lsp_name = 'lsp_b_d_2'),
      RSVP_LSP(source = D, dest = F, lsp_name = 'lsp_d_f_1')]]

    *** NOTE: The make_visualization_beta function is a beta feature.  It may not have been as
    extensively tested as the pyNTM code in general.  The API calls for this may also
    change more rapidly than the general pyNTM code base.



    Visualization is available at http://127.0.0.1:8050/


    Dash is running on http://127.0.0.1:8050/

     * Serving Flask app 'pyNTM.weathermap' (lazy loading)
     * Environment: production
       WARNING: This is a development server. Do not use it in a production deployment.
       Use a production WSGI server instead.
     * Debug mode: off
     * Running on http://127.0.0.1:8050/ (Press CTRL+C to quit)
    127.0.0.1 - - [26/Sep/2021 18:18:19] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "GET /_dash-layout HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "GET /_dash-dependencies HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "GET /_favicon.ico?v=2.0.0 HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "GET /_dash-component-suites/dash/dcc/async-dropdown.js HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "POST /_dash-update-component HTTP/1.1" 200 -
    127.0.0.1 - - [26/Sep/2021 18:18:20] "POST /_dash-update-component HTTP/1.1" 200 -

If you open your browser to http://127.0.0.1:8050/, you will see an interactive visualization.

