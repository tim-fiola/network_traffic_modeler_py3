import unittest

from pyNTM import find_end_index


class TestUtilities(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """
        Sets the class lines.

        Args:
            self: (todo): write your description
        """
        self.lines = ['INTERFACES_TABLE', '', 'foobar']

    def test_find_end_index(self):
        """
        Find the index of the end of the end of the index.

        Args:
            self: (todo): write your description
        """
        end_index = find_end_index(0, self.lines)
        self.assertEqual(1, end_index)
