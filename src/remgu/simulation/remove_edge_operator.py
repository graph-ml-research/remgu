# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Remove an edge as a controlled graph intervention."""
from remgu.simulation.graph_operator import GraphOperator
from remgu.simulation.graph_world import GraphWorld


class RemoveEdgeOperator(GraphOperator):
    """Remove one undirected edge while retaining its critical-edge metadata."""

    def __init__(self, edge: tuple[int, int]) -> None:
        """Create an edge-removal operator.

        Args:
            edge: Endpoint IDs of the undirected edge to remove.
        """
        self.edge = tuple(edge)

    def apply(self, world: GraphWorld) -> GraphWorld:
        """Return a copied world with the selected edge removed."""
        left, right = self.edge
        if not world.has_edge(left, right):
            raise ValueError(f"edge does not exist: {self.edge}")
        adjacency = {node: set(neighbors) for node, neighbors in world.adjacency.items()}
        adjacency[left].remove(right)
        adjacency[right].remove(left)
        return GraphWorld(adjacency, world.features, world.communities, world.critical_bridge)
