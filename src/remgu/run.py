# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Persistent execution object for one research run."""
from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from remgu.models.execution import Execution
from remgu.models.research_metadata import ResearchMetadata
from remgu.models.review import Review
from .file_storage import FileStorage


class Run:
    """Represent one concrete execution and its research artifacts."""

    TERMINAL_STATUSES = {"completed", "failed", "aborted"}
    """Execution states in which a run can no longer accept artifacts."""

    def __init__(self, run_id: str, research: ResearchMetadata, storage: FileStorage,
                 path: Path, execution: Execution, review: Review) -> None:
        """Create a run object bound to persistent storage.

        Args:
            run_id: Stable identifier of the run.
            research: Hypothesis and motivation metadata.
            storage: Storage service used to persist the run.
            path: Directory containing this run's artifacts.
            execution: Current execution lifecycle state.
            review: Current scientific review state.
        """
        self.run_id = run_id
        """Stable identifier of this run."""
        self.research = research
        """Research hypothesis and motivation metadata."""
        self.storage = storage
        """Persistence service used by the run."""
        self.path = path
        """Filesystem directory containing this run's files."""
        self.execution = execution
        """Execution lifecycle state."""
        self.review = review
        """Human review lifecycle state."""

    @property
    def started_at(self) -> datetime | None:
        """Return the execution start timestamp."""
        return self.execution.started_at

    @property
    def finished_at(self) -> datetime | None:
        """Return the execution finish timestamp."""
        return self.execution.finished_at

    @property
    def status(self) -> str:
        """Return the current execution status."""
        return self.execution.status

    @property
    def params_path(self) -> Path:
        """Return the path of the YAML parameters artifact."""
        return self.path / "params.yaml"

    @property
    def metrics_path(self) -> Path:
        """Return the path of the CSV metrics artifact."""
        return self.path / "metrics.csv"

    @property
    def samples_path(self) -> Path:
        """Return the path of the JSON Lines sample artifact."""
        return self.path / "samples.jsonl"

    def start(self) -> None:
        """Persist the run as started and require the ``running`` state."""
        if self.execution.status != "running":
            raise RuntimeError("A run can only be started from the running state")
        if self.execution.started_at is None:
            self.execution.started_at = self.storage.utc_now()
        self.save()

    def complete(self) -> None:
        """Finish successful execution and clear its active pointer."""
        self._finish("completed")

    def fail(self, exc: BaseException) -> None:
        """Record an exception and finish the run as failed.

        Args:
            exc: Exception that caused execution to fail.
        """
        self.execution.error = {"type": type(exc).__name__, "message": str(exc)}
        self._finish("failed")

    def abort(self) -> None:
        """Finish the run as intentionally aborted."""
        self._finish("aborted")

    def save(self) -> None:
        """Persist current research, execution and review metadata."""
        self.storage.write_run(self.run_id, self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Return metadata in the structure persisted to ``run.yaml``."""
        return {"run_id": self.run_id, "research": self.research,
                "execution": self.execution, "review": self.review}

    def log_params(self, params: Mapping[str, Any]) -> None:
        """Merge research-relevant parameters into ``params.yaml``.

        Args:
            params: Parameter mapping whose keys replace existing values.
        """
        self._ensure_running()
        self.path.mkdir(parents=True, exist_ok=True)
        current = self.storage.read_yaml_file(self.params_path) or {}
        if not isinstance(current, dict):
            raise ValueError("params.yaml must contain a mapping")
        current.update(dict(params))
        self.storage.write_yaml_file(self.params_path, current)

    def log_metric(self, name: str, value: Any, step: int | None = None) -> None:
        """Append one metric record to ``metrics.csv``.

        Args:
            name: Metric name.
            value: Metric value to persist.
            step: Optional training or evaluation step associated with the value.
        """
        self._ensure_running()
        self._append_metrics([(name, value, step)])

    def log_metrics(self, metrics: Mapping[str, Any], step: int | None = None) -> None:
        """Append multiple metrics associated with one optional step.

        Args:
            metrics: Mapping from metric names to values.
            step: Optional common step for all supplied metrics.
        """
        self._ensure_running()
        self._append_metrics([(name, value, step) for name, value in metrics.items()])

    def collect(self, record: Mapping[str, Any]) -> None:
        """Append one compact JSON-serializable diagnostic record.

        Args:
            record: Mapping containing the compact information needed to identify or inspect a sample.
        """
        self._ensure_running()
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            encoded = json.dumps(dict(record), ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise TypeError("record must be JSON-serializable") from exc
        with self.samples_path.open("a", encoding="utf-8") as file:
            file.write(encoded + "\n")

    def get_sample(self, example_id: str, provider: Any) -> Any:
        """Resolve an example identifier through an external provider without persisting it.

        Args:
            example_id: Compact identifier stored or referenced by src diagnostics.
            provider: Object implementing the example-provider interface.
        """
        if not example_id:
            raise ValueError("example_id must not be empty")
        return provider.get(example_id)

    def __enter__(self) -> "Run":
        """Return this run for context-manager based execution."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                  exc_value: BaseException | None,
                  traceback: Any) -> bool:
        """Finalize execution on context-manager exit.

        Args:
            exc_type: Exception class raised inside the context, if any.
            exc_value: Exception instance raised inside the context, if any.
            traceback: Python traceback object associated with the exception, if any.
        """
        if exc_value is not None:
            self.fail(exc_value)
            return False
        if self.status == "running":
            self.complete()
        return False

    def _finish(self, status: str) -> None:
        """Transition a running execution to a terminal status.

        Args:
            status: Terminal execution status to assign.
        """
        if self.execution.status != "running":
            raise RuntimeError(f"Cannot finish run from state: {self.execution.status}")
        self.execution.status = status
        self.execution.finished_at = self.storage.utc_now()
        self.save()
        self.storage.clear_active(self.run_id)

    def _ensure_running(self) -> None:
        """Reject artifact writes after execution has become terminal."""
        if self.status != "running":
            raise RuntimeError(f"Cannot modify run artifacts from state: {self.status}")

    def _append_metrics(self, records: list[tuple[str, Any, int | None]]) -> None:
        """Append metric records and create the CSV header when necessary.

        Args:
            records: Ordered metric tuples containing name, value and optional step.
        """
        self.path.mkdir(parents=True, exist_ok=True)
        file_exists = self.metrics_path.exists()
        with self.metrics_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["step", "metric_name", "metric_value"])
            for name, value, step in records:
                writer.writerow([step if step is not None else "", name, value])
