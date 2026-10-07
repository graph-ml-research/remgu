# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Combine several named example-selection criteria."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .top_k_selector import TopKSelector


class ExampleSelector:
    """Run several named top-k criteria over the same candidate stream."""

    def __init__(self, selectors: list[TopKSelector]) -> None:
        """Create a multi-criterion selector.

        Args:
            selectors: Named top-k selectors evaluated over the same records.
        """
        if not selectors:
            raise ValueError("at least one selector is required")
        if any(selector.name is None for selector in selectors):
            raise ValueError("every selector must have a name")
        self.selectors = selectors
        """Ordered selectors whose outputs will be merged."""

    def consider(self, record: Mapping[str, Any]) -> None:
        """Pass one record to every configured selector.

        Args:
            record: Candidate diagnostic record shared by all selectors.
        """
        for selector in self.selectors:
            selector.consider(record)

    def records(self) -> list[dict[str, Any]]:
        """Return unique selected records with reasons and scores attached."""
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
        """Return a concise representation of the configured selectors."""
        return f"{self.selectors}"
