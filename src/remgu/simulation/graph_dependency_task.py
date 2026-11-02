# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Task whose labels depend on a signal in another graph community."""
from __future__ import annotations

from remgu.simulation.graph_world import GraphWorld


class GraphDependencyTask:
    """Define binary labels for target nodes using a designated source node's feature."""

    def __init__(self, source_node: int | None = None, target_nodes: tuple[int, ...] | None = None) -> None:
        """Configure the signal source and target nodes.

        Args:
            source_node: Node whose feature determines all target labels; defaults to the last node.
            target_nodes: Nodes to evaluate; defaults to nodes in the first community.
        """
        self.source_node = source_node
        self.target_nodes = target_nodes

    def labels(self, world: GraphWorld) -> dict[int, int]:
        """Return ground-truth labels independently of model predictions."""
        if not world.node_ids:
            raise ValueError("world must contain at least one node")
        source = self.source_node if self.source_node is not None else world.node_ids[-1]
        if source not in world.features:
            raise ValueError(f"unknown source node: {source}")
        targets = self.target_nodes
        if targets is None:
            source_community = world.communities[source]
            targets = tuple(node for node in world.node_ids if world.communities[node] != source_community)
        if not targets:
            raise ValueError("task must contain at least one target node")
        if any(target not in world.features for target in targets):
            raise ValueError("all target nodes must exist in the world")
        label = int(world.features[source] >= 0.5)
        return {target: label for target in targets}

    def to_dict(self, world: GraphWorld) -> dict[str, object]:
        """Return task settings and target labels for reproducible result metadata."""
        labels = self.labels(world)
        return {"type": type(self).__name__, "source_node": self.source_node if self.source_node is not None else world.node_ids[-1],
                "target_nodes": list(labels), "labels": labels}
