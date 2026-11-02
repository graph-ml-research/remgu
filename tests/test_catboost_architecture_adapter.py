import unittest
from remgu import CatBoostArchitectureAdapter

class FakeCatBoost:
    tree_count_ = 100

class TestCatBoostArchitectureAdapter(unittest.TestCase):
    def test_bounds_tree_count_and_reports_omissions(self):
        dot = CatBoostArchitectureAdapter(max_trees=3).get_architecture_dot(FakeCatBoost())
        self.assertIn('Ensemble: 100 trees', dot)
        self.assertIn('97 additional trees omitted', dot)

    def test_validates_limit(self):
        with self.assertRaises(ValueError): CatBoostArchitectureAdapter(max_trees=0)
