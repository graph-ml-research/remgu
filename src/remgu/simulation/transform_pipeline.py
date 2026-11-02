# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Apply transforms either to a dataset or lazily to batches."""
from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Iterator
from remgu.simulation.random_source import RandomSource
from remgu.simulation.transform import Transform


class TransformPipeline:
    """Apply an ordered sequence of record transforms with explicit randomness."""

    def __init__(self, transforms: Sequence[Transform], mode: str = "dataset") -> None:
        """Create a pipeline in ``dataset`` or ``batch`` mode.

        Args:
            transforms: Ordered transformations; composition order is significant.
            mode: Application mode, either ``dataset`` or ``batch``.
        """
        if mode not in ("dataset", "batch"):
            raise ValueError("mode must be 'dataset' or 'batch'")
        self.transforms = tuple(transforms)
        self.mode = mode
        unsupported = [type(item).__name__ for item in self.transforms if mode not in item.supported_modes]
        if unsupported:
            raise ValueError(f"transforms do not support mode {mode}: {unsupported}")

    def apply_dataset(self, records: Iterable[Mapping[str, Any]], random_source: RandomSource) -> list[dict[str, Any]]:
        """Transform a finite dataset and return a new list without mutating input records."""
        if self.mode != "dataset":
            raise RuntimeError("pipeline is configured for batch mode")
        return [self._apply_record(record, random_source) for record in records]

    def transform_batches(self, batches: Iterable[Iterable[Mapping[str, Any]]],
                          random_source: RandomSource) -> Iterator[list[dict[str, Any]]]:
        """Lazily transform one batch at a time without materializing the full stream."""
        if self.mode != "batch":
            raise RuntimeError("pipeline is configured for dataset mode")
        for batch in batches:
            yield [self._apply_record(record, random_source) for record in batch]

    def _apply_record(self, record: Mapping[str, Any], random_source: RandomSource) -> dict[str, Any]:
        """Apply every configured transform in order to a single record."""
        current = dict(record)
        for transform in self.transforms:
            current = transform.apply(current, random_source)
        return current
