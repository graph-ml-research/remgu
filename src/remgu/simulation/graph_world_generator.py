# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Generate reproducible small graphs with two communities."""
from __future__ import annotations

from remgu.simulation.graph_world import GraphWorld
from remgu.simulation.random_source import RandomSource


class GraphWorldGenerator:
    """Generate an undirected two-community graph with a controlled bridge."""

    def generate(self, random_source: RandomSource, community_sizes: tuple[int, int] = (5, 5),
                 edge_probability: float = 0.6, critical_bridge: bool = True) -> GraphWorld:
        """Generate a graph, numeric node features and community IDs.

        Args:
            random_source: Explicit random stream used for every random choice.
            community_sizes: Positive node counts for the left and right communities.
            edge_probability: Probability of each additional within-community edge beyond a connectivity chain.
            critical_bridge: If true, connect communities using exactly one bridge.
        """
        left_size, right_size = community_sizes
        if left_size < 1 or right_size < 1:
            raise ValueError("community sizes must both be positive")
        if not 0.0 <= edge_probability <= 1.0:
            raise ValueError("edge_probability must be between 0 and 1")
        sizes = (left_size, right_size)
        adjacency = {node: set() for node in range(sum(sizes))}
        communities = {node: 0 if node < left_size else 1 for node in adjacency}
        for community, size in enumerate(sizes):
            start = 0 if community == 0 else left_size
            # A chain guarantees each community is connected; extra edges are sampled separately.
            for offset in range(size - 1):
                left, right = start + offset, start + offset + 1
                adjacency[left].add(right)
                adjacency[right].add(left)
            for offset in range(size):
                left = start + offset
                for other_offset in range(offset + 2, size):
                    right = start + other_offset
                    if random_source.random() < edge_probability:
                        adjacency[left].add(right)
                        adjacency[right].add(left)
        bridge = None
        if critical_bridge:
            bridge = (left_size - 1, left_size)
            adjacency[bridge[0]].add(bridge[1])
            adjacency[bridge[1]].add(bridge[0])
        features = {node: float(random_source.randint(0, 1)) for node in adjacency}
        return GraphWorld(adjacency, features, communities, bridge)
