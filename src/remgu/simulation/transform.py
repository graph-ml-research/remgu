# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Base contract for reproducible dataset and online-batch transforms."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Any
from remgu.simulation.random_source import RandomSource


class Transform(ABC):
    """Transform one record without requiring a particular ML framework."""

    supported_modes = ("dataset", "batch")

    @abstractmethod
    def apply(self, record: Mapping[str, Any], random_source: RandomSource) -> dict[str, Any]:
        """Return a transformed copy of one record using an explicit random source."""
