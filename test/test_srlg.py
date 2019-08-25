import unittest

from pyNTM import Model
from pyNTM import ModelException
from pyNTM import SRLG


class TestSRLG(unittest.TestCase):

    def test_repr(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        new_srlg = SRLG('new_srlg', model)

        self.assertEqual(new_srlg.__repr__(), 'SRLG(Name: new_srlg)')

    def test_failed_boolean(self):
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

    def test_duplicate_srlg(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        SRLG('new_srlg', model)
        err_msg = 'SRLG with name new_srlg already exists in Model'
        with self.assertRaises(ModelException) as context:
            SRLG('new_srlg', model)
        self.assertTrue(err_msg in context.exception.args[0])

    def test_duplicate_srlg_2(self):
        model = Model.load_model_file('test/igp_routing_topology.csv')
        model.add_srlg('new_srlg')
        err_msg = 'SRLG with name new_srlg already exists in Model'
        with self.assertRaises(ModelException) as context:
            model.add_srlg('new_srlg')
        self.assertTrue(err_msg in context.exception.args[0])
