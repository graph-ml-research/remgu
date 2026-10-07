# -*- coding: utf-8 -*-
"""Tests for the Run execution object."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import yaml

from remgu.example.example_provider import ExampleProvider
from remgu.experiment import Experiment


class TestRun(unittest.TestCase):
    """Verify run lifecycle, persistence and artifact logging."""

    def setUp(self) -> None:
        """Create an isolated temporary src directory."""
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base_path = Path(self._temporary_directory.name) / ".src"
        self.experiment = Experiment("graph-mamba", self.base_path)

    def tearDown(self) -> None:
        """Remove the temporary src directory."""
        self._temporary_directory.cleanup()

    def make_experiment(self) -> Experiment:
        """Return the fixture's experiment facade."""
        return self.experiment

    def read_run(self, run_id: str = "run-001") -> dict[str, Any]:
        """Load persisted run metadata for assertions.

        Args:
            run_id: Identifier of the run to read.
        """
        path = self.base_path / "runs" / run_id / "run.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_create_run_and_persist_yaml(self) -> None:
        """Persist initial src, execution and review metadata."""
        run = self.experiment.run("Увеличение hidden_dim до 512 улучшит NDCG@20.", {"type": "new"})
        data = self.read_run()
        self.assertEqual(data["run_id"], "run-001")
        self.assertEqual(data["src"]["hypothesis"], "Увеличение hidden_dim до 512 улучшит NDCG@20.")
        self.assertEqual(data["src"]["motivation"], {"type": "new", "reference": None})
        self.assertEqual(data["execution"]["status"], "running")
        self.assertIsNotNone(data["execution"]["started_at"])
        self.assertIsNone(data["execution"]["finished_at"])
        self.assertEqual(data["review"], {"status": "needs_review", "conclusion": None, "next_step": None})
        self.assertEqual((self.base_path / "active").read_text().strip(), run.run_id)

    def test_successful_context_manager_cleans_active(self) -> None:
        """Complete a successful context-managed run and clear its active pointer."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            self.assertEqual(run.status, "running")
        data = self.read_run()
        self.assertEqual(data["execution"]["status"], "completed")
        self.assertIsNotNone(data["execution"]["finished_at"])
        self.assertFalse((self.base_path / "active").exists())

    def test_exception_marks_failed_and_reraises(self) -> None:
        """Persist an exception as failure metadata and propagate it."""
        with self.assertRaisesRegex(RuntimeError, "CUDA out of memory"):
            with self.experiment.run("H1", {"type": "new"}) as run:
                raise RuntimeError("CUDA out of memory")
        data = self.read_run()
        self.assertEqual(data["execution"]["status"], "failed")
        self.assertEqual(data["execution"]["error"], {"type": "RuntimeError", "message": "CUDA out of memory"})
        self.assertFalse((self.base_path / "active").exists())

    def test_abort(self) -> None:
        """Allow an active run to be explicitly aborted."""
        run = self.experiment.run("H1", {"type": "new"})
        run.abort()
        self.assertEqual(self.read_run()["execution"]["status"], "aborted")
        self.assertFalse((self.base_path / "active").exists())

    def test_second_active_run_is_forbidden(self) -> None:
        """Reject concurrent active runs and allow a second run afterwards."""
        first = self.experiment.run("H1", {"type": "new"})
        with self.assertRaisesRegex(RuntimeError, "already active"):
            self.experiment.run("H2", {"type": "new"})
        first.abort()
        second = self.experiment.run("H2", {"type": "previous_run", "reference": first.run_id})
        self.assertEqual(second.run_id, "run-002")
        second.abort()

    def test_run_ids_are_sequential(self) -> None:
        """Allocate sequential run identifiers."""
        for expected in ("run-001", "run-002", "run-003"):
            run = self.experiment.run("H", {"type": "new"})
            self.assertEqual(run.run_id, expected)
            run.abort()

    def test_reference_is_optional_for_new_motivation(self) -> None:
        """Allow a new motivation without a reference."""
        with self.experiment.run("H", {"type": "new"}):
            pass
        self.assertIsNone(self.read_run()["src"]["motivation"]["reference"])

    def test_log_params(self) -> None:
        """Write src parameters to params.yaml."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_params({"hidden_dim": 512, "batch_size": 64})
        self.assertEqual(yaml.safe_load((run.params_path).read_text()), {"hidden_dim": 512, "batch_size": 64})

    def test_log_params_updates_existing_keys(self) -> None:
        """Replace an existing parameter without losing other parameters."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_params({"hidden_dim": 256, "batch_size": 64})
            run.log_params({"hidden_dim": 512})
        self.assertEqual(yaml.safe_load(run.params_path.read_text()), {"hidden_dim": 512, "batch_size": 64})

    def test_log_metric_creates_metrics_csv(self) -> None:
        """Create a metrics CSV with the standard header."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_metric("loss", 0.5)
        self.assertEqual(run.metrics_path.read_text().splitlines(), ["step,metric_name,metric_value", ",loss,0.5"])

    def test_log_metrics_with_step(self) -> None:
        """Write several metrics sharing one explicit step."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_metrics({"loss": 0.5, "ndcg20": 0.428}, step=10)
        self.assertEqual(run.metrics_path.read_text().splitlines(), ["step,metric_name,metric_value", "10,loss,0.5", "10,ndcg20,0.428"])

    def test_multiple_metric_records(self) -> None:
        """Append multiple metric records in insertion order."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_metric("loss", 0.82, step=1)
            run.log_metric("loss", 0.51, step=10)
            run.log_metrics({"ndcg20": 0.428}, step=10)
        self.assertEqual(run.metrics_path.read_text().splitlines(), ["step,metric_name,metric_value", "1,loss,0.82", "10,loss,0.51", "10,ndcg20,0.428"])

    def test_collect_writes_jsonl(self) -> None:
        """Append compact diagnostic records as JSON Lines."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.collect({"example_id": "node-42", "target": 1, "prediction": 0})
            run.collect({"example_id": "node-73", "target": 0, "prediction": 1})
        self.assertEqual(run.samples_path.read_text().splitlines(), ['{"example_id":"node-42","target":1,"prediction":0}', '{"example_id":"node-73","target":0,"prediction":1}'])

    def test_artifacts_are_not_in_run_yaml(self) -> None:
        """Keep parameter, metric and sample artifacts separate from run metadata."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            run.log_params({"hidden_dim": 512})
            run.log_metric("loss", 0.5)
            run.collect({"example_id": "node-42", "prediction": 0})
        data = self.read_run()
        self.assertNotIn("params", data)
        self.assertNotIn("metrics", data)
        self.assertNotIn("samples", data)

    def test_artifacts_survive_failed_run(self) -> None:
        """Preserve already-written artifacts when execution fails."""
        with self.assertRaisesRegex(RuntimeError, "boom"):
            with self.experiment.run("H1", {"type": "new"}) as run:
                run.log_params({"hidden_dim": 512})
                run.log_metric("loss", 0.5)
                run.collect({"example_id": "node-42", "prediction": 0})
                raise RuntimeError("boom")
        self.assertTrue(run.params_path.exists())
        self.assertTrue(run.metrics_path.exists())
        self.assertTrue(run.samples_path.exists())
        self.assertEqual(self.read_run()["execution"]["status"], "failed")

    def test_artifact_methods_reject_terminal_run(self) -> None:
        """Reject artifact writes after successful completion."""
        run = self.experiment.run("H1", {"type": "new"})
        run.complete()
        with self.assertRaisesRegex(RuntimeError, "completed"):
            run.log_metric("loss", 0.5)
        with self.assertRaisesRegex(RuntimeError, "completed"):
            run.log_params({"hidden_dim": 512})
        with self.assertRaisesRegex(RuntimeError, "completed"):
            run.collect({"example_id": "node-42"})

    def test_get_sample_resolves_example_without_writing_it(self) -> None:
        """Resolve an example through a provider without creating samples.jsonl."""
        provider = MagicMock(spec=ExampleProvider)
        provider.get.return_value = {"node": 42, "neighbors": [1, 2]}
        with self.experiment.run("H1", {"type": "new"}) as run:
            sample = run.get_sample("node-42", provider)
        self.assertEqual(sample, {"node": 42, "neighbors": [1, 2]})
        self.assertFalse(run.samples_path.exists())

    def test_get_sample_rejects_empty_id(self) -> None:
        """Reject empty example identifiers."""
        with self.experiment.run("H1", {"type": "new"}) as run:
            with self.assertRaisesRegex(ValueError, "example_id"):
                run.get_sample("", MagicMock(spec=ExampleProvider))
