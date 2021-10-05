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

Model Type Subclasses
*********************

There are two network model subclasses: ``FlexModel`` and ``PerformanceModel``.

In general, the ``FlexModel`` can accommodate more topology variations, but at the price of a slightly longer convergence time while the ``PerformanceModel`` can only handle
simpler network architectures, but with the benefit of better convergence time.

All model classes support:

* IGP routing
* RSVP LSPs carrying traffic demands that have matching source and destination as the RSVP LSPs
* RSVP auto-bandwidth or fixed bandwidth
* RSVP LSP manual metrics

The ``PerformanceModel`` class allows for:

* Single circuits between 2 Nodes
* Error messages if it detects use of IGP shortcuts or multiple Circuits between 2 Nodes

The ``FlexModel`` class allows for:

* Multiple Circuits between 2 Nodes
* RSVP LSP IGP shortcuts, whereby LSPs can carry traffic demands downstream, even if the demand does not have matching source and destination as the LSP

How do I know the simulation worked correctly?
**********************************************

There are a couple safeguards in place to ensure the simulation's mechanics are correct:

* Functional tests in the CI/CD pipeline check for the expected mechanics and results for each routing method (ECMP, single path, RSVP, RSVP resignaling, etc) in various topology scenarios
  * If any of these tests fail, the build will fail and the bad code will not make it into production
  * This helps ensure that functionality works as expected and that new features and fixes don't break prior functionality
* The model object has internal checks that happen automatically during ``update_simulation()`` method
  * Flagging interfaces that are not part of a circuit
  * If an interface's RSVP reserved bandwidth is greater than the interface's capacity
  * Verifying that each interface's RSVP reserved bandwidth matches the sum of the reserved bandwidth for the LSPs egressing the interface
  * Checks that the interface names on each node are unique
  * Validates that each of the component interfaces in a circuit match
  * Validate that each node in an SRLG has the SRLG in the node's ``srlgs`` set
  * No duplicate node names are present in the topology

The PerformanceModel also checks for

* IGP shortcuts not enabled
* No more than a single circuit (edge) between any two nodes

Note that there are more checks involving RSVP than IGP/ECMP routing because there are more mechanics involved when RSVP is running, whereas the straight IGP/ECMP routing is much simpler.

If any of these checks fails, ``update_simulation()`` will throw an error with debug info.