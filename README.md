
[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![Build Status](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3.svg?branch=master)](https://travis-ci.org/tim-fiola/network_traffic_modeler_py3)
[![Coverage Status](https://coveralls.io/repos/github/tim-fiola/network_traffic_modeler_py3/badge.svg?branch=master)](https://coveralls.io/github/tim-fiola/network_traffic_modeler_py3?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pyntm/badge/?version=latest)](https://pyntm.readthedocs.io/en/latest/?badge=latest)


pyNTM: network_traffic_modeler_py3
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do.  IGP and RSVP auto-bandwidth routing is supported. 


Install
=======

Install via pip:
```bash
pip3 install pyNTM
```

For upgrade:
```bash
pip3 install --upgrade pyNTM
```


Documentation
=============

See the documentation on [Read the Docs](http://pyntm.readthedocs.org).


Examples
========

See the [example directory](https://github.com/tim-fiola/network_traffic_modeler_py3/blob/master/examples).


Notes
=====

The previous py2 version is located [here](https://github.com/tim-fiola/network_traffic_modeler) but won't be maintained any further in favor of the py3 version in this repository.


License
=======

Copyright 2019 Tim Fiola

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
