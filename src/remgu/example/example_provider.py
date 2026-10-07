# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Interface for resolving compact src example identifiers."""
from __future__ import annotations

from typing import Any, Protocol


class ExampleProvider(Protocol):
    """Define the read-only interface used to resolve diagnostic example IDs."""

    def get(self, example_id: str) -> Any:
        """Load the original example or its lightweight context.

        Args:
            example_id: Compact identifier of the requested example.
        """
        ...

    def describe(self, example_id: str) -> str:
        """Return a cheap human-readable description of an example.

        Args:
            example_id: Compact identifier of the requested example.
        """
        ...
