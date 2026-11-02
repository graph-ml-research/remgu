import unittest
from remgu import ResourceMonitor

class TestResourceMonitor(unittest.TestCase):
    def test_snapshot_has_explicit_unavailable_values_and_elapsed_time(self):
        monitor = ResourceMonitor()
        snapshot = monitor.sample()
        self.assertIn('timestamp_seconds', snapshot)
        self.assertIn('ram_bytes_process', snapshot)
        self.assertGreaterEqual(snapshot['timestamp_seconds'], 0)
        self.assertIn('peak_ram_bytes_process', monitor.summary())
