# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Serializable result of a simulation run."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SimulationResult:
    """Capture configuration, seed, metrics, checks and execution status."""

    experiment_id: str
    config: dict[str, Any]
    seed: int
    world: dict[str, Any]
    task: dict[str, Any]
    predictions: dict[int, int] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    checks: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    error: dict[str, str] | None = None
    duration_seconds: float | None = None
    note: str | None = None
    resource_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible result with integer mapping keys normalized to strings."""
        data = asdict(self)
        data["predictions"] = {str(key): value for key, value in self.predictions.items()}
        return data
