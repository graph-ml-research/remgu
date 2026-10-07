# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Internal candidate model used by example selection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Candidate:
    """Represent one record retained by a top-k selector's heap."""

    score: float
    """Numeric diagnostic score used for ranking the record."""

    order: int
    """Insertion order used to make equal-score selection deterministic."""

    record: dict[str, Any]
    """Copy of the selected record."""
