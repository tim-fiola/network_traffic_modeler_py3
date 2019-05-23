
[![PyPI](https://img.shields.io/pypi/v/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![PyPI](https://img.shields.io/pypi/dm/pyntm.svg)](https://pypi.python.org/pypi/pyNTM)
[![Build Status](https://travis-ci.org/fooelisa/pyiosxr.svg?branch=master)](https://travis-ci.org/fooelisa/pyntm)
[![Coverage Status](https://coveralls.io/repos/github/fooelisa/pyntm/badge.svg?branch=master)](https://coveralls.io/github/fooelisa/pyntm?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pyNTM/badge/?version=latest)](http://pyntm.readthedocs.io/en/latest/?badge=latest)


pyNTM: network_traffic_modeler_py3
==================================

This is a network traffic modeler written in python 3. This library allows users to define a layer 3 network topology, define a traffic matrix, and then run a simulation to determine how the traffic will traverse the topology. If you've used Cariden MATE or WANDL, this code solves for some of the same basic use cases those do (but those solve for much more as well).


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

See the [example directory](./examples). 


Notes
=====

The previous py2 version is located [here](https://github.com/tim-fiola/network_traffic_modeler) but won't be maintained any further in favor of the py3 version in this repository.


License
=======

Copyright 2019 Tim Fiola

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
