# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Public facade for simulation experiments."""
from __future__ import annotations

from collections.abc import Iterable
from remgu.simulation.graph_operator import GraphOperator
from remgu.simulation.simulation_config import SimulationConfig
from remgu.simulation.simulation_result import SimulationResult
from remgu.simulation.simulation_runner import SimulationRunner


class SimulationExperiment:
    """Expose a small, explicit Python API for running a simulation configuration."""

    def __init__(self, config: SimulationConfig, runner: SimulationRunner | None = None) -> None:
        """Create an experiment facade.

        Args:
            config: Validated settings for the experiment.
            runner: Optional runner; a default dependency-free runner is created when omitted.
        """
        self.config = config
        self.runner = runner or SimulationRunner()

    def run(self, operators: Iterable[GraphOperator] = ()) -> SimulationResult:
        """Run the configured experiment with the requested ordered transformations."""
        return self.runner.run(self.config, operators)
