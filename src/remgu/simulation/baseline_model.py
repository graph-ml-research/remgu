# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""A dependency-free baseline for graph dependency experiments."""
from __future__ import annotations

from remgu.simulation.graph_world import GraphWorld


class GraphReachabilityBaseline:
    """Predict a target label from the source feature only when it is reachable."""

    def __init__(self, source_node: int | None = None, unreachable_prediction: int = 0) -> None:
        """Create the baseline.

        Args:
            source_node: Signal node; defaults to the final node in the world.
            unreachable_prediction: Binary prediction used when the signal is unreachable.
        """
        if unreachable_prediction not in (0, 1):
            raise ValueError("unreachable_prediction must be 0 or 1")
        self.source_node = source_node
        self.unreachable_prediction = unreachable_prediction

    def predict(self, world: GraphWorld, target_nodes: tuple[int, ...] | list[int]) -> dict[int, int]:
        """Predict labels for target nodes based on graph reachability to the signal node."""
        if not world.node_ids:
            raise ValueError("world must contain at least one node")
        source = self.source_node if self.source_node is not None else world.node_ids[-1]
        if source not in world.features:
            raise ValueError(f"unknown source node: {source}")
        signal = int(world.features[source] >= 0.5)
        return {target: signal if world.reachable(target, source) else self.unreachable_prediction
                for target in target_nodes}
