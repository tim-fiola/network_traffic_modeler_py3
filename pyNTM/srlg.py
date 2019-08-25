"""A Class to represent Shared Risk Link Groups (SRLGs) in a Model"""
from .exceptions import ModelException


class SRLG(object):
    """
    Represents a collection of Model objects with shared risk factors.
    Can include:
    Nodes
    Circuits

    When self.failed = True, the members will go to a failed state as well.
    When self.failed returns to False, the members will also return to
    failed = False.

    """

    def __init__(self, name, model, circuit_objects=set(), node_objects=set()):
        # self.circuit_objects = circuit_objects
        # self.node_objects = node_objects
        if name in set([srlg.name for srlg in model.srlg_objects]):
            raise ModelException("SRLG with name {} already exists in Model".format(name))
        else:
            self.name = name
            self.model = model
            self._failed = False
            model.srlg_objects.add(self)

    def __repr__(self):
        return "SRLG(Name: {})".format(self.name)

    # def interfaces(self, model):  # TODO - use interfaces or circuits?
    #     """
    #     Returns set of Interface objects, derived from Circuits in the SRLG
    #     :param model: Model object
    #     :return: set of Interface objects
    #     """
    #     interfaces = set()
    #     for ckt in (ckt for ckt in self.circuit_objects):
    #         ints = ckt.get_circuit_interfaces(model)
    #         interfaces.add(ints[0])
    #         interfaces.add(ints[1])
    #
    #     return interfaces

    @property
    def failed(self):
        return self._failed

    @failed.setter
    def failed(self, status):
        if isinstance(status, bool):
            self._failed = status
        else:
            raise ModelException('must be boolean')

    @property
    def node_objects(self):
        nodes = set([node for node in self.model.node_objects if self in node.srlgs])
        return nodes

    # TODO - add srlg.fail and srlg.unfail
