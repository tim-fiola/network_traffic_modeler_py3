Shared Risk Link Groups (SRLGs)
===============================

An SRLG represents a collection of model objects with shared risk factors.

An SRLG can include:

- Nodes
- Circuits

When the SRLG is failed (``failed = True``), the members will go to a failed state (``failed = True``) as well.
When the SRLG is not failed (``failed = False``), the members will also return to ``failed = False``.

Nodes are added to an SRLG via the ``add_to_srlg`` node method.

A circuit is added to an SRLG when a component interface is added to the SRLG via the ``add_to_srlg`` interface method.
The other interface in the interface's circuit is also automatically added to the SRLG.