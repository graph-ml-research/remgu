# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for static HTML publication from a ResearchSnapshot."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from remgu import ConsistencyIssue, Experiment, ResearchSnapshotBuilder, StaticSiteAdapter
from remgu.models import Motivation


class TestStaticSiteAdapter(unittest.TestCase):
    """Verify static site content, file layout, safety, and source immutability."""

    def setUp(self) -> None:
        """Create isolated research and site paths."""
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base = self.root / ".research"
        self.output = self.root / "site"
        self.adapter = StaticSiteAdapter()

    def tearDown(self) -> None:
        """Remove all temporary test files."""
        self.temp.cleanup()

    def _create_run(self, hypothesis: str, motivation: Motivation, reviewed: bool = False) -> str:
        """Create a completed run with params, metric, and a compact sample.

        Args:
            hypothesis: Research hypothesis persisted in the run.
            motivation: Existing motivation metadata and optional reference.
            reviewed: Whether to add an existing conclusion and next step.

        Returns:
            Identifier assigned to the new run.
        """
        experiment = Experiment("graph-mamba", self.base)
        with experiment.run(hypothesis, motivation) as run:
            run.log_params({"hidden_dim": 128})
            run.log_metric("auc", 0.91, step=2)
            run.collect({"example_id": "node-42", "target": 1, "prediction": 0.91})
        run_id = run.run_id
        if reviewed:
            data = experiment.storage.read_run(run_id)
            data["review"] = {
                "status": "reviewed",
                "conclusion": "Validation AUC improved.",
                "next_step": "Repeat with another seed.",
            }
            experiment.storage.write_run(run_id, data)
        return run_id

    def test_empty_project_generates_expected_pages(self) -> None:
        """Generate an empty static site without creating the source store."""
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        result = self.adapter.export(snapshot, self.output)
        self.assertEqual(result, self.output)
        self.assertEqual(
            {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()},
            {"index.html", "style.css", "runs", "examples/index.html"} - {"runs"},
        )
        index = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn("Research overview", index)
        self.assertIn("Total runs", index)
        self.assertIn("No runs have been recorded", index)
        self.assertFalse(self.base.exists())

    def test_one_run_page_contains_metrics_params_and_examples(self) -> None:
        """Render the run's hypothesis, metrics, parameters, and compact sample."""
        self._create_run("H1 improves AUC", Motivation(type="new"), reviewed=True)
        self.adapter.export(ResearchSnapshotBuilder(self.base, describe_examples=False).build(), self.output)
        run_page = (self.output / "runs" / "run-001.html").read_text(encoding="utf-8")
        self.assertIn("H1 improves AUC", run_page)
        self.assertIn("Validation AUC improved.", run_page)
        self.assertIn("Repeat with another seed.", run_page)
        self.assertIn("hidden_dim", run_page)
        self.assertIn("auc", run_page)
        self.assertIn("0.91", run_page)
        self.assertIn("node-42", run_page)
        self.assertIn("../style.css", run_page)

    def test_multiple_runs_render_history_and_relations(self) -> None:
        """Link every run from the index and retain motivation references."""
        first = self._create_run("H1 baseline", Motivation(type="new"), reviewed=True)
        self._create_run("H2 follow-up", Motivation(type="previous_run", reference=first))
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        index = self.adapter.render_index(snapshot)
        self.assertIn('href="runs/run-001.html"', index)
        self.assertIn('href="runs/run-002.html"', index)
        self.assertIn("H1 baseline", index)
        self.assertIn("H2 follow-up", index)
        run_page = (self.adapter.export(snapshot, self.output) / "runs" / "run-002.html").read_text(encoding="utf-8")
        self.assertIn("previous_run (reference: run-001)", run_page)

    def test_failed_and_aborted_runs_are_visible(self) -> None:
        """Expose failed and aborted execution statuses on the overview."""
        experiment = Experiment("graph-mamba", self.base)
        aborted = experiment.run("H-aborted", Motivation(type="new"))
        aborted.abort()
        failed = experiment.run("H-failed", Motivation(type="new"))
        failed.fail(RuntimeError("training failed"))
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        index = self.adapter.render_index(snapshot)
        self.assertIn("Failed", index)
        self.assertIn("Aborted", index)
        self.assertIn("failed", index)
        self.assertIn("aborted", index)

    def test_examples_catalogue_and_consistency_findings_are_rendered(self) -> None:
        """Publish compact examples and consistency findings in static HTML."""
        self._create_run("H without review", Motivation(type="new"))
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        snapshot.findings.append(ConsistencyIssue("run-001", "test_warning", "sample warning", "warning"))
        self.adapter.export(snapshot, self.output)
        index = (self.output / "index.html").read_text(encoding="utf-8")
        examples = (self.output / "examples" / "index.html").read_text(encoding="utf-8")
        self.assertIn("test_warning", index)
        self.assertIn("sample warning", index)
        self.assertIn("node-42", examples)
        self.assertIn("compact diagnostic records", examples)
        self.assertNotIn("<script", examples.lower())

    def test_example_descriptions_are_rendered_as_readable_text(self) -> None:
        """Show provider descriptions before compact diagnostic JSON."""
        self._create_run("H1", Motivation(type="new"))

        class Provider:
            def describe(self, example_id: str) -> str:
                return f"Graph node {example_id}: high-degree user"

            def get(self, example_id: str):
                return {"id": example_id}

        snapshot = ResearchSnapshotBuilder(
            self.base, example_provider=Provider(), describe_examples=True
        ).build()
        self.adapter.export(snapshot, self.output)
        examples = (self.output / "examples" / "index.html").read_text(encoding="utf-8")
        run_page = (self.output / "runs" / "run-001.html").read_text(encoding="utf-8")
        self.assertIn("Description:", examples)
        self.assertIn("Graph node node-42: high-degree user", examples)
        self.assertIn("Graph node node-42: high-degree user", run_page)

    def test_dynamic_content_is_html_escaped(self) -> None:
        """Escape untrusted snapshot strings rather than treating them as markup."""
        self._create_run("H1 <script>alert('x')</script>", Motivation(type="new"))
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        index = self.adapter.render_index(snapshot)
        self.assertNotIn("<script>alert('x')</script>", index)
        self.assertIn("&lt;script&gt;", index)

    def test_export_does_not_modify_source_and_refuses_existing_output(self) -> None:
        """Preserve all research source bytes and avoid implicit overwrite."""
        self._create_run("H1", Motivation(type="new"), reviewed=True)
        source_files = [path for path in self.base.rglob("*") if path.is_file()]
        before = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in source_files}
        snapshot = ResearchSnapshotBuilder(self.base, describe_examples=False).build()
        self.adapter.export(snapshot, self.output)
        after = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in source_files}
        self.assertEqual(before, after)
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            self.adapter.export(snapshot, self.output)


if __name__ == "__main__":
    unittest.main()
