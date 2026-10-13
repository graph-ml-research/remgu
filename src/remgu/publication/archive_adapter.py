# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""ZIP publication adapter for self-contained research archives."""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from remgu.research_snapshot import ResearchSnapshot, ResearchSnapshotRun


class ArchiveAdapter:
    """Publish a ResearchSnapshot and known source artifacts as a ZIP archive."""

    ARCHIVE_ROOT = "research-archive"
    """Top-level directory inside every generated archive."""

    def __init__(self, base_path: str | Path = ".research", project_name: str = "ReMgu") -> None:
        """Create an archive adapter for one research store.

        Args:
            base_path: Root directory containing persisted research runs.
            project_name: Human-readable project or research name shown in the archive.
        """
        self.base_path = Path(base_path)
        """Research directory whose persisted files are published."""
        self.project_name = project_name
        """Human-readable project or research name published in archive metadata."""

    def create(self, snapshot: ResearchSnapshot, output_path: str | Path = "research-archive.zip") -> Path:
        """Create a deterministic ZIP archive without changing the source store.

        Args:
            snapshot: In-memory research snapshot to publish.
            output_path: Destination ZIP file. Existing files are rejected.
        """
        output = Path(output_path)
        if output.exists():
            raise FileExistsError(f"Archive already exists: {output}. Choose another path.")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        if temporary.exists():
            temporary.unlink()
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                self._write_text(archive, f"{self.ARCHIVE_ROOT}/README.md", self._readme(snapshot))
                self._write_text(archive, f"{self.ARCHIVE_ROOT}/report.md", self._report(snapshot))
                self._write_yaml(archive, f"{self.ARCHIVE_ROOT}/research.yaml", self._research_yaml(snapshot))
                for run in snapshot.runs:
                    self._copy_run(archive, run)
                self._write_examples(archive, snapshot)
            temporary.replace(output)
        except Exception:
            if temporary.exists():
                temporary.unlink()
            raise
        return output

    def _copy_run(self, archive: zipfile.ZipFile, run: ResearchSnapshotRun) -> None:
        """Copy only existing known run artifacts into the archive.

        Args:
            archive: Open ZIP archive receiving files.
            run: Snapshot run describing which persisted run to publish.
        """
        source_dir = self.base_path / "runs" / run.run_id
        for name in ("run.yaml", "params.yaml", "metrics.csv", "samples.jsonl"):
            source = source_dir / name
            if source.exists() and source.is_file():
                self._write_bytes(archive, f"{self.ARCHIVE_ROOT}/runs/{run.run_id}/{name}", source.read_bytes())

    def _write_examples(self, archive: zipfile.ZipFile, snapshot: ResearchSnapshot) -> None:
        """Publish compact sample records as individual JSON example files when possible.

        Args:
            archive: Open ZIP archive receiving example files.
            snapshot: Snapshot containing compact diagnostic samples.
        """
        used: set[str] = set()
        for index, sample in enumerate(snapshot.samples, start=1):
            example_id = sample.get("example_id")
            if not isinstance(example_id, str) or not example_id.strip():
                continue
            stem = self._safe_filename(example_id)
            if not stem:
                continue
            name = f"{self.ARCHIVE_ROOT}/examples/{stem}.json"
            if name in used:
                name = f"{self.ARCHIVE_ROOT}/examples/{stem}-{index}.json"
            used.add(name)
            payload = {key: value for key, value in sample.items() if key != "run_id"}
            self._write_text(archive, name, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    def _readme(self, snapshot: ResearchSnapshot) -> str:
        """Generate the archive README from snapshot facts.

        Args:
            snapshot: Snapshot being documented.
        """
        created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        s = snapshot.summary
        return (f"# {self.project_name} research archive\n\n"
                f"Archive created: {created}\n\n"
                "This archive is a self-contained publication of the ReMgu research history. "
                "The original `.research` store remains the source of truth.\n\n"
                "## Summary\n\n"
                f"- Runs: {s.total_runs}\n- Completed: {s.completed}\n- Failed: {s.failed}\n"
                f"- Aborted: {s.aborted}\n- Running: {s.running}\n- Reviewed: {s.reviewed}\n"
                f"- Needs review: {s.needs_review}\n\n"
                "## Contents\n\n"
                "- `report.md` — compact automatically generated research summary.\n"
                "- `research.yaml` — machine-readable snapshot summary and relations.\n"
                "- `runs/` — copies of existing `run.yaml`, `params.yaml`, `metrics.csv`, and `samples.jsonl` files.\n"
                "- `examples/` — compact diagnostic examples with an `example_id`, when available.\n\n"
                "The archive does not contain original datasets, model objects, or other large data that ReMgu cannot serialize. "
                "Examples are compact diagnostic records, not copies of source datasets.\n")

    def _report(self, snapshot: ResearchSnapshot) -> str:
        """Generate a conservative research report using only persisted facts.

        Args:
            snapshot: Snapshot whose facts are rendered.
        """
        lines = ["# Research report", "", "## Summary", "", snapshot.summary_text, "", "## Research history", ""]
        if snapshot.relations:
            for relation in snapshot.relations:
                lines.append(f"- `{relation['run_id']}` → `{relation['reference']}`")
        else:
            lines.append("No run relations were recorded.")
        lines += ["", "## Runs", ""]
        for run in snapshot.runs:
            lines += [f"### {run.run_id}", "", f"- Hypothesis: {run.hypothesis}",
                      f"- Execution: `{run.execution_status}`", f"- Review: `{run.review_status}`"]
            if run.started_at is not None:
                lines.append(f"- Started: {run.started_at.isoformat()}")
            if run.finished_at is not None:
                lines.append(f"- Finished: {run.finished_at.isoformat()}")
            if run.conclusion is not None:
                lines.append(f"- Conclusion: {run.conclusion}")
            if run.next_step is not None:
                lines.append(f"- Next step: {run.next_step}")
            lines.append("")
        lines += ["## Key metrics", ""]
        if snapshot.metrics:
            lines += ["| Run | Step | Metric | Value |", "|---|---:|---|---|"]
            for row in snapshot.metrics:
                lines.append(f"| {row.get('run_id', '')} | {row.get('step', '')} | {row.get('metric_name', '')} | {row.get('metric_value', '')} |")
        else:
            lines.append("No metrics were recorded.")
        lines += ["", "## Collected examples", ""]
        lines.append(f"{len(snapshot.samples)} compact diagnostic records were collected.")
        lines += ["", "## Consistency", ""]
        errors = sum(issue.severity == "error" for issue in snapshot.findings)
        warnings = sum(issue.severity != "error" for issue in snapshot.findings)
        lines.append(f"Findings: {warnings} warnings, {errors} errors.")
        for issue in snapshot.findings:
            lines.append(f"- `{issue.severity}` `{issue.run_id}` `{issue.code}` — {issue.message}")
        lines += ["", "## Conclusions", "", "This report contains only conclusions explicitly recorded in run review data. "
                  "ReMgu does not infer or generate scientific conclusions.", ""]
        return "\n".join(lines)

    def _research_yaml(self, snapshot: ResearchSnapshot) -> dict[str, Any]:
        """Build the machine-readable archive metadata document.

        Args:
            snapshot: Snapshot being serialized.
        """
        return {"project": self.project_name, "summary": {
            "total_runs": snapshot.summary.total_runs,
            "completed": snapshot.summary.completed,
            "failed": snapshot.summary.failed,
            "aborted": snapshot.summary.aborted,
            "running": snapshot.summary.running,
            "reviewed": snapshot.summary.reviewed,
            "needs_review": snapshot.summary.needs_review,
        }, "relations": snapshot.relations,
        "findings": [{"run_id": issue.run_id, "severity": issue.severity,
                      "code": issue.code, "message": issue.message} for issue in snapshot.findings]}

    @staticmethod
    def _safe_filename(value: str) -> str:
        """Convert an example identifier into a safe archive filename stem.

        Args:
            value: Example identifier supplied by a compact sample record.
        """
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")

    @staticmethod
    def _write_text(archive: zipfile.ZipFile, name: str, content: str) -> None:
        """Write deterministic UTF-8 text into an archive.

        Args:
            archive: Open ZIP archive.
            name: Archive-relative file name.
            content: Text content to store.
        """
        ArchiveAdapter._write_bytes(archive, name, content.encode("utf-8"))

    @staticmethod
    def _write_yaml(archive: zipfile.ZipFile, name: str, data: dict[str, Any]) -> None:
        """Serialize a mapping as deterministic YAML inside the archive.

        Args:
            archive: Open ZIP archive.
            name: Archive-relative file name.
            data: Mapping to serialize.
        """
        import yaml
        content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        ArchiveAdapter._write_text(archive, name, content)

    @staticmethod
    def _write_bytes(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
        """Write bytes with a fixed ZIP timestamp for reproducible content.

        Args:
            archive: Open ZIP archive.
            name: Archive-relative file name.
            content: Bytes to store.
        """
        info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)
