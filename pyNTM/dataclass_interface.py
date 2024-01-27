from .exceptions import ModelException

from dataclasses import dataclass
from .dataclass_node import Node


@dataclass
class Interface(object):
    name: str
    cost: int
    capacity: float
    node_object: Node
    remote_node_object: Node
    circuit_id: str
    rsvp_enabled: bool
    reservable_bandwidth: float



    @property
    def _key(self):
        """Unique ID for interface object"""
        return (self.name, self.node_object.name)

    def __eq__(self, other_object):
        if not isinstance(other_object, Interface):
            return NotImplemented

        return [
            self.node_object,
            self.remote_node_object,
            self.name,
            self.capacity,
            self.circuit_id,
        ] == [
            other_object.node_object,
            other_object.remote_node_object,
            other_object.name,
            other_object.capacity,
            other_object.circuit_id,
        ]

    def __ne__(self, other_object):
        return [
            self.node_object,
            self.remote_node_object,
            self.name,
            self.capacity,
            self.circuit_id,
        ] != [
            other_object.node_object,
            other_object.remote_node_object,
            other_object.name,
            other_object.capacity,
            other_object.circuit_id,
        ]

    def __hash__(self):
        # return hash(tuple(sorted(self.__dict__.items())))
        return hash(self.name + self.node_object.name)

