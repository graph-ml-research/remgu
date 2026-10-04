# -*- coding: utf8 -*-
from __future__ import annotations
from dataclasses import dataclass
from heapq import heappush, heappushpop
from typing import Any, Callable, Mapping

__author__ = 'Mstislav Maslennikov'

ScoreFunction = Callable[[Mapping[str, Any]], float]

@dataclass(frozen=True)
class _Candidate:
    score: float
    order: int
    record: dict[str, Any]


class TopKSelector:
    """Keep the k records with the largest (or smallest) score.

    The selector is domain-agnostic. Evaluation code computes diagnostic
    fields such as ``score``, ``baseline_gap`` or ``regression`` and supplies
    a score function. Multiple selectors can therefore be run over the same
    validation stream for different diagnostic criteria.

    ``priority=`` is retained as a small backwards-compatible convenience.
    """

    def __init__(
        self,
        k: int,
        *,
        key: ScoreFunction | None = None,
        largest: bool = True,
        name: str | None = None,
    ) -> None:
        if k <= 0:
            raise ValueError("k must be positive")
        if key is not None and not callable(key):
            raise TypeError("key must be callable")
        self.k = k
        self.key = key
        self.largest = largest
        self.name = name
        self._heap: list[tuple[float, int, _Candidate]] = []
        self._counter = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.k}, {self.name}, {self.largest})"

    def consider(
        self,
        record: Mapping[str, Any],
        priority: float | None = None,
        *,
        score: float | None = None,
    ) -> None:
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

        candidate = _Candidate(value, self._counter, dict(record))
        self._counter += 1
        # The heap always keeps the less desirable candidate at its root.
        heap_score = value if self.largest else -value
        item = (heap_score, candidate.order, candidate)
        if len(self._heap) < self.k:
            heappush(self._heap, item)
        elif item[:2] > self._heap[0][:2]:
            heappushpop(self._heap, item)

    def records(self) -> list[dict[str, Any]]:
        """Return selected records in best-first order."""
        candidates = [item[2] for item in self._heap]
        candidates.sort(
            key=lambda item: (item.score, item.order),
            reverse=self.largest,
        )
        return [item.record for item in candidates]

    def __len__(self) -> int:
        return len(self._heap)


class ExampleSelector:
    """Run several named TopK criteria over the same candidate stream.

    A selected record is returned once, with ``selection.reasons`` listing
    every selector that selected it and ``selection.scores`` containing the
    corresponding diagnostic score.
    """

    def __init__(self, selectors: list[TopKSelector]) -> None:
        if not selectors:
            raise ValueError("at least one selector is required")
        if any(selector.name is None for selector in selectors):
            raise ValueError("every selector must have a name")
        self.selectors = selectors

    def consider(self, record: Mapping[str, Any]) -> None:
        for selector in self.selectors:
            selector.consider(record)

    def records(self) -> list[dict[str, Any]]:
        merged: dict[Any, dict[str, Any]] = {}
        for selector in self.selectors:
            for record in selector.records():
                example_id = record.get("example_id")
                if example_id is None:
                    raise ValueError("multi-selector records require example_id")
                item = merged.setdefault(example_id, dict(record))
                selection = item.setdefault("selection", {})
                reasons = selection.setdefault("reasons", [])
                if selector.name not in reasons:
                    reasons.append(selector.name)
                scores = selection.setdefault("scores", {})
                if selector.key is not None:
                    scores[selector.name] = float(selector.key(record))
        return list(merged.values())

    def __repr__(self) -> str:
        return f"{self.selectors}"