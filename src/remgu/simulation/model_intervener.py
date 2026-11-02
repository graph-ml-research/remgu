# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Apply and restore an explicit attribute-level model intervention."""
from __future__ import annotations
from typing import Any


class ModelIntervener:
    """Temporarily replace one existing model attribute and retain restoration data."""

    def apply(self, model: Any, attribute: str, value: Any) -> dict[str, Any]:
        """Replace an existing attribute and return an intervention record.

        Args:
            model: Model object to intervene on.
            attribute: Existing attribute name; new arbitrary attributes are not allowed.
            value: Replacement value.
        """
        if not attribute or not hasattr(model, attribute):
            raise ValueError(f"model has no attribute: {attribute}")
        previous = getattr(model, attribute)
        setattr(model, attribute, value)
        return {"attribute": attribute, "previous_value": previous, "new_value": value,
                "status": "applied"}

    def restore(self, model: Any, record: dict[str, Any]) -> None:
        """Restore the original attribute value from a record produced by ``apply``."""
        attribute = record.get("attribute")
        if not attribute or not hasattr(model, attribute):
            raise ValueError("intervention record does not match the model")
        setattr(model, attribute, record["previous_value"])
