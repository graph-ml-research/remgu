# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Validated allowlist for optional dashboard control operations."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Callable


class ExperimentController:
    """Expose only explicitly registered hot parameters and supported lifecycle commands."""

    def __init__(self, parameter_specs: dict[str, dict[str, Any]] | None = None,
                 parameter_setter: Callable[[str, Any], Any] | None = None,
                 commands: dict[str, Callable[[], Any]] | None = None) -> None:
        """Configure parameter metadata and explicit trusted callbacks."""
        self.parameter_specs = dict(parameter_specs or {})
        self.parameter_setter = parameter_setter
        self.commands = dict(commands or {})
        self.audit_log: list[dict[str, Any]] = []
        self._values = {name: spec.get("value") for name, spec in self.parameter_specs.items()}
        for name, spec in self.parameter_specs.items():
            if spec.get("category") not in {"hot", "structural", "view", "ui-only"}:
                raise ValueError(f"invalid parameter category for {name}")

    def apply_parameter(self, name: str, value: Any) -> dict[str, Any]:
        """Validate and apply an allowlisted parameter update, recording accepted/rejected outcomes."""
        spec = self.parameter_specs.get(name)
        old_value = self._values.get(name) if name in self._values else None
        try:
            if spec is None:
                raise ValueError("parameter is not allowlisted")
            if spec.get("category") != "hot":
                raise ValueError("only hot parameters can be changed while running")
            expected = spec.get("type")
            if expected == "int" and (not isinstance(value, int) or isinstance(value, bool)):
                raise ValueError("parameter must be an integer")
            if expected == "float" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                raise ValueError("parameter must be numeric")
            if expected == "bool" and not isinstance(value, bool):
                raise ValueError("parameter must be boolean")
            if expected == "str" and not isinstance(value, str):
                raise ValueError("parameter must be a string")
            if "min" in spec and value < spec["min"]: raise ValueError("parameter is below minimum")
            if "max" in spec and value > spec["max"]: raise ValueError("parameter is above maximum")
            if self.parameter_setter is None: raise RuntimeError("parameter updates are not supported by this runner")
            outcome = self.parameter_setter(name, value)
            self._values[name] = value
            event = {"timestamp": datetime.now(timezone.utc).isoformat(), "type": "parameter_update",
                     "name": name, "old_value": old_value, "new_value": value,
                     "result": str(outcome), "status": "applied"}
            self.audit_log.append(event)
            return event
        except (ValueError, TypeError, RuntimeError) as exc:
            event = {"timestamp": datetime.now(timezone.utc).isoformat(), "type": "parameter_update",
                     "name": name, "old_value": old_value, "new_value": value,
                     "result": str(exc), "status": "rejected"}
            self.audit_log.append(event)
            raise

    def execute(self, command: str) -> dict[str, Any]:
        """Execute a registered lifecycle command, never arbitrary client code."""
        if command not in {"pause", "resume", "stop", "checkpoint"} or command not in self.commands:
            raise ValueError("command is not supported")
        result = self.commands[command]()
        event = {"timestamp": datetime.now(timezone.utc).isoformat(), "type": "command",
                 "command": command, "result": str(result)}
        self.audit_log.append(event)
        return event
