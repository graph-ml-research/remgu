# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""In-memory research snapshot used by analysis and publication layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from remgu.example.example_provider import ExampleProvider

from remgu.consistency import ConsistencyIssue


@dataclass
class ResearchSnapshotSummary:
    """Aggregate execution and review counts for a research snapshot."""

    total_runs: int = 0
    """Total number of persisted runs."""
    completed: int = 0
    """Number of completed runs."""
    failed: int = 0
    """Number of failed runs."""
    aborted: int = 0
    """Number of aborted runs."""
    running: int = 0
    """Number of running runs."""
    reviewed: int = 0
    """Number of reviewed runs."""
    needs_review: int = 0
    """Number of runs awaiting review."""


@dataclass
class ResearchSnapshotRun:
    """Derived publication view of one persisted research run."""

    run_id: str
    """Persistent run identifier."""
    hypothesis: str
    """Research hypothesis."""
    motivation: dict[str, Any]
    """Existing motivation data, including an optional reference."""
    execution_status: str
    """Persisted execution lifecycle status."""
    review_status: str
    """Persisted review status."""
    started_at: datetime | None
    """Execution start timestamp, when available."""
    finished_at: datetime | None
    """Execution finish timestamp, when available."""
    conclusion: str | None
    """Existing review conclusion, when available."""
    next_step: str | None
    """Existing review next step, when available."""
    params: dict[str, Any] | None = None
    """Effective parameters loaded from params.yaml, when the file exists."""
    metrics: list[dict[str, Any]] = field(default_factory=list)
    """Metric rows loaded from metrics.csv, when the file exists."""
    samples: list[dict[str, Any]] = field(default_factory=list)
    """Compact diagnostic sample records loaded from samples.jsonl."""


@dataclass
class ResearchSnapshot:
    """Non-persistable derived representation of the current research history."""

    summary: ResearchSnapshotSummary
    """Aggregate execution and review counts."""
    runs: list[ResearchSnapshotRun]
    """Derived views of persisted runs."""
    relations: list[dict[str, str]] = field(default_factory=list)
    """Relations derived only from existing motivation references."""
    metrics: list[dict[str, Any]] = field(default_factory=list)
    """Flattened metric rows with their run identifiers."""
    samples: list[dict[str, Any]] = field(default_factory=list)
    """Flattened compact samples with their run identifiers."""
    findings: list[ConsistencyIssue] = field(default_factory=list)
    """Consistency findings produced by the read-only checker."""
    summary_text: str = ""
    """Short human-readable description of the snapshot."""

    @property
    def ok(self) -> bool:
        """Return whether consistency analysis found no issues."""
        return not self.findings


class ResearchSnapshotBuilder:
    """Build an in-memory snapshot from the existing .research store."""

    def __init__(
        self,
        base_path: str = ".research",
        example_provider: ExampleProvider | None = None,
        describe_examples: bool = False,
    ) -> None:
        """Create a snapshot builder for a research directory.

        Args:
            base_path: Root directory containing the persisted research data.
            example_provider: Optional domain-specific provider used to describe sample IDs.
            describe_examples: Whether to enrich snapshot samples with provider descriptions.
                Requires ``example_provider`` when enabled.
        """
        if describe_examples and example_provider is None:
            raise ValueError("describe_examples=True requires an example_provider")
        self.example_provider = example_provider
        self.describe_examples = describe_examples
        from remgu.file_storage import FileStorage
        from remgu.consistency import ResearchChecker

        self.storage = FileStorage(base_path)
        """Storage service used only for read access during snapshot construction."""
        self.checker = ResearchChecker(base_path)
        """Read-only consistency checker for the same research directory."""

    def build(self) -> ResearchSnapshot:
        """Build a snapshot without changing any persisted research files."""
        run_ids = self.storage.list_run_ids()
        findings_report = self.checker.check()
        runs: list[ResearchSnapshotRun] = []
        relations: list[dict[str, str]] = []
        metrics: list[dict[str, Any]] = []
        samples: list[dict[str, Any]] = []
        summary = ResearchSnapshotSummary(total_runs=len(run_ids))

        for run_id in run_ids:
            run = self._build_run(run_id)
            runs.append(run)
            self._update_summary(summary, run)
            reference = run.motivation.get("reference")
            if isinstance(reference, str) and reference:
                relations.append({"run_id": run_id, "reference": reference})
            for row in run.metrics:
                metrics.append({"run_id": run_id, **row})
            for sample in run.samples:
                samples.append({"run_id": run_id, **self._describe_sample(sample)})

        summary_text = self._summary_text(summary)
        return ResearchSnapshot(summary=summary, runs=runs, relations=relations,
                                metrics=metrics, samples=samples,
                                findings=findings_report.issues, summary_text=summary_text)

    def _describe_sample(self, sample: dict[str, Any]) -> dict[str, Any]:
        """Optionally attach a cheap, human-readable description to a sample.

        The enrichment exists only in the in-memory snapshot; persisted sample
        records are never modified. Provider errors propagate so a requested
        description export cannot silently omit descriptions.
        """
        enriched = dict(sample)
        if not self.describe_examples or self.example_provider is None:
            return enriched
        example_id = enriched.get("example_id")
        if not isinstance(example_id, str) or not example_id.strip():
            return enriched
        description = self.example_provider.describe(example_id)
        if isinstance(description, str) and description.strip():
            enriched["description"] = description.strip()
        return enriched

    def _build_run(self, run_id: str) -> ResearchSnapshotRun:
        """Build one derived run view from persisted run and artifact files.

        Args:
            run_id: Identifier of the run being read.
        """
        data = self.storage.read_run(run_id) or {}
        research = data.get("research") if isinstance(data, dict) else {}
        execution = data.get("execution") if isinstance(data, dict) else {}
        review = data.get("review") if isinstance(data, dict) else {}
        research = research if isinstance(research, dict) else {}
        execution = execution if isinstance(execution, dict) else {}
        review = review if isinstance(review, dict) else {}
        motivation = research.get("motivation")
        motivation = dict(motivation) if isinstance(motivation, dict) else {}
        return ResearchSnapshotRun(
            run_id=run_id,
            hypothesis=str(research.get("hypothesis", "")),
            motivation=motivation,
            execution_status=str(execution.get("status", "")),
            review_status=str(review.get("status", "needs_review")),
            started_at=self._parse_time(execution.get("started_at")),
            finished_at=self._parse_time(execution.get("finished_at")),
            conclusion=self._optional_text(review.get("conclusion")),
            next_step=self._optional_text(review.get("next_step")),
            params=self._read_params(run_id),
            metrics=self._read_metrics(run_id),
            samples=self._read_samples(run_id),
        )

    def _read_params(self, run_id: str) -> dict[str, Any] | None:
        """Read params.yaml when present and valid as a mapping.

        Args:
            run_id: Identifier of the run whose parameters are read.
        """
        value = self.storage.read_yaml_file(self.storage.run_path(run_id) / "params.yaml")
        return dict(value) if isinstance(value, dict) else None

    def _read_metrics(self, run_id: str) -> list[dict[str, Any]]:
        """Read metric CSV rows without modifying the source file.

        Args:
            run_id: Identifier of the run whose metrics are read.
        """
        import csv
        path = self.storage.run_path(run_id) / "metrics.csv"
        if not path.exists():
            return []
        with path.open(encoding="utf-8", newline="") as file:
            return [dict(row) for row in csv.DictReader(file)]

    def _read_samples(self, run_id: str) -> list[dict[str, Any]]:
        """Read compact JSON Lines sample records.

        Args:
            run_id: Identifier of the run whose samples are read.
        """
        import json
        path = self.storage.run_path(run_id) / "samples.jsonl"
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                value = json.loads(line)
                if isinstance(value, dict):
                    records.append(value)
        return records

    @staticmethod
    def _update_summary(summary: ResearchSnapshotSummary, run: ResearchSnapshotRun) -> None:
        """Update aggregate counts from one derived run view.

        Args:
            summary: Mutable summary being updated.
            run: Run whose execution and review statuses are counted.
        """
        if run.execution_status == "completed": summary.completed += 1
        elif run.execution_status == "failed": summary.failed += 1
        elif run.execution_status == "aborted": summary.aborted += 1
        elif run.execution_status == "running": summary.running += 1
        if run.review_status == "reviewed": summary.reviewed += 1
        else: summary.needs_review += 1

    @staticmethod
    def _summary_text(summary: ResearchSnapshotSummary) -> str:
        """Format the aggregate summary as one compact line.

        Args:
            summary: Snapshot summary to format.
        """
        return (f"Runs: {summary.total_runs}; completed: {summary.completed}; "
                f"failed: {summary.failed}; aborted: {summary.aborted}; "
                f"running: {summary.running}; reviewed: {summary.reviewed}; "
                f"needs_review: {summary.needs_review}")

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        """Convert persisted ISO timestamp data to datetime.

        Args:
            value: Timestamp value loaded from YAML.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        """Return non-empty textual values and otherwise ``None``.

        Args:
            value: Candidate text value.
        """
        if isinstance(value, str) and value.strip():
            return value
        return None
