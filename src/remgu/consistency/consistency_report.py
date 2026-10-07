# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Consistency-analysis report model."""
from __future__ import annotations

from dataclasses import dataclass, field

from .consistency_issue import ConsistencyIssue


@dataclass
class ConsistencyReport:
    """Aggregate completed runs, hypotheses and detected consistency issues."""

    completed_runs: list[str] = field(default_factory=list)
    """Identifiers of runs whose execution status is ``completed``."""

    runs_with_hypotheses: list[str] = field(default_factory=list)
    """Identifiers of runs containing a non-empty hypothesis."""

    issues: list[ConsistencyIssue] = field(default_factory=list)
    """Consistency problems discovered while scanning persisted runs."""

    @property
    def ok(self) -> bool:
        """Return whether the report contains no consistency issues."""
        return not self.issues
