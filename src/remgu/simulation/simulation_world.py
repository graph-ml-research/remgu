# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Common contract for worlds used by controlled simulations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SimulationWorld(ABC):
    """Base interface shared by graph, text, user-history, and future worlds.

    A world owns domain data; renderers decide how that data is displayed. The
    shared methods let generic simulation tools inspect, summarize, and copy a
    world without assuming that it is a graph.
    """

    @abstractmethod
    def validate(self) -> None:
        """Validate the world's internal data and raise ``ValueError`` if invalid."""

    @abstractmethod
    def copy(self) -> "SimulationWorld":
        """Return an independent copy suitable for a simulation intervention."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the world."""

    @abstractmethod
    def summary(self) -> str:
        """Return a short, human-readable summary of the world."""

    @abstractmethod
    def to_text(self) -> str:
        """Return a bounded, human-readable text representation of the world."""
