import unittest
from remgu import ExampleSelectionService

class TestExampleSelectionService(unittest.TestCase):
    def test_random_selection_is_reproducible_and_does_not_mutate(self):
        records = [{'example_id': str(i)} for i in range(10)]
        original = [dict(record) for record in records]
        service = ExampleSelectionService()
        self.assertEqual(service.select(records, seed=3), service.select(records, seed=3))
        self.assertEqual(records, original)

    def test_confident_errors_require_metadata_and_rank(self):
        records = [{'correct': False, 'confidence': .4}, {'correct': False, 'confidence': .9}, {'correct': True, 'confidence': 1.0}]
        selected = ExampleSelectionService().select(records, 'confident_errors')
        self.assertEqual(selected[0]['confidence'], .9)
        with self.assertRaises(ValueError): ExampleSelectionService().select([{'correct': False}], 'confident_errors')

    def test_correct_predictions_and_rare_examples(self):
        service = ExampleSelectionService()
        records = [
            {"correct": True, "frequency": 50},
            {"correct": False, "frequency": 2},
            {"correct": True, "frequency": 1},
        ]
        self.assertEqual(len(service.select(records, "correct_predictions")), 2)
        rare = service.select(records, "rare_examples", limit=2)
        self.assertEqual([item["frequency"] for item in rare], [1, 2])
