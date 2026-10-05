# -*- coding: utf-8 -*-
"""Tests for ResearchChecker and its report models."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from research import FileStorage, ResearchChecker


class TestResearchChecker(unittest.TestCase):
    """Verify read-only consistency analysis of persisted runs."""

    def setUp(self) -> None:
        """Create an isolated storage directory."""
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self._temporary_directory.name) / ".research"
        self.storage = FileStorage(self.base)

    def tearDown(self) -> None:
        """Remove the isolated storage directory."""
        self._temporary_directory.cleanup()

    def write_run(self, run_id: str, data: dict[str, Any]) -> None:
        """Write a synthetic run fixture.

        Args:
            run_id: Identifier of the synthetic run.
            data: Run YAML mapping used as fixture input.
        """
        path = self.base / "runs" / run_id
        path.mkdir(parents=True, exist_ok=True)
        (path / "run.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def base_run(self, hypothesis: str = "H1", motivation: dict[str, Any] | None = None,
                 status: str = "completed", conclusion: str | None = None,
                 next_step: str | None = None) -> dict[str, Any]:
        """Build a minimal valid run fixture.

        Args:
            hypothesis: Hypothesis text placed in the fixture.
            motivation: Motivation mapping, defaulting to a new run motivation.
            status: Execution status stored in the fixture.
            conclusion: Optional review conclusion.
            next_step: Optional review next step.
        """
        return {"run_id": "run-001", "research": {"hypothesis": hypothesis,
                "motivation": motivation or {"type": "new", "reference": None}},
                "execution": {"status": status},
                "review": {"status": "reviewed" if conclusion else "needs_review",
                           "conclusion": conclusion, "next_step": next_step}}

    def test_check_reports_completed_and_hypothesis_runs(self) -> None:
        """Count completed runs and runs with hypotheses."""
        self.write_run("run-001", self.base_run(conclusion="supported", next_step="H2"))
        self.write_run("run-002", self.base_run(hypothesis="H2", status="failed"))
        report = ResearchChecker(self.storage).check()
        self.assertEqual(report.completed_runs, ["run-001"])
        self.assertEqual(report.runs_with_hypotheses, ["run-001", "run-002"])
        self.assertEqual(report.issues, [])

    def test_check_flags_weak_motivation_and_missing_conclusion(self) -> None:
        """Report incomplete previous-run motivation and conclusion."""
        self.write_run("run-001", self.base_run(motivation={"type": "previous_run"}))
        codes = {issue.code for issue in ResearchChecker(self.storage).check().issues}
        self.assertIn("weak_motivation", codes)
        self.assertIn("missing_conclusion", codes)

    def test_check_handles_failed_and_aborted_runs_without_requiring_conclusion(self) -> None:
        """Do not require conclusions for failed or aborted executions."""
        self.write_run("run-001", self.base_run(status="failed"))
        self.write_run("run-002", self.base_run(status="aborted"))
        report = ResearchChecker(self.storage).check()
        self.assertEqual(report.completed_runs, [])
        self.assertFalse(any(issue.code == "missing_conclusion" for issue in report.issues))

    def test_check_detects_broken_previous_run_reference(self) -> None:
        """Detect references to nonexistent previous runs."""
        self.write_run("run-001", self.base_run(motivation={"type": "previous_run", "reference": "run-999"}, conclusion="done", next_step="next"))
        self.assertTrue(any(issue.code == "broken_motivation_reference" for issue in ResearchChecker(self.storage).check().issues))

    def test_check_is_read_only(self) -> None:
        """Guarantee that consistency checking does not modify run YAML."""
        data = self.base_run()
        self.write_run("run-001", data)
        path = self.base / "runs" / "run-001" / "run.yaml"
        before = path.read_bytes()
        ResearchChecker(self.storage).check()
        self.assertEqual(path.read_bytes(), before)

