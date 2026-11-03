import json
import unittest
from urllib.request import Request, urlopen
from remgu import DashboardServer, ExperimentController

class TestDashboardServer(unittest.TestCase):
    def test_local_server_serves_state_and_probe_panel(self):
        server = DashboardServer({'status': 'running'}, port=0)
        server.publish_event({'type': 'probe', 'message': 'gradient warning'})
        url = server.start()
        try:
            with urlopen(url + 'api/state', timeout=3) as response:
                state = json.loads(response.read().decode())
            with urlopen(url, timeout=3) as response:
                page = response.read().decode()
            self.assertEqual(state['state']['status'], 'running')
            self.assertIn('Probe and model health', page)
            self.assertIn('textContent', page)
            self.assertIn("input.type='range'", page)
            self.assertIn('examples-page-status', page)
            self.assertIn('metric-chart', page)
            self.assertIn('Probe and model health', page)
        finally:
            server.stop()

    def test_config_param_types_are_exposed_as_structural_and_view_controls(self):
        server = DashboardServer({"config": {"depth": 4, "filter": "spam", "param_types": {"depth": "structural", "filter": "view"}}}, port=0)
        url = server.start()
        try:
            with urlopen(url + 'api/state', timeout=3) as response:
                state = json.loads(response.read().decode())['state']
            self.assertEqual(state['control_parameters']['depth']['category'], 'structural')
            self.assertEqual(state['control_parameters']['filter']['category'], 'view')
        finally:
            server.stop()

    def test_rejects_non_loopback_bind(self):
        with self.assertRaises(ValueError): DashboardServer(host='0.0.0.0')

    def test_control_endpoint_uses_allowlisted_controller(self):
        applied = []
        controller = ExperimentController({'lr': {'category': 'hot', 'type': 'float', 'min': 0, 'max': 1}},
                                          lambda name, value: applied.append((name, value)) or 'ok')
        server = DashboardServer(controller=controller, port=0)
        url = server.start()
        try:
            request = Request(url + 'api/command', data=json.dumps({'action': 'parameter', 'name': 'lr', 'value': 0.2}).encode(),
                              headers={'Content-Type': 'application/json'}, method='POST')
            with urlopen(request, timeout=3) as response:
                result = json.loads(response.read().decode())
            self.assertTrue(result['ok'])
            self.assertEqual(applied, [('lr', 0.2)])
        finally:
            server.stop()

    def test_run_context_starts_and_stops_dashboard_and_accepts_metrics(self):
        server = DashboardServer(port=0)
        with server.run(interval=0.02) as url:
            self.assertTrue(url.startswith("http://127.0.0.1:"))
            server.log_metrics(loss=0.4, accuracy=0.8)
            self.assertEqual(server.snapshot()["state"]["metrics"]["loss"], 0.4)
        self.assertIsNone(server._httpd)
        self.assertEqual(server.state["status"], "completed")
