# -*- coding: utf-8 -*-
"""Tests for the ExampleProvider interface contract."""
from __future__ import annotations

import unittest
from typing import Any

from remgu.example.example_provider import ExampleProvider


class FakeProvider(ExampleProvider):
    """In-memory provider used to verify the protocol contract."""

    def __init__(self) -> None:
        """Initialize one representative example."""
        self.items = {"node-42": {"degree": 17, "label": "fraud"}}

    def get(self, example_id: str) -> Any:
        """Return a stored example.

        Args:
            example_id: Example identifier.
        """
        return self.items[example_id]

    def describe(self, example_id: str) -> str:
        """Describe a stored example.

        Args:
            example_id: Example identifier.
        """
        item = self.items[example_id]
        return f"{example_id}: degree={item['degree']}, label={item['label']}"


class TestExampleProvider(unittest.TestCase):
    """Verify the provider's get/describe contract."""

    def test_example_provider_supports_get_and_describe(self) -> None:
        """Resolve an example and provide its human-readable description."""
        provider: ExampleProvider = FakeProvider()
        self.assertEqual(provider.get("node-42"), {"degree": 17, "label": "fraud"})
        self.assertEqual(provider.describe("node-42"), "node-42: degree=17, label=fraud")
