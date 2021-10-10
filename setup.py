from setuptools import setup, find_packages

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

version = "3.4.0"

# with open("README.md", "r") as fh:  # TODO - delete if pypi build works
#     long_description = fh.read()

long_description = (
    "This is a network traffic modeler written in python 3. The main use cases involve "
    "understanding how your layer 3 traffic will transit a given topology.  You can modify the "
    "topology (add/remove layer 3 Nodes, Circuits, Shared Risk Link Groups), fail elements in the "
    "topology, or add new traffic Demands to the topology. pyNTM is a simulation engine that will "
    "converge the modeled topology to give you insight as to how traffic will transit a given "
    "topology, either steady state or with failures. This library allows users "
    "to define a layer 3 network "
    "topology, define a traffic matrix, and then run a simulation to determine how the traffic will "
    "traverse the topology, traverse a modified topology, and fail over. If you've used Cariden MATE "
    "or WANDL, this code solves for some of the same basic use cases those do.  This package is in "
    "no way related to those, or any, commercial products.  IGP and RSVP routing is supported."
)

setup(
    name="pyNTM",
    version=version,
    py_modules=["pyNTM"],
    packages=find_packages(),
    install_requires=reqs,
    include_package_data=True,
    description="Network traffic modeler API written in Python 3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tim Fiola",
    author_email="timothy.fiola@gmail.com",
    url="https://github.com/tim-fiola/network_traffic_modeler_py3",
    download_url="https://github.com/tim-fiola/network_traffic_modeler_py3/tarball/%s"
    % version,
    keywords=["networking", "layer3", "failover", "modeling", "model", "pyNTM"],
    classifiers=[],
)
