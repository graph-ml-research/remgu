import unittest
from remgu import Word2VecArchitectureAdapter

class FakeVectors:
    vector_size = 128

class FakeWord2Vec:
    wv = FakeVectors()

class TestWord2VecArchitectureAdapter(unittest.TestCase):
    def test_returns_conceptual_embedding_flow(self):
        dot = Word2VecArchitectureAdapter().get_architecture_dot(FakeWord2Vec())
        self.assertIn('128 dimensions', dot)
        self.assertIn('Embedding lookup', dot)

    def test_returns_none_without_vector_size(self):
        self.assertIsNone(Word2VecArchitectureAdapter().get_architecture_dot(object()))
