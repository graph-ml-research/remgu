# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""High-level facade for creating and resuming research runs."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from remgu.models.execution import Execution
from remgu.models.motivation import Motivation
from remgu.models.research_metadata import ResearchMetadata
from remgu.models.review import Review
from .run import Run
from .file_storage import FileStorage


class Experiment:
    """Provide the student-facing API for persistent src execution."""

    def __init__(self, experiment_id: str, base_path: str | Path = ".research") -> None:
        """Create an experiment facade over a file-backed research store.

        Args:
            experiment_id: Human-readable identifier of the experiment or project.
            base_path: Root directory used for persistent research state.
        """
        self.experiment_id = experiment_id
        """Human-readable experiment identifier."""
        self.storage = FileStorage(base_path)
        """Persistence service used to create and resume runs."""
        self.storage.initialize()

    def run(self, hypothesis: str | None = None,
            motivation: Mapping[str, Any] | Motivation | None = None) -> Run:
        """Resume the active run or create a new programmatic run.

        Args:
            hypothesis: Hypothesis for a new run; omit it when resuming an active run.
            motivation: Motivation for a new run; omit it when resuming an active run.
        """
        if hypothesis is None and motivation is None:
            return self._active_run()
        if hypothesis is None or motivation is None:
            raise ValueError("hypothesis and motivation must be provided together, or both omitted to continue the active run")
        return self._create_run(hypothesis, motivation)

    def _active_run(self) -> Run:
        """Load and validate the run referenced by the active pointer."""
        run_id = self.storage.get_active()
        if run_id is None:
            raise RuntimeError("No active research run. Run `src new` first.")
        run = self._load_run(run_id)
        if run.execution.status != "running":
            self.storage.clear_active(run_id)
            raise RuntimeError(f"Active research run is not running: {run_id} ({run.execution.status})")
        return run

    def _create_run(self, hypothesis: str,
                    motivation: Mapping[str, Any] | Motivation) -> Run:
        """Create, activate and persist a new running execution.

        Args:
            hypothesis: Research hypothesis associated with the new run.
            motivation: Motivation object or mapping describing why it was created.
        """
        active = self.storage.get_active()
        if active is not None:
            raise RuntimeError(f"Another run is already active: {active}")
        motivation_model = self._make_motivation(motivation)
        run_id = self.storage.next_run_id()
        run = Run(run_id=run_id,
                  research=ResearchMetadata(hypothesis=hypothesis, motivation=motivation_model),
                  storage=self.storage, path=self.storage.run_path(run_id),
                  execution=Execution(status="running"), review=Review())
        self.storage.set_active(run_id)
        try:
            run.start()
        except Exception:
            self.storage.clear_active(run_id)
            raise
        return run

    def _load_run(self, run_id: str) -> Run:
        """Deserialize one persisted run into its domain object.

        Args:
            run_id: Identifier of the run to load.
        """
        data = self.storage.read_run(run_id)
        if not data:
            raise RuntimeError(f"Active run not found: {run_id}")
        try:
            research_data = data["research"]
            motivation_data = research_data["motivation"]
            execution_data = data["execution"]
            review_data = data["review"]
            motivation = Motivation(type=str(motivation_data["type"]),
                                     reference=str(motivation_data["reference"]) if motivation_data.get("reference") is not None else None)
            execution = Execution(status=str(execution_data["status"]),
                                  started_at=self._parse_time(execution_data.get("started_at")),
                                  finished_at=self._parse_time(execution_data.get("finished_at")),
                                  error=execution_data.get("error"))
            review = Review(status=str(review_data.get("status", "needs_review")),
                            conclusion=review_data.get("conclusion"), next_step=review_data.get("next_step"))
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid run.yaml for {run_id}: {exc}") from exc
        return Run(run_id=run_id,
                   research=ResearchMetadata(hypothesis=str(research_data["hypothesis"]), motivation=motivation),
                   storage=self.storage, path=self.storage.run_path(run_id),
                   execution=execution, review=review)

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        """Convert persisted time data to a timezone-aware datetime.

        Args:
            value: YAML value representing an ISO timestamp or ``None``.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    @staticmethod
    def _make_motivation(motivation: Mapping[str, Any] | Motivation) -> Motivation:
        """Normalize a motivation mapping or object into ``Motivation``.

        Args:
            motivation: Motivation value object or mapping containing ``type`` and optional ``reference``.
        """
        if isinstance(motivation, Motivation):
            return motivation
        if "type" not in motivation:
            raise ValueError("motivation must contain 'type'")
        return Motivation(type=str(motivation["type"]),
                          reference=str(motivation["reference"]) if motivation.get("reference") is not None else None)
