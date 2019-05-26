import unittest

from pyNTM import Node
from pyNTM import Demand


class TestDemand(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.node_a = Node(name='nodeA', lat=0, lon=0)
        self.node_b = Node(name='nodeB', lat=0, lon=0)
        self.demand = Demand(source_node_object=self.node_a, dest_node_object=self.node_b, traffic=10, name='A-to-B')
