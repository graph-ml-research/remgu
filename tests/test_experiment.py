# -*- coding: utf-8 -*-
"""Tests for the Experiment facade."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from remgu.experiment import Experiment
from remgu.models.motivation import Motivation
from remgu.research_cli import main


class TestExperiment(unittest.TestCase):
    """Verify creation, continuation and validation of src runs."""

    def setUp(self) -> None:
        """Create an isolated temporary src directory for the test."""
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base_path = Path(self._temporary_directory.name) / ".src"

    def tearDown(self) -> None:
        """Remove the isolated src directory after the test."""
        self._temporary_directory.cleanup()

    def test_custom_base_path(self) -> None:
        """Persist a run under a caller-selected storage directory."""
        base = Path(self._temporary_directory.name) / "src-data"
        experiment = Experiment("graph-mamba", base)
        with experiment.run("H1", Motivation(type="literature_citation", reference="paper-123")):
            pass
        self.assertTrue((base / "runs" / "run-001" / "run.yaml").exists())

    def test_run_without_arguments_continues_active_cli_run(self) -> None:
        """Resume the active run created by the CLI without creating another run."""
        self.assertEqual(main(("--base-path", str(self.base_path), "new", "--hypothesis", "H1",
                               "--motivation-type", "previous_run", "--reference", "run-002")), 0)
        experiment = Experiment("graph-mamba", self.base_path)
        with experiment.run() as run:
            self.assertEqual(run.run_id, "run-001")
            self.assertEqual(run.research.hypothesis, "H1")
            self.assertEqual(run.research.motivation.type, "previous_run")
            self.assertEqual(run.research.motivation.reference, "run-002")
        data = yaml.safe_load((self.base_path / "runs" / "run-001" / "run.yaml").read_text())
        self.assertEqual(data["execution"]["status"], "completed")
        self.assertEqual(data["review"]["status"], "needs_review")
        self.assertFalse((self.base_path / "active").exists())

    def test_run_without_arguments_requires_active_run(self) -> None:
        """Reject continuation when there is no active CLI-created run."""
        with self.assertRaisesRegex(RuntimeError, "src new"):
            Experiment("graph-mamba", self.base_path).run()

    def test_run_without_arguments_does_not_create_second_run(self) -> None:
        """Ensure a completed context-managed run is not silently recreated."""
        experiment = Experiment("graph-mamba", self.base_path)
        with experiment.run("H1", Motivation(type="new")) as first:
            self.assertEqual(first.run_id, "run-001")
        with self.assertRaisesRegex(RuntimeError, "src new"):
            experiment.run()
        self.assertFalse((self.base_path / "runs" / "run-002").exists())

    def test_run_rejects_partial_programmatic_arguments(self) -> None:
        """Require hypothesis and motivation to be supplied together."""
        experiment = Experiment("graph-mamba", self.base_path)
        with self.assertRaisesRegex(ValueError, "provided together"):
            experiment.run("H1")
        with self.assertRaisesRegex(ValueError, "provided together"):
            experiment.run(motivation=Motivation(type="new"))
