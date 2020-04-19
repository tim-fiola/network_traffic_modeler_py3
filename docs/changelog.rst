Changelog
=========

1.6
---
* Added support for multiple links between nodes (Parallel_Link_Model)
* Cached parallel_lsp_groups in Model and Parallel_Link_Model objects (performance optimization)
* Added check for multiple links between nodes in Model object (not allowed)
* Added Parent Class MasterModel to hold common defs for Model and Parallel_Link_Model subclasses
* Added simulation_diagnostics def in MasterModel that gives potentially useful diagnostic info about the simulation results
* Simple user interface (beta feature) supports RSVP LSPs

1.5
---
* Updated code to account for networkx
* Improved some docstrings


1.4
---
* updated requirements.txt to allow use of beta features


1.3
---
* improved docstring for Model load_model_file class method
* updated requirements
* fixed bugs in beta features: visualization and simple UI
* updated unit testing


1.2
---
* added shared-risk link group (SRLG) support for Nodes and Interfaces
* added performance optimizations
* simplified sections of code

1.1
----
* added configured, fixed setup bandwidth capability on RSVP LSPs
* made small performance optimizations

1.0
----
* first release including pypi inetgration



previous releases
------------------
* versions prior to v1.0 were not released to pip, but distributed as a github directory
* initially a py2 version was made available `here <https://github.com/tim-fiola/network_traffic_modeler>`_
* the py2 version is not maintained anymore in favor of the current py3 releases
