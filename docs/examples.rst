Examples
=========

Demo/Example scripts
--------------------

These scripts are in the ``examples`` directory and are meant to showcase different capabilities and how to use them.

The ``lsp_practice_code.py`` script demos how auto-bandwidth RSVP LSPs react to

* link failures
* adding traffic
* adding additional LSPs

The ``network_modeling_client_code_examples_read_from_dict.py`` file demos the following:

* loading a network topology from a list of info (instead of a model file)
* addition of new circuit and node to the network
* viewing interface traffic
* getting the shortest path
* failing an interface
* demand path changes before/after a link failure
* adding traffic

Interactive Visualization Example
----------------------------------

The ``interactive_visualization_example.py`` script demonstrates the interactive
visualization feature.  It loads a model, runs the simulation, and opens a
browser-based visualization::

    from pyNTM import Model

    model = Model.load_model_file('sample_network_model_file.csv')
    model.update_simulation()
    model.visualize()

You can also call ``model.visualize('output.html')`` to save to a specific file.

See the `visualization <visualization.rst>`_ docs page for full details on visualization features.
