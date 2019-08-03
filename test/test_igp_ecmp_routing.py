import unittest

from pyNTM import Model


class TestIGPRouting(unittest.TestCase):
    def test_ecmp(self):
        model8 = Model.load_model_file('test/igp_routing_topology.csv')

        model8.update_simulation()

        int_a_b = model8.get_interface_object('A-to-B', 'A')
        int_b_d = model8.get_interface_object('B-to-D', 'B')
        int_b_g = model8.get_interface_object('B-to-G', 'B')
        int_g_d = model8.get_interface_object('G-to-D', 'G')
        int_d_f = model8.get_interface_object('D-to-F', 'D')
        int_a_c = model8.get_interface_object('A-to-C', 'A')
        int_c_d = model8.get_interface_object('C-to-D', 'C')
        int_a_d = model8.get_interface_object('A-to-D', 'A')

        self.assertEqual(int_a_b.traffic, 20)
        self.assertEqual(int_b_d.traffic, 10)
        self.assertEqual(int_d_f.traffic, 40)
        self.assertEqual(int_b_g.traffic, 10)
        self.assertEqual(int_g_d.traffic, 10)
        self.assertEqual(int_a_c.traffic, 0)
        self.assertEqual(int_c_d.traffic, 0)
        self.assertEqual(int_a_d.traffic, 20)
