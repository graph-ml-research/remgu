# -*- coding: utf8 -*-
from __future__ import annotations
import csv, json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Execution, ResearchMetadata, Review
from .storage import FileStorage, utc_now

__author__ = 'Mstislav Maslennikov'


TERMINAL_STATUSES = {"completed", "failed", "aborted"}


@dataclass
class Run:
    run_id: str
    research: ResearchMetadata
    storage: FileStorage
    path: Path
    execution: Execution
    review: Review

    @property
    def started_at(self) -> datetime | None:
        return self.execution.started_at

    @property
    def finished_at(self) -> datetime | None:
        return self.execution.finished_at

    @property
    def status(self) -> str:
        return self.execution.status

    @property
    def params_path(self) -> Path:
        return self.path / "params.yaml"

    @property
    def metrics_path(self) -> Path:
        return self.path / "metrics.csv"

    @property
    def samples_path(self) -> Path:
        return self.path / "samples.jsonl"

    def start(self) -> None:
        if self.execution.status != "running":
            raise RuntimeError("A run can only be started from the running state")
        if self.execution.started_at is None:
            self.execution.started_at = utc_now()
        self.save()

    def complete(self) -> None:
        self._finish("completed")

    def fail(self, exc: BaseException) -> None:
        self.execution.error = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        self._finish("failed")

    def abort(self) -> None:
        self._finish("aborted")

    def _finish(self, status: str) -> None:
        if self.execution.status != "running":
            raise RuntimeError(f"Cannot finish run from state: {self.execution.status}")
        self.execution.status = status
        self.execution.finished_at = utc_now()
        self.save()
        self.storage.clear_active(self.run_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "research": self.research,
            "execution": self.execution,
            "review": self.review,
        }

    def save(self) -> None:
        self.storage.write_run(self.run_id, self.to_dict())

    def __enter__(self) -> "Run":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_value is not None:
            self.fail(exc_value)
            return False
        if self.status == "running":
            self.complete()
        return False

    def log_params(self, params: Mapping[str, Any]) -> None:
        """Persist run parameters in a human-readable YAML file.

        Calling this method again updates/replaces the supplied parameter keys.
        Parameters are intentionally kept outside run.yaml because they are
        artifacts of the run rather than research/execution metadata.
        """
        self._ensure_running()
        self.path.mkdir(parents=True, exist_ok=True)
        current = self.storage.read_yaml_file(self.params_path) or {}
        if not isinstance(current, dict):
            raise ValueError("params.yaml must contain a mapping")
        current.update(dict(params))
        self.storage.write_yaml_file(self.params_path, current)

    def log_metric(self, name: str, value: Any, step: int | None = None) -> None:
        """Append one metric record to metrics.csv."""
        self._ensure_running()
        self._append_metrics([(name, value, step)])

    def log_metrics(
        self,
        metrics: Mapping[str, Any],
        step: int | None = None,
    ) -> None:
        """Append several metrics for the same optional step."""
        self._ensure_running()
        self._append_metrics(
            [(name, value, step) for name, value in metrics.items()]
        )

    def collect(self, record: Mapping[str, Any]) -> None:
        """Append one compact JSON-serializable record to samples.jsonl."""
        self._ensure_running()
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")

        self.path.mkdir(parents=True, exist_ok=True)
        try:
            encoded = json.dumps(
                dict(record),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise TypeError("record must be JSON-serializable") from exc

        with self.samples_path.open("a", encoding="utf-8") as file:
            file.write(encoded + "\n")

    def _ensure_running(self) -> None:
        if self.status != "running":
            raise RuntimeError(
                f"Cannot modify run artifacts from state: {self.status}"
            )

    def _append_metrics(
        self,
        records: list[tuple[str, Any, int | None]],
    ) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        file_exists = self.metrics_path.exists()
        with self.metrics_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["step", "metric_name", "metric_value"])
            for name, value, step in records:
                writer.writerow([step if step is not None else "", name, value])

