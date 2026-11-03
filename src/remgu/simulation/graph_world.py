# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Lightweight graph-world data structure."""
from __future__ import annotations

from collections import deque
from typing import Iterable, Mapping

from remgu.simulation.simulation_world import SimulationWorld


class GraphWorld(SimulationWorld):
    """Represent an undirected graph, node features and community assignments."""

    def __init__(self, adjacency: Mapping[int, Iterable[int]],
                 features: Mapping[int, float], communities: Mapping[int, int],
                 critical_bridge: tuple[int, int] | None = None) -> None:
        """Build a validated graph world from adjacency and node metadata.

        Args:
            adjacency: Mapping from node ID to adjacent node IDs.
            features: Numeric feature for each node.
            communities: Community ID for each node.
            critical_bridge: Optional edge expected to connect two communities.
        """
        self.adjacency = {int(node): set(neighbors) for node, neighbors in adjacency.items()}
        self.features = {int(node): float(value) for node, value in features.items()}
        self.communities = {int(node): int(value) for node, value in communities.items()}
        self.critical_bridge = tuple(critical_bridge) if critical_bridge is not None else None
        self.validate()

    @property
    def node_ids(self) -> tuple[int, ...]:
        """Return node IDs in deterministic sorted order."""
        return tuple(sorted(self.adjacency))

    @property
    def edges(self) -> tuple[tuple[int, int], ...]:
        """Return each undirected edge exactly once in sorted order."""
        return tuple(sorted((node, neighbor) for node, neighbors in self.adjacency.items()
                            for neighbor in neighbors if node < neighbor))

    def validate(self) -> None:
        """Raise ``ValueError`` when graph metadata or undirected edges are inconsistent."""
        nodes = set(self.adjacency)
        if set(self.features) != nodes or set(self.communities) != nodes:
            raise ValueError("features and communities must cover exactly the graph nodes")
        for node, neighbors in self.adjacency.items():
            if node in neighbors:
                raise ValueError("self-loops are not supported")
            if not neighbors.issubset(nodes):
                raise ValueError(f"node {node} references an unknown neighbor")
            for neighbor in neighbors:
                if node not in self.adjacency[neighbor]:
                    raise ValueError("adjacency must describe an undirected graph")
        if self.critical_bridge is not None:
            left, right = self.critical_bridge
            if left not in nodes or right not in nodes:
                raise ValueError("critical_bridge endpoints must exist in the graph")

    def has_edge(self, left: int, right: int) -> bool:
        """Return whether an undirected edge exists."""
        return right in self.adjacency.get(left, set())

    def reachable(self, start: int, target: int) -> bool:
        """Return whether target is reachable from start using breadth-first search."""
        if start not in self.adjacency or target not in self.adjacency:
            return False
        pending = deque([start])
        visited = {start}
        while pending:
            current = pending.popleft()
            if current == target:
                return True
            for neighbor in self.adjacency[current] - visited:
                visited.add(neighbor)
                pending.append(neighbor)
        return False

    def copy(self) -> "GraphWorld":
        """Return an independent copy of the graph world."""
        return GraphWorld(self.adjacency, self.features, self.communities, self.critical_bridge)

    def to_text(self, max_nodes: int = 30) -> str:
        """Return a compact terminal representation of nodes and edges.

        Args:
            max_nodes: Maximum number of nodes to list before reporting truncation.
        """
        if max_nodes < 1:
            raise ValueError("max_nodes must be positive")
        selected = self.node_ids[:max_nodes]
        lines = ["Nodes:"]
        for node in selected:
            lines.append(f"  {node}: community={self.communities[node]}, feature={self.features[node]:g}")
        if len(self.node_ids) > max_nodes:
            lines.append(f"  ... truncated {len(self.node_ids) - max_nodes} node(s)")
        selected_set = set(selected)
        selected_edges = [(left, right) for left, right in self.edges
                          if left in selected_set and right in selected_set]
        lines.append("Edges:")
        lines.extend(f"  {left} -- {right}" for left, right in selected_edges)
        if len(selected_edges) < len(self.edges):
            lines.append(f"  ... {len(self.edges) - len(selected_edges)} edge(s) omitted")
        return "\n".join(lines)

    def to_ascii(self, max_nodes: int = 30) -> str:
        """Backward-compatible alias for :meth:`to_text`."""
        return self.to_text(max_nodes=max_nodes)

    def summary(self) -> str:
        """Return a compact description shared by generic world viewers."""
        communities = len(set(self.communities.values()))
        return f"GraphWorld: {len(self.node_ids)} nodes, {len(self.edges)} edges, {communities} communities"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation of the graph world."""
        return {"adjacency": {str(node): sorted(neighbors) for node, neighbors in sorted(self.adjacency.items())},
                "features": {str(node): self.features[node] for node in sorted(self.features)},
                "communities": {str(node): self.communities[node] for node in sorted(self.communities)},
                "critical_bridge": list(self.critical_bridge) if self.critical_bridge is not None else None}
