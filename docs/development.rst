Development
===========

Installing Requirements
***********************

To install the Python modules required for development, run

``pip3 install -r requirements_dev.txt``


The Black Code Formatter
************************

pyNTM uses the `black <https://pypi.org/project/black/>`_ code formatter. ``black`` is an opinionated formatter that
will make changes to your files to bring them in line with the ``black`` standards.


Setting Up Pre-Commit Hooks
***************************

You will need to install the pre-commit hooks to run ``black``.

Run ``pre-commit install``:

```
(venv) PycharmProjects/network_traffic_modeler_py3 % pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

This will set up a check that runs ``black`` prior to allowing a commit.

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





