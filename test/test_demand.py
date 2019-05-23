import unittest

from network_modeling import Node
from network_modeling import Demand


class TestDemand(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        node_a = Node(name='nodeA', lat=0, lon=0)
        node_b = Node(name='nodeB', lat=0, lon=0)
        self.demand = Demand(source_node_object=node_a, dest_node_object=node_b, traffic=10, name='A-to-B')