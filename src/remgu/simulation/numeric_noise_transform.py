# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Add reproducible bounded noise to a numeric record field."""
from typing import Any, Mapping
from remgu.simulation.random_source import RandomSource
from remgu.simulation.transform import Transform


class NumericNoiseTransform(Transform):
    """Add uniform noise in ``[-magnitude, magnitude]`` to a numeric field."""

    def __init__(self, field_name: str, magnitude: float) -> None:
        """Configure the field and noise magnitude.

        Args:
            field_name: Numeric mapping key to transform.
            magnitude: Non-negative maximum absolute perturbation.
        """
        if not field_name:
            raise ValueError("field_name must not be empty")
        if magnitude < 0:
            raise ValueError("magnitude must be non-negative")
        self.field_name = field_name
        self.magnitude = float(magnitude)

    def apply(self, record: Mapping[str, Any], random_source: RandomSource) -> dict[str, Any]:
        """Return a copied record with noise added to the configured numeric field."""
        if self.field_name not in record:
            raise ValueError(f"record is missing field: {self.field_name}")
        try:
            value = float(record[self.field_name])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"field must be numeric: {self.field_name}") from exc
        result = dict(record)
        result[self.field_name] = value + (random_source.random() * 2.0 - 1.0) * self.magnitude
        return result
