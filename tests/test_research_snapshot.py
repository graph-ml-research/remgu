# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Tests for the in-memory research snapshot layer."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from remgu import ArchiveAdapter, Experiment, ResearchSnapshotBuilder
from remgu.models import Motivation


class TestResearchSnapshot(unittest.TestCase):
    """Verify snapshot construction, read-only behaviour and archive publication."""

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

    def test_snapshot_does_not_modify_source_files(self) -> None:
        """Ensure snapshot construction leaves source files byte-for-byte unchanged."""
        self._completed_run("H1", Motivation(type="new"))
        files = sorted(path for path in self.base.rglob("*") if path.is_file())
        before = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in files}
        ResearchSnapshotBuilder(self.base).build()
        after = {path.relative_to(self.base): hashlib.sha256(path.read_bytes()).digest() for path in files}
        self.assertEqual(before, after)


class TestArchiveAdapter(unittest.TestCase):
    """Verify self-contained ZIP publication from a research snapshot."""

    def setUp(self) -> None:
        """Create an isolated research store and output directory."""
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name) / ".research"
        self.output = Path(self.temp.name) / "research-archive.zip"

    def tearDown(self) -> None:
        """Remove temporary files."""
        self.temp.cleanup()

    def _make_run(self) -> None:
        """Create a completed run containing all optional publication artifacts."""
        experiment = Experiment("graph-mamba", self.base)
        with experiment.run("H1", Motivation(type="new")) as run:
            run.log_params({"lr": 0.001})
            run.log_metric("auc", 0.91, step=5)
            run.collect({"example_id": "node-42", "score": 0.91})
        data = experiment.storage.read_run(run.run_id)
        data["review"] = {"status": "reviewed", "conclusion": "Supported", "next_step": "H2"}
        experiment.storage.write_run(run.run_id, data)

    def test_empty_archive_contains_publication_files_only(self) -> None:
        """Publish an empty project without inventing run files."""
        snapshot = ResearchSnapshotBuilder(self.base).build()
        ArchiveAdapter(self.base).create(snapshot, self.output)
        with zipfile.ZipFile(self.output) as archive:
            names = archive.namelist()
        self.assertEqual(names, [
            "research-archive/README.md", "research-archive/report.md", "research-archive/research.yaml",
        ])

    def test_archive_contains_existing_artifacts_and_compact_examples(self) -> None:
        """Copy known run artifacts and publish serializable compact examples."""
        self._make_run()
        snapshot = ResearchSnapshotBuilder(self.base).build()
        ArchiveAdapter(self.base).create(snapshot, self.output)
        with zipfile.ZipFile(self.output) as archive:
            names = archive.namelist()
            self.assertIn("research-archive/README.md", names)
            self.assertIn("research-archive/report.md", names)
            self.assertIn("research-archive/research.yaml", names)
            self.assertIn("research-archive/runs/run-001/run.yaml", names)
            self.assertIn("research-archive/runs/run-001/params.yaml", names)
            self.assertIn("research-archive/runs/run-001/metrics.csv", names)
            self.assertIn("research-archive/runs/run-001/samples.jsonl", names)
            self.assertIn("research-archive/examples/node-42.json", names)
            report = archive.read("research-archive/report.md").decode("utf-8")
            self.assertIn("Supported", report)
            self.assertIn("auc", report)

    def test_archive_rejects_existing_output(self) -> None:
        """Never overwrite an existing archive implicitly."""
        self.output.write_bytes(b"existing")
        snapshot = ResearchSnapshotBuilder(self.base).build()
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            ArchiveAdapter(self.base).create(snapshot, self.output)
        self.assertEqual(self.output.read_bytes(), b"existing")

    def test_archive_does_not_change_source_data(self) -> None:
        """Ensure archive publication leaves source files unchanged."""
        self._make_run()
        files = sorted(path for path in self.base.rglob("*") if path.is_file())
        before = {path.relative_to(self.base): path.read_bytes() for path in files}
        snapshot = ResearchSnapshotBuilder(self.base).build()
        ArchiveAdapter(self.base).create(snapshot, self.output)
        after = {path.relative_to(self.base): path.read_bytes() for path in files}
        self.assertEqual(before, after)

    def test_archive_zip_metadata_is_deterministic(self) -> None:
        """Use fixed ZIP entry metadata so binary archive differences are minimized."""
        self._make_run()
        snapshot = ResearchSnapshotBuilder(self.base).build()
        first = Path(self.temp.name) / "one.zip"
        second = Path(self.temp.name) / "two.zip"
        ArchiveAdapter(self.base).create(snapshot, first)
        ArchiveAdapter(self.base).create(snapshot, second)
        with zipfile.ZipFile(first) as archive:
            first_metadata = [(info.filename, info.date_time) for info in archive.infolist()]
        with zipfile.ZipFile(second) as archive:
            second_metadata = [(info.filename, info.date_time) for info in archive.infolist()]
        self.assertEqual(first_metadata, second_metadata)
