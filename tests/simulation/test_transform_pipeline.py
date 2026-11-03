import unittest
from remgu import NumericNoiseTransform, RandomSource, TransformPipeline

class TestTransformPipeline(unittest.TestCase):
    def test_dataset_mode_is_reproducible(self):
        pipeline = TransformPipeline([NumericNoiseTransform('x', 0.1)])
        records = [{'x': 1.0}, {'x': 2.0}]
        self.assertEqual(pipeline.apply_dataset(records, RandomSource(5)),
                         pipeline.apply_dataset(records, RandomSource(5)))
        self.assertEqual(records, [{'x': 1.0}, {'x': 2.0}])

    def test_batch_mode_is_lazy_over_batches(self):
        pipeline = TransformPipeline([NumericNoiseTransform('x', 0.0)], mode='batch')
        batches = pipeline.transform_batches([[{'x': 1}], [{'x': 2}]], RandomSource(1))
        self.assertEqual(next(batches), [{'x': 1.0}])
        self.assertEqual(next(batches), [{'x': 2.0}])

    def test_wrong_mode_is_rejected(self):
        with self.assertRaises(RuntimeError):
            TransformPipeline([], mode='batch').apply_dataset([], RandomSource(1))
