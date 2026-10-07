# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Research motivation value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Motivation:
    """Describe why a research run was started and, optionally, its source run."""

    type: str
    """Canonical motivation kind, for example ``new`` or ``previous_run``."""

    reference: str | None = None
    """Identifier of the referenced run or src object, if applicable."""
