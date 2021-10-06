Changelog
=========

3.4.0
-----
* Updated test environment to Focal linux (from Xenial) to allow ``dash`` and ``dash-cytoscape`` package import in CI/CD for visualization

  * Allows for moving WeatherMap from beta to production in future
  * It's no longer necessary to explicitly install the visualization requirements separately

* Heavy updates for docs
* Implemented black code formatting for local commits and in Travis CI/CD pipeline
* Implemented standard column name for RSVP LSP attribute to describe a manually assigned metric:

  * FlexModel had ``lsp_metric`` column name in docstrings and examples
  * PerformanceModel had ``manual_metric`` column name in docstrings and examples
  * Standardized column name to ``manual_metric``
  * This was a purely cosmetic change as the actual ``manual_metric`` is based on the column's order in the table, not the specific column name

3.3.1
-----
* Fixed bug in FlexModel to account for complex topology scenario involving ECMP demand paths with multipe IGP shortcut LSPs and parallel links
* Added spacing_factor as a WeatherMap configurable parameter
* Added another test to functional tests within test_parallel_link_model for complex topology

3.3
---
* Import of the WeatherMap class must be done from pyNTM.weathermap instead of directly from pyNTM.  This prevents a warning message that is otherwise superficial unless you are using the WeatherMap class

3.2
---
* Fixed bug in WeatherMap class that caused scripts with WeatherMap to run 2x and to not be able to run a WeatherMap class live from the python3 CLI

3.1
---
* Removed automatic call of load_model_file class methods performing update_simulation() call automatically.

3.0
---
* WeatherMap class added as beta feature to provide interactive visualization of network topology.  This is a beta feature and is not undergoing unit testing.  This feature is supported in the python3 interpreter, but not in the pypy3 interpreter.  This feature gives a very interactive and informative visualization of the topology
* path_detail Demand property support in all Model classes; provides clarity on how much traffic is passing on a given Demand's path and how much of that traffic transits each component in the path
* Python 3.5 no longer supported
* Python 3.8 support added to unit/functional testing
* load_model_file class methods now perform update_simulation() call automatically.  The update_simulation() call is only necessary to run after making a change to the topology after the model file has been loaded


2.1
---
*  Enforcing tab-separated data in model data files (used to allow spaces or tabs between data entries)
*  FlexModel class allows IGP RSVP shortcuts
*  FlexModel and PerformanceModel classes allow/honor RSVP LSP manual metrics
*  Made load_model_file for FlexModel and PerformanceModel classes more forgiving for number of lines allowed between tables

2.0
---
*  Made version 1.7 into major version 2.0 to account for possible backwards compatibilty

1.7
---
* Renamed Model class to PerformanceModel
* Renamed Parallel_Link_Model class to FlexModel
* Optimization: general 18-25% performance improvement when measured by time to converge
* Moved common code from PerformanceModel and FlexModel to _MasterModel parent class
* Maintained unit testing coverage at 95%
* Cleaned up documentation/docstrings

1.6
---
* Added support for multiple links between nodes (Parallel_Link_Model)
* Cached parallel_lsp_groups in Model and Parallel_Link_Model objects (performance optimization)
* Added check for multiple links between nodes in Model object (not allowed)
* Added Parent Class _MasterModel to hold common defs for Model and Parallel_Link_Model subclasses
* Added simulation_diagnostics def in _MasterModel that gives potentially useful diagnostic info about the simulation results
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
