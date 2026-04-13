Visualization
=============

pyNTM includes an interactive network visualization that opens in the browser.
After running a simulation, call ``visualize()`` on the model object to launch it.

Quick Start
-----------

::

    from pyNTM import Model

    model = Model.load_model_file('network.csv')
    model.update_simulation()

    model.visualize()                    # opens in default browser
    model.visualize('output.html')       # saves to a specific file

The ``visualize()`` method generates a self-contained HTML file with no server
or additional dependencies required.

Features
--------

* **Draggable nodes** - click and drag any node to rearrange the topology for better visibility
* **Per-direction utilization coloring** - each interface direction is independently color-coded by utilization
* **Toggleable utilization legend** - click a utilization range in the legend to hide/show interfaces at that level
* **Demand path tracing** - select a demand to highlight its path; see its traffic, LSPs it rides, and interfaces it transits
* **RSVP LSP path tracing** - select an LSP to see its traffic, reserved bandwidth, demands it carries, and path interfaces
* **Interface inspection by node** - select a node to list all its interfaces with utilization, demands, and LSPs
* **Cross-linked navigation** - click any demand, LSP, or interface in any panel to make it the active selection
* **Tooltips** - hover over edges and nodes for interface name, endpoints, capacity, and utilization
* **Controls** - toggle physics simulation, show/hide edge arrows, fit to screen, reset node positions

Utilization Color Ranges
------------------------

The default utilization color ranges are:

===========  ============
Range        Color
===========  ============
0-24%        Royal Blue
25-49%       Forest Green
50-74%       Gold
75-89%       Orange Red
90-99%       Dark Red
100%+        Dark Violet
Failed       Grey (dashed)
===========  ============

These can be customized via the ``InteractiveVisualization`` class if needed::

    from pyNTM.interactive_visualization import InteractiveVisualization

    vis = InteractiveVisualization(model)
    vis.util_ranges = [
        (50, "#0000FF", "0-49%"),
        (100, "#FF0000", "50-99%"),
        (None, "#800080", "100%+"),
    ]
    vis.create_visualization('custom.html')

Deprecated: WeatherMap
----------------------

The legacy ``WeatherMap`` class (``pyNTM.weathermap``) using Dash and
dash-cytoscape is deprecated.  Use ``model.visualize()`` instead.
