# -*- coding: utf8 -*-
from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Execution, Motivation, ResearchMetadata, Review
from .run import Run
from .storage import FileStorage


__author__ = 'Mstislav Maslennikov'


class Experiment:
    """Small facade for creating persistent research runs."""

    def __init__(self, experiment_id: str, base_path: str | Path = ".research"):
        self.experiment_id = experiment_id
        self.storage = FileStorage(base_path)
        self.storage.initialize()

    def run(
        self,
        hypothesis: str | None = None,
        motivation: Mapping[str, Any] | Motivation | None = None,
    ) -> Run:
        """Open the active research run, or create a new one programmatically.

        With no arguments, the active run created by ``research new`` is
        continued.  This keeps run IDs and research metadata out of student
        code.  Supplying both ``hypothesis`` and ``motivation`` retains the
        programmatic run-creation API.
        """
        if hypothesis is None and motivation is None:
            return self._active_run()
        if hypothesis is None or motivation is None:
            raise ValueError(
                "hypothesis and motivation must be provided together, "
                "or both omitted to continue the active run"
            )
        return self._create_run(hypothesis, motivation)

    def _active_run(self) -> Run:
        run_id = self.storage.get_active()
        if run_id is None:
            raise RuntimeError("No active research run. Run `research new` first.")

        run = self._load_run(run_id)
        if run.execution.status != "running":
            self.storage.clear_active(run_id)
            raise RuntimeError(
                f"Active research run is not running: {run_id} "
                f"({run.execution.status})"
            )
        return run

    def _create_run(
        self,
        hypothesis: str,
        motivation: Mapping[str, Any] | Motivation,
    ) -> Run:
        active = self.storage.get_active()
        if active is not None:
            raise RuntimeError(f"Another run is already active: {active}")

        motivation_model = self._make_motivation(motivation)
        run_id = self.storage.next_run_id()
        run = Run(
            run_id=run_id,
            research=ResearchMetadata(
                hypothesis=hypothesis,
                motivation=motivation_model,
            ),
            storage=self.storage,
            path=self.storage.run_path(run_id),
            execution=Execution(status="running"),
            review=Review(),
        )

        self.storage.set_active(run_id)
        try:
            run.start()
        except Exception:
            self.storage.clear_active(run_id)
            raise
        return run

    def _load_run(self, run_id: str) -> Run:
        data = self.storage.read_run(run_id)
        if not data:
            raise RuntimeError(f"Active run not found: {run_id}")
        try:
            research_data = data["research"]
            motivation_data = research_data["motivation"]
            execution_data = data["execution"]
            review_data = data["review"]

            motivation = Motivation(
                type=str(motivation_data["type"]),
                reference=(
                    str(motivation_data["reference"])
                    if motivation_data.get("reference") is not None
                    else None
                ),
            )

            def parse_time(value: Any) -> datetime | None:
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

            execution = Execution(
                status=str(execution_data["status"]),
                started_at=parse_time(execution_data.get("started_at")),
                finished_at=parse_time(execution_data.get("finished_at")),
                error=execution_data.get("error"),
            )
            review = Review(
                status=str(review_data.get("status", "needs_review")),
                conclusion=review_data.get("conclusion"),
                next_step=review_data.get("next_step"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid run.yaml for {run_id}: {exc}") from exc

        return Run(
            run_id=run_id,
            research=ResearchMetadata(
                hypothesis=str(research_data["hypothesis"]),
                motivation=motivation,
            ),
            storage=self.storage,
            path=self.storage.run_path(run_id),
            execution=execution,
            review=review,
        )

    @staticmethod
    def _make_motivation(
        motivation: Mapping[str, Any] | Motivation,
    ) -> Motivation:
        if isinstance(motivation, Motivation):
            return motivation
        if "type" not in motivation:
            raise ValueError("motivation must contain 'type'")
        return Motivation(
            type=str(motivation["type"]),
            reference=(
                str(motivation["reference"])
                if motivation.get("reference") is not None
                else None
            ),
        )
