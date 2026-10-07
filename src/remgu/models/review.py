# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Research review lifecycle model."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Review:
    """Store the human review state and scientific interpretation of a run."""

    status: str = "needs_review"
    """Review lifecycle state: ``needs_review`` or ``reviewed``."""

    conclusion: str | None = None
    """Human conclusion about the result, when the run has been reviewed."""

    next_step: str | None = None
    """Suggested next src action, when the run has been reviewed."""
