

from dataclasses import dataclass


@dataclass
class Node(object):
    name: str
    _failed: bool=False
    _lat: float = ""
    _lon: float = ""
    _srlgs: set = ""
    _igp_shortcuts_enabled: bool = False

    # Modify __eq__ and __hash__ default behavior for Node class
    # to allow us to easily determine if a Node instance is equivalent to another.
    # By default, equivalency test is 1) id, 2) hash, 3) equality.  The id test will
    # fail and so it will move to hash and then equality.  Modifying the __eq__ to
    # focus on the Node.name equivalency and __hash__ to focus on the
    # hash of the Node.name will make equivalency testing possible
    def __eq__(self, other_node):
        return self.__dict__ == other_node.__dict__

    def __hash__(self):
        # return hash(tuple(sorted(self.__dict__.items())))
        return hash(self.name)

    def _key(self):
        return self.name

