# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Validated configuration for a reproducible simulation run."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SimulationConfig:
    """Store explicit settings for a small graph-dependency experiment.

    Args:
        experiment_id: Stable human-readable identifier for this simulation.
        hypothesis: Research claim the run is intended to probe.
        seed: Seed for the reproducible random stream.
        community_sizes: Positive node counts for the two generated communities.
        edge_probability: Probability of extra within-community edges beyond a connectivity chain.
        critical_bridge: Whether to add the single designated inter-community bridge.
        source_node: Optional node whose feature determines target labels.
        target_nodes: Optional explicit target-node IDs.
        metadata: Additional JSON-compatible research metadata.
        param_types: Optional UI classification for parameters (hot, structural, or view).
    """

    experiment_id: str = "graph-dependency"
    hypothesis: str = "Removing the critical bridge reduces prediction accuracy when the signal is positive."
    seed: int = 0
    community_sizes: tuple[int, int] = (5, 5)
    edge_probability: float = 0.6
    critical_bridge: bool = True
    source_node: int | None = None
    target_nodes: tuple[int, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    param_types: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration fields immediately after initialization."""
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty")
        if len(self.community_sizes) != 2 or any(size < 1 for size in self.community_sizes):
            raise ValueError("community_sizes must contain two positive integers")
        if not 0.0 <= self.edge_probability <= 1.0:
            raise ValueError("edge_probability must be between 0 and 1")
        invalid_types = {name: kind for name, kind in self.param_types.items()
                         if kind not in {"hot", "structural", "view"}}
        if invalid_types:
            raise ValueError(f"invalid parameter types: {invalid_types}")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible copy of the configuration."""
        return asdict(self)
