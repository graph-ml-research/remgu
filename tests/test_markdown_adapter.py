# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for Markdown publication from a ResearchSnapshot."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from remgu import ConsistencyIssue, Experiment, MarkdownAdapter, ResearchSnapshotBuilder
from remgu.models import Motivation


class TestMarkdownAdapter(unittest.TestCase):
    """Verify report content, read-only publication, and overwrite protection."""

    def setUp(self) -> None:
        """Create isolated source and publication paths."""
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name) / ".research"
        self.output = Path(self.temp.name) / "research.md"
        self.adapter = MarkdownAdapter()

    def tearDown(self) -> None:
        """Remove temporary files created by this test case."""
        self.temp.cleanup()

    def _create_run(self, hypothesis: str, motivation: Motivation, reviewed: bool = False) -> str:
        """Persist a completed run with representative metrics and samples.

        Args:
            hypothesis: Hypothesis text to store in the run.
            motivation: Existing motivation and optional reference for the run.
            reviewed: Whether to attach a conclusion and next step.

        Returns:
            Persistent run identifier.
        """
        experiment = Experiment("graph-mamba", self.base)
        with experiment.run(hypothesis, motivation) as run:
            run.log_params({"hidden_dim": 128, "seed": 7})
            run.log_metric("auc", 0.91, step=3)
            run.collect({"example_id": "node-42", "target": 1, "prediction": 0.91})
        run_id = run.run_id
        if reviewed:
            data = experiment.storage.read_run(run_id)
            data["review"] = {
                "status": "reviewed",
                "conclusion": "AUC improved on validation data.",
                "next_step": "Repeat with another seed.",
            }
            experiment.storage.write_run(run_id, data)
        return run_id

    def test_empty_project_contains_all_required_sections(self) -> None:
        """Render an empty snapshot with all report sections and no source writes."""
        snapshot = ResearchSnapshotBuilder(self.base).build()
        markdown = self.adapter.render(snapshot)
        self.assertIn("# Research report", markdown)
        for heading in ("## Summary", "## Research history", "## Relations", "## Collected examples", "## Consistency", "## Conclusions"):
            self.assertIn(heading, markdown)
        self.assertIn("Total runs: 0", markdown)
        self.assertFalse(self.base.exists())

    def test_one_run_includes_hypothesis_params_metrics_and_sample(self) -> None:
        """Render core run metadata and compact artifacts from the snapshot."""
        self._create_run("H1 improves AUC", Motivation(type="new"))
        markdown = self.adapter.render(ResearchSnapshotBuilder(self.base).build())
        self.assertIn("### run-001", markdown)
        self.assertIn("H1 improves AUC", markdown)
        self.assertIn("Execution status:", markdown)
        self.assertIn("Review status:", markdown)
        self.assertIn("hidden_dim", markdown)
        self.assertIn("auc", markdown)
        self.assertIn("0.91", markdown)
        self.assertIn('"example_id": "node-42"', markdown)

    def test_multiple_runs_render_chronologically_and_show_relations(self) -> None:
        """Render runs in snapshot order and show existing motivation references."""
        first = self._create_run("H1 baseline", Motivation(type="new"), reviewed=True)
        second = self._create_run("H2 follow-up", Motivation(type="previous_run", reference=first))
        markdown = self.adapter.render(ResearchSnapshotBuilder(self.base).build())
        self.assertLess(markdown.index("### run-001"), markdown.index("### run-002"))
        self.assertIn(f"`{second}` ← `{first}`", markdown)
        self.assertIn("AUC improved on validation data.", markdown)
        self.assertIn("Repeat with another seed.", markdown)

    def test_failed_and_aborted_statuses_are_reported(self) -> None:
        """Include non-successful execution states in summary and history."""
        experiment = Experiment("graph-mamba", self.base)
        aborted = experiment.run("H-aborted", Motivation(type="new"))
        aborted.abort()
        failed = experiment.run("H-failed", Motivation(type="new"))
        failed.fail(RuntimeError("training failed"))
        markdown = self.adapter.render(ResearchSnapshotBuilder(self.base).build())
        self.assertIn("- Failed: 1", markdown)
        self.assertIn("- Aborted: 1", markdown)
        self.assertIn("`failed`", markdown)
        self.assertIn("`aborted`", markdown)

    def test_consistency_findings_are_included(self) -> None:
        """Surface existing consistency warnings without inferring conclusions."""
        self._create_run("H1 without review", Motivation(type="new"))
        markdown = self.adapter.render(ResearchSnapshotBuilder(self.base).build())
        self.assertIn("Findings: 1 warnings, 0 errors.", markdown)
        self.assertIn("missing_conclusion", markdown)
        self.assertIn("completed run has no conclusion", markdown)

    def test_consistency_errors_are_counted_and_rendered(self) -> None:
        """Render error-level consistency findings distinctly from warnings."""
        snapshot = ResearchSnapshotBuilder(self.base).build()
        snapshot.findings.append(ConsistencyIssue("run-999", "invalid_structure", "run record is malformed", "error"))
        markdown = self.adapter.render(snapshot)
        self.assertIn("Findings: 0 warnings, 1 errors.", markdown)
        self.assertIn("**error**", markdown)
        self.assertIn("invalid_structure", markdown)
        self.assertIn("run record is malformed", markdown)

    def test_export_does_not_modify_source_and_refuses_overwrite(self) -> None:
        """Write a report without changing research files or replacing existing output."""
        self._create_run("H1", Motivation(type="new"), reviewed=True)
        source_files = sorted(path for path in self.base.rglob("*") if path.is_file())
        before = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in source_files}
        snapshot = ResearchSnapshotBuilder(self.base).build()
        result = self.adapter.export(snapshot, self.output)
        self.assertEqual(result, self.output)
        after = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in source_files}
        self.assertEqual(before, after)
        self.assertTrue(self.output.read_text(encoding="utf-8").startswith("# Research report"))
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            self.adapter.export(snapshot, self.output)
