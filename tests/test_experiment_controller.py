import unittest
from remgu import ExperimentController

class TestExperimentController(unittest.TestCase):
    def test_validates_hot_parameter_and_audits_update(self):
        changes = []
        controller = ExperimentController({'lr': {'category': 'hot', 'type': 'float', 'min': 0, 'max': 1}},
                                          lambda name, value: changes.append((name, value)) or 'applied')
        event = controller.apply_parameter('lr', 0.1)
        self.assertEqual(changes, [('lr', 0.1)])
        self.assertEqual(event['type'], 'parameter_update')
        self.assertEqual(len(controller.audit_log), 1)

    def test_rejects_structural_and_unknown_parameters(self):
        controller = ExperimentController({'layers': {'category': 'structural', 'type': 'int'}})
        with self.assertRaises(ValueError): controller.apply_parameter('layers', 4)
        with self.assertRaises(ValueError): controller.apply_parameter('unknown', 4)
