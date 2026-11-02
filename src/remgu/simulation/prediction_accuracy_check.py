# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Evaluate prediction accuracy for a simulation task."""
from typing import Mapping
from remgu.simulation.graph_world import GraphWorld
from remgu.simulation.simulation_check import SimulationCheck


class PredictionAccuracyCheck(SimulationCheck):
    """Report accuracy over the supplied target labels."""

    def evaluate(self, world: GraphWorld, labels: Mapping[int, int],
                 predictions: Mapping[int, int]) -> dict[str, object]:
        """Calculate accuracy and return a structured check result."""
        del world
        if not labels:
            return {"name": type(self).__name__, "status": "not_evaluated", "details": "No target labels"}
        missing = set(labels) - set(predictions)
        if missing:
            return {"name": type(self).__name__, "status": "failed", "details": f"Missing predictions for {sorted(missing)}"}
        correct = sum(int(labels[node] == predictions[node]) for node in labels)
        return {"name": type(self).__name__, "status": "evaluated", "details": "Predictions evaluated; quality is represented by the accuracy metric",
                "metrics": {"correct": correct, "count": len(labels), "accuracy": correct / len(labels)}}
