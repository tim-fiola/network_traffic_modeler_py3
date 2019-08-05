import unittest

from pyNTM import find_end_index


class TestUtilities(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.lines = ['INTERFACES_TABLE', '', 'foobar']

    def test_find_end_index(self):
        end_index = find_end_index(0, self.lines)
        self.assertEqual(1, end_index)
