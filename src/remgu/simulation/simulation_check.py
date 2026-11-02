# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Base contract for structured simulation checks."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping
from remgu.simulation.graph_world import GraphWorld


class SimulationCheck(ABC):
    """Define a check that reports a structured, serializable outcome."""

    @abstractmethod
    def evaluate(self, world: GraphWorld, labels: Mapping[int, int],
                 predictions: Mapping[int, int]) -> dict[str, object]:
        """Evaluate a property and return status and explanatory details."""
