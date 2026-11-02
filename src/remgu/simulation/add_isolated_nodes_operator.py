# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Add isolated nodes without altering existing nodes."""
from remgu.simulation.graph_operator import GraphOperator
from remgu.simulation.graph_world import GraphWorld


class AddIsolatedNodesOperator(GraphOperator):
    """Add a configurable number of isolated nodes to a graph world."""

    def __init__(self, count: int, feature: float = 0.0, community: int = -1) -> None:
        """Configure the number and metadata of the new nodes.

        Args:
            count: Non-negative number of nodes to add.
            feature: Numeric feature assigned to each new node.
            community: Community ID assigned to each new node.
        """
        if count < 0:
            raise ValueError("count must be non-negative")
        self.count = count
        self.feature = float(feature)
        self.community = int(community)

    def apply(self, world: GraphWorld) -> GraphWorld:
        """Return a copied world with new isolated nodes appended after current IDs."""
        adjacency = {node: set(neighbors) for node, neighbors in world.adjacency.items()}
        features = dict(world.features)
        communities = dict(world.communities)
        next_node = max(adjacency, default=-1) + 1
        for node in range(next_node, next_node + self.count):
            adjacency[node] = set()
            features[node] = self.feature
            communities[node] = self.community
        return GraphWorld(adjacency, features, communities, world.critical_bridge)
