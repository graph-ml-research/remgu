from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .storage import FileStorage


@dataclass(frozen=True)
class ConsistencyIssue:
    run_id: str
    code: str
    message: str
    severity: str = "warning"


@dataclass
class ConsistencyReport:
    completed_runs: list[str] = field(default_factory=list)
    runs_with_hypotheses: list[str] = field(default_factory=list)
    issues: list[ConsistencyIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_consistency(storage: FileStorage) -> ConsistencyReport:
    """Read-only consistency analysis of all persisted run.yaml files.

    The checker deliberately reads raw YAML instead of constructing ``Run``
    objects: a consistency report should still be able to describe malformed
    or partially written runs without failing as a whole.
    """
    report = ConsistencyReport()
    run_ids = storage.list_run_ids()
    known_ids = set(run_ids)

    for run_id in run_ids:
        path = storage.run_path(run_id) / "run.yaml"
        try:
            data = storage.read_yaml_file(path)
        except Exception as exc:
            report.issues.append(
                ConsistencyIssue(
                    run_id,
                    "invalid_yaml",
                    f"cannot read run.yaml: {exc}",
                    "error",
                )
            )
            continue

        if not isinstance(data, dict):
            report.issues.append(
                ConsistencyIssue(run_id, "invalid_structure", "run.yaml must contain a mapping", "error")
            )
            continue

        research = data.get("research")
        execution = data.get("execution")
        review = data.get("review")

        if not isinstance(research, dict):
            report.issues.append(
                ConsistencyIssue(run_id, "missing_research", "research section is missing or invalid", "error")
            )
            research = {}
        if not isinstance(execution, dict):
            report.issues.append(
                ConsistencyIssue(run_id, "missing_execution", "execution section is missing or invalid", "error")
            )
            execution = {}
        if not isinstance(review, dict):
            report.issues.append(
                ConsistencyIssue(run_id, "missing_review", "review section is missing or invalid", "error")
            )
            review = {}

        hypothesis = research.get("hypothesis")
        if _nonempty_text(hypothesis):
            report.runs_with_hypotheses.append(run_id)
        else:
            report.issues.append(
                ConsistencyIssue(run_id, "missing_hypothesis", "hypothesis is empty or missing")
            )

        motivation = research.get("motivation")
        if not isinstance(motivation, dict):
            report.issues.append(
                ConsistencyIssue(run_id, "missing_motivation", "motivation is missing or invalid")
            )
        else:
            motivation_type = motivation.get("type")
            reference = motivation.get("reference")
            if not _nonempty_text(motivation_type):
                report.issues.append(
                    ConsistencyIssue(run_id, "weak_motivation", "motivation type is empty")
                )
            elif motivation_type == "previous_run" and not _nonempty_text(reference):
                report.issues.append(
                    ConsistencyIssue(
                        run_id,
                        "weak_motivation",
                        "previous_run motivation has no reference",
                    )
                )
            elif _nonempty_text(reference) and reference not in known_ids:
                report.issues.append(
                    ConsistencyIssue(
                        run_id,
                        "broken_motivation_reference",
                        f"motivation references unknown run {reference}",
                    )
                )

        execution_status = execution.get("status")
        if execution_status == "completed":
            report.completed_runs.append(run_id)
            if not _nonempty_text(review.get("conclusion")):
                report.issues.append(
                    ConsistencyIssue(run_id, "missing_conclusion", "completed run has no conclusion")
                )
        elif execution_status not in {"running", "failed", "aborted", None}:
            report.issues.append(
                ConsistencyIssue(
                    run_id,
                    "invalid_execution_status",
                    f"unknown execution status: {execution_status}",
                    "error",
                )
            )

        review_status = review.get("status", "needs_review")
        if review_status not in {"needs_review", "reviewed"}:
            report.issues.append(
                ConsistencyIssue(
                    run_id,
                    "invalid_review_status",
                    f"unknown review status: {review_status}",
                    "error",
                )
            )
        if review_status == "reviewed" and execution_status != "completed":
            report.issues.append(
                ConsistencyIssue(
                    run_id,
                    "reviewed_noncompleted_run",
                    "run is marked reviewed but execution is not completed",
                )
            )
        if review_status == "reviewed" and not _nonempty_text(review.get("next_step")):
            report.issues.append(
                ConsistencyIssue(run_id, "missing_next_step", "reviewed run has no next_step")
            )

    return report
