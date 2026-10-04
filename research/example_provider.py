# -*- coding: utf8 -*-
from __future__ import annotations
from typing import Any, Protocol


__author__ = 'Mstislav Maslennikov'

class ExampleProvider(Protocol):
    """Resolve a compact example id to data and a human-readable description."""

    def get(self, example_id: str) -> Any:
        """Load the original example or its lightweight context."""
        ...

    def describe(self, example_id: str) -> str:
        """Return a cheap, human-readable description of the example."""
        ...