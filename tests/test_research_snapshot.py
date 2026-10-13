# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for the in-memory research snapshot layer."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from remgu import Experiment, ResearchSnapshotBuilder
from remgu.models import Motivation
from remgu.publication import MarkdownAdapter


class TestResearchSnapshot(unittest.TestCase):
    """Verify snapshot construction, optional enrichment and read-only behaviour."""

    def setUp(self) -> None:
        """Create an isolated research store."""
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name) / ".research"

    def tearDown(self) -> None:
        """Remove the isolated research store."""
        self.temp.cleanup()

    def _completed_run(self, hypothesis: str, motivation: Motivation) -> str:
        """Create one completed reviewed run with representative artifacts.

        Args:
            hypothesis: Hypothesis to persist.
            motivation: Motivation for the run.
        """
        experiment = Experiment("graph-mamba", self.base)
        with experiment.run(hypothesis, motivation) as run:
            run.log_params({"hidden_dim": 512, "seed": 42})
            run.log_metric("ndcg@20", 0.428, step=10)
            run.collect({"example_id": "node-42", "target": 1, "prediction": 0.91})
        run_id = run.run_id
        data = experiment.storage.read_run(run_id)
        data["review"] = {"status": "reviewed", "conclusion": "Supported", "next_step": "Run H2"}
        experiment.storage.write_run(run_id, data)
        return run_id

    def test_empty_project_is_empty_and_read_only(self) -> None:
        """Build an empty snapshot without creating the runs directory."""
        snapshot = ResearchSnapshotBuilder(self.base).build()
        self.assertEqual(snapshot.summary.total_runs, 0)
        self.assertEqual(snapshot.runs, [])
        self.assertEqual(snapshot.findings, [])
        self.assertFalse(self.base.exists())

    def test_snapshot_collects_runs_relations_artifacts_and_review(self) -> None:
        """Collect persisted metadata, artifacts and existing motivation relations."""
        first = self._completed_run("H1", Motivation(type="new"))
        second = self._completed_run("H2", Motivation(type="previous_run", reference=first))
        snapshot = ResearchSnapshotBuilder(self.base).build()
        self.assertEqual(snapshot.summary.total_runs, 2)
        self.assertEqual(snapshot.summary.completed, 2)
        self.assertEqual(snapshot.summary.reviewed, 2)
        self.assertEqual(snapshot.relations, [{"run_id": second, "reference": first}])
        self.assertEqual(snapshot.runs[0].params["hidden_dim"], 512)
        self.assertEqual(snapshot.runs[0].metrics[0]["metric_name"], "ndcg@20")
        self.assertEqual(snapshot.samples[0]["example_id"], "node-42")
        self.assertEqual(snapshot.runs[0].conclusion, "Supported")

    def test_snapshot_counts_failed_and_aborted(self) -> None:
        """Count terminal failure states without requiring conclusions."""
        experiment = Experiment("graph-mamba", self.base)
        first = experiment.run("H1", Motivation(type="new"))
        first.abort()
        second = experiment.run("H2", Motivation(type="new"))
        second.fail(RuntimeError("boom"))
        snapshot = ResearchSnapshotBuilder(self.base).build()
        self.assertEqual(snapshot.summary.aborted, 1)
        self.assertEqual(snapshot.summary.failed, 1)
        self.assertEqual(snapshot.summary.completed, 0)

    def test_example_descriptions_are_optional_snapshot_enrichment(self) -> None:
        """Attach provider descriptions to reports without changing persisted samples."""
        self._completed_run("H1", Motivation(type="new"))

        class Provider:
            def describe(self, example_id: str) -> str:
                return f"User-item interaction for {example_id}"

            def get(self, example_id: str):
                return {"id": example_id}

        with self.assertRaisesRegex(ValueError, "requires an example_provider"):
            ResearchSnapshotBuilder(self.base, describe_examples=True)

        snapshot = ResearchSnapshotBuilder(
            self.base, example_provider=Provider(), describe_examples=True
        ).build()
        self.assertEqual(snapshot.samples[0]["description"], "User-item interaction for node-42")
        report = MarkdownAdapter().render(snapshot)
        self.assertIn("**Description:** User-item interaction for node-42", report)

        plain_snapshot = ResearchSnapshotBuilder(self.base).build()
        self.assertNotIn("description", plain_snapshot.samples[0])

    def test_snapshot_does_not_modify_source_files(self) -> None:
        """Ensure snapshot construction leaves source files byte-for-byte unchanged."""
        self._completed_run("H1", Motivation(type="new"))
        files = sorted(path for path in self.base.rglob("*") if path.is_file())
        before = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in files}
        ResearchSnapshotBuilder(self.base).build()
        after = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in files}
        self.assertEqual(before, after)
