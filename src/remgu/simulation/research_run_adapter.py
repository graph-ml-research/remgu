# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Bridge a completed simulation result to an existing ReMgu research run."""
from __future__ import annotations

from remgu.run import Run
from remgu.simulation.simulation_result import SimulationResult


class ResearchRunAdapter:
    """Write a simulation result into an already-running ReMgu ``Run``."""

    def record(self, run: Run, result: SimulationResult) -> None:
        """Persist simulation metadata, metrics and a compact diagnostic sample.

        The adapter does not create or finalize the run and does not alter the `.research` schema.
        """
        if run.status != "running":
            raise RuntimeError("simulation results can only be recorded in a running research run")
        run.log_params({"simulation": {"experiment_id": result.experiment_id, "seed": result.seed,
                                       "status": result.status, "config": result.config}})
        if result.metrics:
            run.log_metrics(result.metrics)
        run.collect({"type": "simulation_result", "experiment_id": result.experiment_id,
                     "status": result.status, "checks": result.checks, "error": result.error})
