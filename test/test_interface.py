import unittest

from network_modeling import Interface


class TestInterface(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.interface_a = Interface(name='inerfaceA-to-B', cost=4, capacity=100,
                                     node_object='nodeA', remote_node_object='nodeB', address=1)
