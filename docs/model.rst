The Model Object
================

What is the model object?
*************************

The model object has two main functions:

* It holds all the objects that represent the network (interfaces, nodes, demands, RSVPs, etc)
* It controls the mechanics of how each object interacts with others

A network model requires these primitive objects to create a simulation and higher-level objects:

* Interfaces
* Nodes
* Demands
* RSVP LSPs (only required if network has RSVP LSPs)

From these primitives, the model can construct higher-level objects such as:

* Circuits
* Shared Risk Link Groups (SRLGs)
* Paths for demands and LSPs
* etc

The model produces a simulation of the network behavior by applying the traffic demand objects to the network topology, routing the traffic demands across the topology as a real network would.
The model produces a simulation when its ``update_simulation()`` method is called.

The Model Class
***************

The model class is ``Model``.  It supports all pyNTM features:

* IGP routing
* Multiple Circuits (parallel links) between layer 3 Nodes
* RSVP LSPs with bandwidth reservation, auto-bandwidth, and manual metrics
* RSVP LSP IGP shortcuts, whereby LSPs can carry traffic demands downstream, even if the demand does not have matching source and destination as the LSP
* SRLG (Shared Risk Link Group) support
* Interactive visualization via ``model.visualize()``

The legacy class names ``FlexModel``, ``PerformanceModel``, and ``Parallel_Link_Model`` are available as aliases for backward compatibility.

Model files from either the old PerformanceModel format (without ``circuit_id`` column) or FlexModel format (with ``circuit_id`` column) are automatically detected and loaded correctly by ``load_model_file()``.

Quick Start
***********

::

    from pyNTM import Model

    model = Model.load_model_file('network.csv')
    model.update_simulation()

    # Inspect results
    model.display_interfaces_traffic()

    # Visualize in the browser
    model.visualize()

How do I know the simulations work correctly?
**********************************************

There are many safeguards in place to ensure the simulation's mechanics are correct:

* Multiple functional tests in the CI/CD pipeline check for the expected mechanics and results for each routing method (ECMP, single path, RSVP, RSVP resignaling, etc) and other features in various topology scenarios:

  * If any of these tests fail, the build will fail and the bad code will not make it into production

    * This helps ensure that functionality works as expected and that new features and fixes don't break prior functionality

  * There are over 270 unit and functional tests in the pyNTM CI/CD pipeline
  * There are dozens of topology-specific functional tests in the pyNTM CI/CD pipeline that ensure the simulation works properly for different topologies, and more are added for each new feature

* The model object has internal checks that happen automatically during the ``update_simulation()`` execution:

  * Flagging interfaces that are not part of a circuit
  * Flagging if an interface's RSVP reserved bandwidth is greater than the interface's capacity
  * Verifying that each interface's RSVP reserved bandwidth matches the sum of the reserved bandwidth for the LSPs egressing the interface
  * Checks that the interface names on each node are unique
  * Validates that the capacities of each of the component interfaces in a circuit match
  * Validates that each node in an SRLG has the SRLG in the node's ``srlgs`` set
  * No duplicate node names are present in the topology

Note that there are more checks involving RSVP than IGP/ECMP routing because there are more mechanics involved when RSVP is running, whereas the straight IGP/ECMP routing is much simpler.

If any of these checks fails, ``update_simulation()`` will throw an error with debug info.
