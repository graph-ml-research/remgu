# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Base class for graph-world transformations."""
from __future__ import annotations
from abc import ABC, abstractmethod
from remgu.simulation.graph_world import GraphWorld


class GraphOperator(ABC):
    """Define the contract for an explicit graph-world transformation."""

    @abstractmethod
    def apply(self, world: GraphWorld) -> GraphWorld:
        """Return the transformed world without mutating the input."""
