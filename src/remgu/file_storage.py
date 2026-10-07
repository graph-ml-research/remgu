# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""File-backed persistence for ReMgu research runs and artifacts."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class FileStorage:
    """Persist research state in the project's human-readable ``.research`` tree."""

    def __init__(self, base_path: str | Path):
        """Create storage rooted at a research directory.

        Args:
            base_path: Root directory containing ``runs/`` and the active-run pointer.
        """
        self.base_path = Path(base_path)
        """Root directory of the persistent research store."""
        self.runs_path = self.base_path / "runs"
        """Directory containing one subdirectory per run."""
        self.active_path = self.base_path / "active"
        """Text file containing the identifier of the active run."""

    def initialize(self) -> None:
        """Create the run directory if it does not exist."""
        self.runs_path.mkdir(parents=True, exist_ok=True)

    def next_run_id(self) -> str:
        """Return the next sequential run identifier without creating a run."""
        self.initialize()
        numbers = []
        for path in self.runs_path.iterdir():
            if not path.is_dir() or not path.name.startswith("run-"):
                continue
            suffix = path.name[4:]
            if suffix.isdigit():
                numbers.append(int(suffix))
        number = max(numbers, default=0) + 1
        return f"run-{number:03d}"

    def run_path(self, run_id: str) -> Path:
        """Return the filesystem path belonging to a run.

        Args:
            run_id: Persistent run identifier such as ``run-001``.
        """
        return self.runs_path / run_id

    def list_run_ids(self) -> list[str]:
        """Return valid run identifiers ordered by numeric suffix, oldest first."""
        self.initialize()
        runs = []
        for path in self.runs_path.iterdir():
            if not path.is_dir() or not path.name.startswith("run-"):
                continue
            suffix = path.name[4:]
            if suffix.isdigit():
                runs.append((int(suffix), path.name))
        runs.sort()
        return [run_id for _, run_id in runs]

    def write_run(self, run_id: str, data: dict[str, Any]) -> None:
        """Serialize one run's metadata to ``run.yaml``.

        Args:
            run_id: Identifier of the run being persisted.
            data: Mapping containing research, execution and review metadata.
        """
        path = self.run_path(run_id)
        path.mkdir(parents=True, exist_ok=True)
        with (path / "run.yaml").open("w", encoding="utf-8") as file:
            yaml.safe_dump(self._to_yaml_data(data), file, allow_unicode=True,
                           sort_keys=False, default_flow_style=False)

    def read_run(self, run_id: str) -> dict[str, Any]:
        """Load one run's ``run.yaml`` mapping.

        Args:
            run_id: Identifier of the run to load.
        """
        with (self.run_path(run_id) / "run.yaml").open(encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def set_active(self, run_id: str) -> None:
        """Set the active-run pointer, rejecting a different active run.

        Args:
            run_id: Identifier of the run that should become active.
        """
        self.initialize()
        if self.active_path.exists():
            current = self.active_path.read_text(encoding="utf-8").strip()
            if current:
                raise RuntimeError(f"Another run is already active: {current}")
        self.active_path.write_text(run_id + "\n", encoding="utf-8")

    def clear_active(self, run_id: str) -> None:
        """Remove the active pointer only when it points to the supplied run.

        Args:
            run_id: Identifier whose active pointer should be cleared.
        """
        if not self.active_path.exists():
            return
        current = self.active_path.read_text(encoding="utf-8").strip()
        if current == run_id:
            self.active_path.unlink()

    def get_active(self) -> str | None:
        """Return the active run identifier, or ``None`` when no pointer exists."""
        if not self.active_path.exists():
            return None
        value = self.active_path.read_text(encoding="utf-8").strip()
        return value or None

    def write_yaml_file(self, path: Path, data: Any) -> None:
        """Write arbitrary YAML data to an artifact file.

        Args:
            path: Destination path for the YAML file.
            data: Python value to serialize as YAML.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(self._to_yaml_data(data), file, allow_unicode=True,
                           sort_keys=False, default_flow_style=False)

    def read_yaml_file(self, path: Path) -> Any:
        """Read arbitrary YAML data, returning ``None`` for a missing file.

        Args:
            path: Source path of the YAML file.
        """
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as file:
            return yaml.safe_load(file)

    @staticmethod
    def utc_now() -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc)

    @classmethod
    def _to_yaml_data(cls, value: Any) -> Any:
        """Convert dataclasses, datetimes and containers into YAML-safe data.

        Args:
            value: Arbitrary Python value that should be represented in YAML.
        """
        if is_dataclass(value):
            return {key: cls._to_yaml_data(item) for key, item in asdict(value).items()}
        if isinstance(value, datetime):
            return value.isoformat().replace("+00:00", "Z")
        if isinstance(value, dict):
            return {key: cls._to_yaml_data(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._to_yaml_data(item) for item in value]
        return value
