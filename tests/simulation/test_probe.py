import unittest
from remgu import Probe

class TestProbe(unittest.TestCase):
    def test_collects_adapter_diagnostics(self):
        class Adapter:
            def get_probe_data(self):
                return {'gradient_norm': 0.5}
        self.assertEqual(Probe(Adapter()).collect(), {'status': 'available', 'data': {'gradient_norm': 0.5}})

    def test_reports_unavailable_when_contract_missing(self):
        self.assertEqual(Probe(object()).collect()['status'], 'unavailable')

    def test_rejects_invalid_adapter_payload(self):
        class Adapter:
            def get_probe_data(self):
                return []
        with self.assertRaises(TypeError):
            Probe(Adapter()).collect()
