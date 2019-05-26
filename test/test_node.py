import unittest

from pyNTM import Node


class TestNode(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.node_a = Node(name='nodeA', lat=0, lon=0)
