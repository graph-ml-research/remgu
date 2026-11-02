# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Reproducible random source for simulation components."""
from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class RandomSource:
    """Encapsulate a deterministic random generator with an explicit seed."""

    def __init__(self, seed: int) -> None:
        """Create a random source.

        Args:
            seed: Integer seed that identifies the random stream.
        """
        self.seed = int(seed)
        self._random = random.Random(self.seed)

    def random(self) -> float:
        """Return the next random float in the half-open interval [0, 1)."""
        return self._random.random()

    def randint(self, lower: int, upper: int) -> int:
        """Return a random integer in the inclusive interval [lower, upper]."""
        return self._random.randint(lower, upper)

    def choice(self, values: Sequence[T]) -> T:
        """Choose one value from a non-empty sequence."""
        if not values:
            raise ValueError("values must not be empty")
        return self._random.choice(values)

    def shuffle(self, values: list[T]) -> None:
        """Shuffle a mutable list in place using this source's random stream."""
        self._random.shuffle(values)
