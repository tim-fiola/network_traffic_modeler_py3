# Virtualenv

[Virtualenv](https://github.com/pypa/virtualenv) is tool for creating isolated 'virtual' python environments.

## Create your virtualenv

* Create an isolated virtual environment under the directory "venv" with python3 :
  ```bash
  virtualenv -p python3 venv
  ```
* Activate "venv" that sets up the required env variables
  ```bash
  source venv/bin/activate
  ```
* Install required packages with "pip"
  ```bash
  pip install -r requirements.txt
  ```

## Remove your virtualenv

* Deactivate "venv" that unsets the virtual env variables
  ```bash
  deactivate
  ```
* Remove directory "venv"
  ```bash
  rm -rf venv
  ```
