# -*- coding: utf8 -*-
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

__author__ = 'Mstislav Maslennikov'


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_yaml_data(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_yaml_data(item) for key, item in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {key: to_yaml_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_yaml_data(item) for item in value]
    return value


class FileStorage:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.runs_path = self.base_path / "runs"
        self.active_path = self.base_path / "active"

    def initialize(self) -> None:
        self.runs_path.mkdir(parents=True, exist_ok=True)

    def next_run_id(self) -> str:
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
        return self.runs_path / run_id

    def list_run_ids(self) -> list[str]:
        """Return run IDs ordered by their numeric suffix, oldest first."""
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
        path = self.run_path(run_id)
        path.mkdir(parents=True, exist_ok=True)
        with (path / "run.yaml").open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                to_yaml_data(data),
                file,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

    def read_run(self, run_id: str) -> dict[str, Any]:
        with (self.run_path(run_id) / "run.yaml").open(encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def set_active(self, run_id: str) -> None:
        self.initialize()
        if self.active_path.exists():
            current = self.active_path.read_text(encoding="utf-8").strip()
            if current:
                raise RuntimeError(f"Another run is already active: {current}")
        self.active_path.write_text(run_id + "\n", encoding="utf-8")

    def clear_active(self, run_id: str) -> None:
        if not self.active_path.exists():
            return
        current = self.active_path.read_text(encoding="utf-8").strip()
        if current == run_id:
            self.active_path.unlink()

    def get_active(self) -> str | None:
        if not self.active_path.exists():
            return None
        value = self.active_path.read_text(encoding="utf-8").strip()
        return value or None

    @staticmethod
    def write_yaml_file(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                to_yaml_data(data),
                file,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

    @staticmethod
    def read_yaml_file(path: Path) -> Any:
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as file:
            return yaml.safe_load(file)