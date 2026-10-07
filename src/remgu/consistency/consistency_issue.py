# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""One issue reported by src consistency analysis."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsistencyIssue:
    """Describe one consistency problem in persisted src data."""

    run_id: str
    """Run identifier where the problem was detected."""

    code: str
    """Stable machine-readable issue code."""

    message: str
    """Human-readable explanation of the issue."""

    severity: str = "warning"
    """Issue severity, normally ``warning`` or ``error``."""
