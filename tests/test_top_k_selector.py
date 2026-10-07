# -*- coding: utf-8 -*-
"""Tests for TopKSelector."""
from __future__ import annotations

import unittest

from remgu.example import TopKSelector


class TestTopKSelector(unittest.TestCase):
    """Verify ranking and bounded-memory behavior of TopKSelector."""

    def test_keeps_only_highest_priority(self) -> None:
        """Retain the two records with highest explicit priorities."""
        selector = TopKSelector(k=2)
        for example_id, priority in (("a", 0.1), ("b", 0.9), ("c", 0.4), ("d", 1.2)):
            selector.consider({"example_id": example_id}, priority)
        self.assertEqual(selector.records(), [{"example_id": "d"}, {"example_id": "b"}])
        self.assertEqual(len(selector), 2)

    def test_can_choose_smallest_score_with_key(self) -> None:
        """Retain the smallest scores when configured accordingly."""
        selector = TopKSelector(k=2, key=lambda record: record["score"], largest=False, name="lowest_score")
        for score in (0.8, 0.1, 0.5, 0.2):
            selector.consider({"example_id": str(score), "score": score})
        self.assertEqual([record["score"] for record in selector.records()], [0.1, 0.2])

    def test_can_choose_largest_change(self) -> None:
        """Rank records by absolute change from a baseline."""
        selector = TopKSelector(k=2, key=lambda record: abs(record["score"] - record["baseline_score"]), name="largest_change")
        selector.consider({"example_id": "a", "score": 0.3, "baseline_score": 0.4})
        selector.consider({"example_id": "b", "score": 0.1, "baseline_score": 0.8})
        selector.consider({"example_id": "c", "score": 0.7, "baseline_score": 0.2})
        self.assertEqual([record["example_id"] for record in selector.records()], ["b", "c"])

    def test_does_not_require_dataset_storage(self) -> None:
        """Keep only k records regardless of stream length."""
        selector = TopKSelector(k=2, key=lambda record: record["score"])
        for index in range(1000):
            selector.consider({"example_id": str(index), "score": index})
        self.assertEqual(len(selector), 2)
        self.assertEqual([record["example_id"] for record in selector.records()], ["999", "998"])

    def test_rejects_invalid_k(self) -> None:
        """Reject non-positive selector sizes."""
        with self.assertRaisesRegex(ValueError, "positive"):
            TopKSelector(0)
