# -*- coding: utf-8 -*-
"""Tests for the src value objects."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from remgu.models.execution import Execution
from remgu.models.motivation import Motivation
from remgu.models import ResearchMetadata
from remgu.models import Review


class TestResearchModels(unittest.TestCase):
    """Verify the small immutable/mutable src state models."""

    def test_motivation_defaults_reference_to_none(self) -> None:
        """A new motivation has no reference by default."""
        self.assertEqual(Motivation("new").reference, None)

    def test_research_metadata_keeps_hypothesis_and_motivation(self) -> None:
        """Research metadata retains its two semantic components."""
        motivation = Motivation("previous_run", "run-001")
        metadata = ResearchMetadata("H2", motivation)
        self.assertEqual(metadata.hypothesis, "H2")
        self.assertEqual(metadata.motivation, motivation)

    def test_execution_stores_lifecycle_fields(self) -> None:
        """Execution stores status and timestamps without transformation."""
        started = datetime.now(timezone.utc)
        execution = Execution("running", started_at=started)
        self.assertEqual(execution.status, "running")
        self.assertEqual(execution.started_at, started)

    def test_review_defaults_to_needs_review(self) -> None:
        """New review state requires human review."""
        review = Review()
        self.assertEqual(review.status, "needs_review")
        self.assertIsNone(review.conclusion)
        self.assertIsNone(review.next_step)
