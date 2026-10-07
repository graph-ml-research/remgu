# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Domain-agnostic top-k example selector."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from heapq import heappush, heappushpop
from typing import Any

from remgu.example.candidate import Candidate

ScoreFunction = Callable[[Mapping[str, Any]], float]
"""Callable that extracts a numeric selection score from a record."""


class TopKSelector:
    """Keep the k records with the largest or smallest diagnostic score."""

    def __init__(self, k: int, *, key: ScoreFunction | None = None,
                 largest: bool = True, name: str | None = None) -> None:
        """Create an incremental top-k selector.

        Args:
            k: Maximum number of records retained.
            key: Optional score function applied to each record.
            largest: Whether larger scores are considered better.
            name: Optional stable selector name used by ``ExampleSelector``.
        """
        if k <= 0:
            raise ValueError("k must be positive")
        if key is not None and not callable(key):
            raise TypeError("key must be callable")
        self.k = k
        """Maximum number of candidates retained."""
        self.key = key
        """Optional score function."""
        self.largest = largest
        """Whether higher scores are preferred."""
        self.name = name
        """Optional selector name used in merged diagnostics."""
        self._heap: list[tuple[float, int, Candidate]] = []
        """Heap containing the currently retained candidates."""
        self._counter = 0
        """Monotonic insertion counter used for deterministic ties."""

    def consider(self, record: Mapping[str, Any], priority: float | None = None,
                 *, score: float | None = None) -> None:
        """Consider one record for retention.

        Args:
            record: Candidate diagnostic record.
            priority: Backwards-compatible explicit score argument.
            score: Preferred explicit score argument when no score function is configured.
        """
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        if priority is not None and score is not None:
            raise TypeError("use either priority or score, not both")
        if priority is not None:
            value = priority
        elif score is not None:
            value = score
        elif self.key is not None:
            value = self.key(record)
        else:
            raise TypeError("provide priority, score, or a key")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError("selection score must be numeric") from exc
        candidate = Candidate(value, self._counter, dict(record))
        self._counter += 1
        heap_score = value if self.largest else -value
        item = (heap_score, candidate.order, candidate)
        if len(self._heap) < self.k:
            heappush(self._heap, item)
        elif item[:2] > self._heap[0][:2]:
            heappushpop(self._heap, item)

    def records(self) -> list[dict[str, Any]]:
        """Return retained records in best-first order."""
        candidates = [item[2] for item in self._heap]
        candidates.sort(key=lambda item: (item.score, item.order), reverse=self.largest)
        return [item.record for item in candidates]

    def __len__(self) -> int:
        """Return the number of records currently retained."""
        return len(self._heap)
