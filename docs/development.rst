Development
===========

Installing Requirements
***********************

To install the Python modules required for development, run

``pip3 install -r requirements_dev.txt``


Local Unit Testing
******************

To run the unit tests locally:

1. Go to the ``network_traffic_modeler_py3`` directory

```
(venv) PycharmProjects/network_traffic_modeler_py3 % pwd
/dev/network_traffic_modeler_py3
(venv) PycharmProjects/network_traffic_modeler_py3 %
```

2. Run ``pytest``

``% pytest``

If the tests fail to run, depending on your OS, you may need to run one of the following variations on ``pytest``:

``python -m pytest``

``python3 -m pytest``





