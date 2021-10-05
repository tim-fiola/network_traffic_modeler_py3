Development
===========

If you wish to contribute PRs to pyNTM, the sections below describe how to set up your development environment.

Currently, pyNTM adheres to the *black* code formatting and *flake8*. More info on *black* is below.

The *black* code formatting and *flake8* checks occur in the CI/CD pipeline.

The sections below cover how to set up your local dev environment to run these checks prior to submitting a pull request.

Set Up Your Virtual Environment
-------------------------------

Set up your virtual environment.

`Virtualenv <https://github.com/pypa/virtualenv>`_ is a tool for creating isolated 'virtual' python environments. For directions on how to run this modeler in a virtual environment and auto-download all dependencies, follow the steps below (authored by nelsg).

Create your virtualenv
**********************

Create an isolated virtual environment under the directory "network_traffic_modeler_py3" with python3::

   $ virtualenv -p python3 venv

Activate "venv" that sets up the required env variables::

   $ source venv/bin/activate

Install pyNTM's required packages with "pip3"::

    (venv) $ pip3 install -r requirements.txt

Installing Development Requirements
-----------------------------------

To install the Python modules required for development, run::

    % pip3 install -r requirements_dev.txt

The Black Code Formatter
************************

pyNTM uses the `black <https://pypi.org/project/black/>`_ code formatter. ``black`` is an opinionated formatter that
will make changes to your files to bring them in line with the ``black`` standards.

Setting Up Pre-Commit Hooks
***************************

The ``pre-commit`` package is installed when you install the ``requirements_dev.txt``.

To run ``black`` automatically after each commit, you will need to install the pre-commit hooks.

Run ``pre-commit install``::

    % pre-commit install

You should see a response that the hook has been installed::

    pre-commit installed at .git/hooks/pre-commit

This will set up a check that runs ``black`` prior to allowing a commit, allowing you to focus on making your code, instead of worrying about your formatting.

Local Unit Testing
------------------

To run the unit tests locally:

1. Go to the repository's ``network_traffic_modeler_py3`` directory::

    (venv) % pwd
    /path/to/network_traffic_modeler_py3
    (venv) %


2. Run ``pytest``::

    ``% pytest``

If the tests fail to run due to ``ImportError``, depending on your OS, you may need to run one of the following ``pytest`` variations::

    ``python -m pytest``

or::

    ``python3 -m pytest``

.. tip::
   When submitting a pull request, your build will be tested against black and the unit tests, so it's advantageous to test them locally prior so they don't fail in the CI pipeline.

Remove your virtualenv
----------------------

If you wish to remove your virtualenv when you are complete, follow the steps below.

Deactivate "venv" that unsets the virtual env variables::

   $ deactivate

Remove directory "venv"::

   $ rm -rf venv

pypy3
-----

pyNTM is compatible with the pypy3 interpreter. The pypy3 interpreter provides a 70-80% performance improvement over the python3 interpreter.

.. tip::
   By *performance*, we mean the time it takes to converge the model to produce a simulation (running  ``update_simulation``).

It is recommended, however, to *develop* in **python3**. Developing in **pypy3** is **NOT** recommended, because some of the developer tools are not compatible in a pypy3 environment.




