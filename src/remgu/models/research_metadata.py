# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Research metadata model."""
from __future__ import annotations

from dataclasses import dataclass

from .motivation import Motivation


@dataclass
class ResearchMetadata:
    """Store the hypothesis and motivation belonging to one research run."""

    hypothesis: str
    """Research hypothesis tested by the run."""

    motivation: Motivation
    """Reason that led to the hypothesis or run."""
