import unittest
from remgu import SpacyPipelineArchitectureAdapter

class FakeNlp:
    pipe_names = ['tok2vec', 'tagger', 'parser']

class TestSpacyPipelineArchitectureAdapter(unittest.TestCase):
    def test_builds_pipeline_chain(self):
        dot = SpacyPipelineArchitectureAdapter().get_architecture_dot(FakeNlp())
        self.assertIn('pipe0 -> pipe1', dot)
        self.assertIn('parser', dot)

    def test_returns_none_without_pipeline(self):
        self.assertIsNone(SpacyPipelineArchitectureAdapter().get_architecture_dot(object()))
