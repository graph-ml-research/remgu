# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Reproducible bounded-memory selection of diagnostic examples."""
from __future__ import annotations
import heapq
import math
import random
from collections.abc import Iterable, Mapping
from typing import Any


class ExampleSelectionService:
    """Select examples by explicit strategies while retaining at most ``limit`` records."""

    def select(self, records: Iterable[Mapping[str, Any]], strategy: str = "random", *, limit: int = 20,
               seed: int = 0, score_key: str = "score") -> list[dict[str, Any]]:
        """Return a bounded selection without mutating records or materializing the whole pool.

        Supported strategies: ``random``, ``top_k``, ``errors``, ``confident_errors``,
        ``correct_predictions``, ``rare_examples``, ``hard`` and ``has_bridge``.

        ``confident_errors`` selects incorrect predictions with the highest confidence
        (confidence is expected on a 0..1 scale, so 0.93 means 93%).
        ``rare_examples`` ranks records by ascending ``frequency``; smaller values mean rarer.
        ``correct_predictions`` selects records marked with ``correct=True``. Required metadata is validated as records are read.
        """
        if limit < 1: raise ValueError("limit must be positive")
        if strategy not in {"random", "top_k", "errors", "confident_errors", "correct_predictions", "rare_examples", "hard", "has_bridge"}:
            raise ValueError(f"unsupported example selection strategy: {strategy}")
        randomizer = random.Random(seed)
        if strategy == "random":
            reservoir = []
            for index, record in enumerate(records):
                copied = dict(record)
                if index < limit: reservoir.append(copied)
                else:
                    replacement = randomizer.randrange(index + 1)
                    if replacement < limit: reservoir[replacement] = copied
            return reservoir
        if strategy in {"top_k", "confident_errors", "rare_examples", "hard"}:
            heap = []
            for index, record in enumerate(records):
                copied = dict(record)
                if strategy == "top_k":
                    if score_key not in copied: raise ValueError(f"records must contain {score_key!r}")
                    score = float(copied[score_key])
                elif strategy == "hard":
                    if "difficulty" not in copied: raise ValueError("records must contain 'difficulty'")
                    score = float(copied["difficulty"])
                elif strategy == "rare_examples":
                    if "frequency" not in copied: raise ValueError("records must contain 'frequency'")
                    score = -float(copied["frequency"])
                else:
                    if not {"correct", "confidence"}.issubset(copied):
                        raise ValueError("records must contain 'correct' and 'confidence'")
                    if copied["correct"] is not False: continue
                    score = float(copied["confidence"])
                if not math.isfinite(score): raise ValueError("selection scores must be finite numbers")
                item = (score, -index, copied)
                if len(heap) < limit: heapq.heappush(heap, item)
                elif item[:2] > heap[0][:2]: heapq.heapreplace(heap, item)
            return [item[2] for item in sorted(heap, key=lambda item: (-item[0], -item[1]))]
        selected = []
        required = "correct" if strategy in {"errors", "correct_predictions"} else "has_bridge"
        for record in records:
            copied = dict(record)
            if required not in copied: raise ValueError(f"records must contain {required!r}")
            matches = (copied[required] is False if strategy == "errors" else
                       copied[required] is True if strategy == "correct_predictions" else
                       copied[required] is True)
            if matches:
                selected.append(copied)
                if len(selected) >= limit: break
        return selected
