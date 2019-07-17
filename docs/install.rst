Install
=========

To use the library, best install it via pip as shown below.

Install via pip::

  $ pip3 install pyNTM

To upgrade::

  $ pip3 install --upgrade pyNTM


Virtualenv
-----------

`Virtualenv <https://github.com/pypa/virtualenv>`_ is a tool for creating isolated 'virtual' python environments. For directions on how to run this modeler in a virtual environment and auto-download all dependencies, follow the steps below (authored by nelsg).

Create your virtualenv
~~~~~~~~~~~~~~~~~~~~~~~~

Create an isolated virtual environment under the directory "venv" with python3::

   $ virtualenv -p python3 venv

Activate "venv" that sets up the required env variables::

   $ source venv/bin/activate

Install required packages with "pip"::

   $ pip install -r requirements.txt

Remove your virtualenv
~~~~~~~~~~~~~~~~~~~~~~~~~

Deactivate "venv" that unsets the virtual env variables::

   $ deactivate

Remove directory "venv"::

   $ rm -rf venv
