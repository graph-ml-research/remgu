import unittest
from remgu import ExampleReportSelector


class TestExampleReportSelector(unittest.TestCase):
    def test_prioritizes_errors_and_bounds_selection(self):
        records = [{"id": index, "correct": index >= 20, "confidence": index / 100}
                   for index in range(1000)]
        selected = ExampleReportSelector(limit=10).select(records)
        self.assertEqual(len(selected), 10)
        self.assertTrue(all(record["correct"] is False for record in selected))
        self.assertEqual(len(records), 1000)

    def test_handles_generic_scored_examples(self):
        selected = ExampleReportSelector(limit=2).select([{"score": 1}, {"score": 4}, {"score": 3}])
        self.assertEqual([item["score"] for item in selected], [4, 3])
