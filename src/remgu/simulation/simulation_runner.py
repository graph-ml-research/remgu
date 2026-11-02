# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Execute a deterministic graph-dependency simulation."""
from __future__ import annotations

from time import perf_counter
from typing import Iterable

from remgu.simulation.baseline_model import GraphReachabilityBaseline
from remgu.simulation.graph_dependency_task import GraphDependencyTask
from remgu.simulation.graph_operator import GraphOperator
from remgu.simulation.graph_world_generator import GraphWorldGenerator
from remgu.simulation.random_source import RandomSource
from remgu.simulation.simulation_check import SimulationCheck
from remgu.simulation.prediction_accuracy_check import PredictionAccuracyCheck
from remgu.simulation.simulation_config import SimulationConfig
from remgu.simulation.simulation_result import SimulationResult


class SimulationRunner:
    """Run graph generation, task labeling, optional transformations and evaluation."""

    def __init__(self, world_generator: GraphWorldGenerator | None = None,
                 checks: Iterable[SimulationCheck] | None = None) -> None:
        """Configure reusable generation and check components."""
        self.world_generator = world_generator or GraphWorldGenerator()
        self.checks = list(checks) if checks is not None else [PredictionAccuracyCheck()]

    def run(self, config: SimulationConfig, operators: Iterable[GraphOperator] = ()) -> SimulationResult:
        """Execute one run and return a structured result.

        Operators are applied in the supplied order. Labels are created from the original
        world before transformations, so operators can test whether information was lost.
        """
        started = perf_counter()
        # Import lazily: resource monitoring remains optional and does not load ML integrations.
        from remgu.visualization.resource_monitor import ResourceMonitor
        resource_monitor = ResourceMonitor()
        resource_monitor.sample()
        try:
            random_source = RandomSource(config.seed)
            original_world = self.world_generator.generate(
                random_source, config.community_sizes, config.edge_probability, config.critical_bridge)
            task = GraphDependencyTask(config.source_node, config.target_nodes)
            labels = task.labels(original_world)
            world = original_world
            applied_operators = []
            for operator in operators:
                world = operator.apply(world)
                applied_operators.append(type(operator).__name__)
            model = GraphReachabilityBaseline(config.source_node)
            predictions = model.predict(world, tuple(labels))
            check_results = [check.evaluate(world, labels, predictions) for check in self.checks]
            correct = sum(int(labels[node] == predictions.get(node, -1)) for node in labels)
            metrics = {"correct": correct, "count": len(labels), "accuracy": correct / len(labels) if labels else None,
                       "positive_count": sum(labels.values()),
                       "positive_accuracy": (sum(int(predictions.get(node, -1) == 1) for node in labels if labels[node] == 1)
                                              / sum(labels.values())) if sum(labels.values()) else None}
            result = SimulationResult(
                experiment_id=config.experiment_id,
                config={**config.to_dict(), "operators": applied_operators},
                seed=config.seed, world=world.to_dict(), task=task.to_dict(original_world),
                predictions=predictions, metrics=metrics, checks=check_results,
                duration_seconds=perf_counter() - started, resource_summary=resource_monitor.summary())
            return result
        except Exception as exc:
            return SimulationResult(experiment_id=config.experiment_id, config=config.to_dict(), seed=config.seed,
                                    world={}, task={}, status="failed",
                                    error={"type": type(exc).__name__, "message": str(exc)},
                                    duration_seconds=perf_counter() - started,
                                    resource_summary=resource_monitor.summary())
