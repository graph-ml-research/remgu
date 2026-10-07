# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Compatibility facade for the src consistency service."""
from .consistency_report import ConsistencyReport
from remgu.consistency.research_checker import ResearchChecker


class Consistency:
    """Compatibility facade exposing the consistency service as an object."""

    def __init__(self, checker: ResearchChecker) -> None:
        """Create a consistency facade.

        Args:
            checker: Read-only checker that performs the actual analysis.
        """
        self.checker = checker
        """Underlying src consistency checker."""

    def check(self) -> ConsistencyReport:
        """Run consistency analysis and return its report."""
        return self.checker.check()
