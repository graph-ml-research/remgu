# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Execution lifecycle model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Execution:
    """Store execution status and timestamps for one research run."""

    status: str
    """Execution lifecycle state: ``running``, ``completed``, ``failed`` or ``aborted``."""

    started_at: datetime | None = None
    """UTC timestamp at which execution started, when known."""

    finished_at: datetime | None = None
    """UTC timestamp at which execution reached a terminal state, when known."""

    error: dict[str, str] | None = None
    """Serialized exception type and message for a failed execution, if any."""
