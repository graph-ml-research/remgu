# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Read-only consistency analysis service."""
from __future__ import annotations

from typing import Any

from remgu.consistency.consistency_issue import ConsistencyIssue
from remgu.consistency.consistency_report import ConsistencyReport
from remgu.file_storage import FileStorage


class ResearchChecker:
    """Analyze persisted runs without modifying research state."""

    def __init__(self, storage: FileStorage) -> None:
        """Create a checker bound to a src storage service.

        Args:
            storage: File-backed src storage to inspect.
        """
        self.storage = storage
        """Storage service whose run files are inspected."""

    def check(self) -> ConsistencyReport:
        """Scan all persisted runs and return a consistency report."""
        report = ConsistencyReport()
        run_ids = self.storage.list_run_ids()
        known_ids = set(run_ids)
        for run_id in run_ids:
            self._check_run(run_id, known_ids, report)
        return report

    def _check_run(self, run_id: str, known_ids: set[str], report: ConsistencyReport) -> None:
        """Analyze one run and append findings to an existing report.

        Args:
            run_id: Identifier of the run being checked.
            known_ids: All known run identifiers used to validate references.
            report: Mutable report receiving the findings.
        """
        path = self.storage.run_path(run_id) / "run.yaml"
        try:
            data = self.storage.read_yaml_file(path)
        except Exception as exc:
            report.issues.append(ConsistencyIssue(run_id, "invalid_yaml", f"cannot read run.yaml: {exc}", "error"))
            return
        if not isinstance(data, dict):
            report.issues.append(ConsistencyIssue(run_id, "invalid_structure", "run.yaml must contain a mapping", "error"))
            return
        research = self._section(data, "research", run_id, report)
        execution = self._section(data, "execution", run_id, report)
        review = self._section(data, "review", run_id, report)
        self._check_hypothesis(run_id, research, report)
        self._check_motivation(run_id, research, known_ids, report)
        self._check_execution(run_id, execution, review, report)
        self._check_review(run_id, execution, review, report)

    def _section(self, data: dict[str, Any], name: str, run_id: str, report: ConsistencyReport) -> dict[str, Any]:
        """Read a required top-level mapping and report malformed sections.

        Args:
            data: Parsed run YAML mapping.
            name: Section name expected in the run YAML document.
            run_id: Identifier of the run being checked.
            report: Report receiving a malformed-section issue when needed.
        """
        section = data.get(name)
        if not isinstance(section, dict):
            report.issues.append(ConsistencyIssue(run_id, f"missing_{name}", f"{name} section is missing or invalid", "error"))
            return {}
        return section

    def _check_hypothesis(self, run_id: str, research: dict[str, Any], report: ConsistencyReport) -> None:
        """Validate and count the run hypothesis."""
        hypothesis = research.get("hypothesis")
        if self._nonempty_text(hypothesis):
            report.runs_with_hypotheses.append(run_id)
        else:
            report.issues.append(ConsistencyIssue(run_id, "missing_hypothesis", "hypothesis is empty or missing"))

    def _check_motivation(self, run_id: str, research: dict[str, Any], known_ids: set[str], report: ConsistencyReport) -> None:
        """Validate motivation structure and previous-run references."""
        motivation = research.get("motivation")
        if not isinstance(motivation, dict):
            report.issues.append(ConsistencyIssue(run_id, "missing_motivation", "motivation is missing or invalid"))
            return
        motivation_type = motivation.get("type")
        reference = motivation.get("reference")
        if not self._nonempty_text(motivation_type):
            report.issues.append(ConsistencyIssue(run_id, "weak_motivation", "motivation type is empty"))
        elif motivation_type == "previous_run" and not self._nonempty_text(reference):
            report.issues.append(ConsistencyIssue(run_id, "weak_motivation", "previous_run motivation has no reference"))
        elif self._nonempty_text(reference) and reference not in known_ids:
            report.issues.append(ConsistencyIssue(run_id, "broken_motivation_reference", f"motivation references unknown run {reference}"))

    def _check_execution(self, run_id: str, execution: dict[str, Any], review: dict[str, Any], report: ConsistencyReport) -> None:
        """Validate execution status and require conclusions for completed runs."""
        status = execution.get("status")
        if status == "completed":
            report.completed_runs.append(run_id)
            if not self._nonempty_text(review.get("conclusion")):
                report.issues.append(ConsistencyIssue(run_id, "missing_conclusion", "completed run has no conclusion"))
        elif status not in {"running", "failed", "aborted", None}:
            report.issues.append(ConsistencyIssue(run_id, "invalid_execution_status", f"unknown execution status: {status}", "error"))

    def _check_review(self, run_id: str, execution: dict[str, Any], review: dict[str, Any], report: ConsistencyReport) -> None:
        """Validate review status and its relationship with execution."""
        status = review.get("status", "needs_review")
        if status not in {"needs_review", "reviewed"}:
            report.issues.append(ConsistencyIssue(run_id, "invalid_review_status", f"unknown review status: {status}", "error"))
        if status == "reviewed" and execution.get("status") != "completed":
            report.issues.append(ConsistencyIssue(run_id, "reviewed_noncompleted_run", "run is marked reviewed but execution is not completed"))
        if status == "reviewed" and not self._nonempty_text(review.get("next_step")):
            report.issues.append(ConsistencyIssue(run_id, "missing_next_step", "reviewed run has no next_step"))

    @staticmethod
    def _nonempty_text(value: Any) -> bool:
        """Return whether a value is a non-empty string.

        Args:
            value: Value being checked.
        """
        return isinstance(value, str) and bool(value.strip())
