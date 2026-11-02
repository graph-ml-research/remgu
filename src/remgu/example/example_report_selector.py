# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Bounded TopKSelector-based selection for report and dashboard examples."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import math
from typing import Any

from remgu.example.top_k_selector import TopKSelector


class ExampleReportSelector:
    """Select a bounded, diagnostic-first set of examples without mutating source records."""

    def __init__(self, limit: int = 100) -> None:
        """Set the maximum candidate count retained for HTML pagination."""
        if limit < 1:
            raise ValueError("limit must be positive")
        self.limit = limit

    def select(self, records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Return highest-priority errors, using known score fields or stable input order."""
        selector = TopKSelector(self.limit, largest=True)
        for index, source in enumerate(records):
            record = dict(source)
            if record.get("correct") is False or record.get("is_error") is True or record.get("error") is True:
                priority = 1.0
            elif record.get("correct") is True or record.get("is_error") is False or record.get("error") is False:
                priority = 0.0
            else:
                priority = 0.0
            numeric_score = None
            for key in ("error_score", "loss", "difficulty", "confidence", "score"):
                value = record.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    candidate_score = float(value)
                    if math.isfinite(candidate_score):
                        numeric_score = math.tanh(candidate_score)
                        break
            priority = priority * 2.0 + (numeric_score if numeric_score is not None else 0.0)
            # Earlier records win stable ties; TopKSelector retains deterministic insertion order.
            record.setdefault("_remgu_source_order", index)
            selector.consider(record, score=priority)
        selected = selector.records()
        for record in selected:
            record.pop("_remgu_source_order", None)
        return selected
