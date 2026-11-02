# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Collect optional model diagnostics without requiring a specific ML framework."""
from __future__ import annotations
from typing import Any


class Probe:
    """Call an adapter's optional ``get_probe_data`` method when it is available."""

    def __init__(self, adapter: Any) -> None:
        """Create a probe for a model adapter implementing the optional diagnostics contract."""
        self.adapter = adapter

    def collect(self) -> dict[str, Any]:
        """Return available diagnostic data or an explicit unavailable status."""
        getter = getattr(self.adapter, "get_probe_data", None)
        if not callable(getter):
            return {"status": "unavailable", "reason": "adapter does not implement get_probe_data"}
        data = getter()
        if data is None:
            return {"status": "unavailable", "reason": "adapter returned no diagnostic data"}
        if not isinstance(data, dict):
            raise TypeError("get_probe_data() must return a dict or None")
        return {"status": "available", "data": dict(data)}
