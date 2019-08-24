import unittest

from pyNTM import Model
from pyNTM import ModelException


class TestSRLG(unittest.TestCase):

    def test_failed(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        node_a = model.get_node_object('A')
        model.update_simulation()
        model.add_srlg('test_srlg')
        node_a.add_to_srlg('test_srlg', model)
        model.update_simulation()
        test_srlg = model.get_srlg_object('test_srlg')

        err_msg = 'must be boolean'
        with self.assertRaises(ModelException) as context:
            test_srlg.failed = 4
        self.assertTrue(err_msg in context.exception.args[0])
