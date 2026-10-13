# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Markdown publication adapter for in-memory research snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from remgu.research_snapshot import ResearchSnapshot, ResearchSnapshotRun


class MarkdownAdapter:
    """Render a ``ResearchSnapshot`` as one standalone Markdown document."""

    def export(self, snapshot: ResearchSnapshot, output_path: str | Path = "research.md") -> Path:
        """Write a Markdown report without reading or modifying the research store.

        Args:
            snapshot: In-memory research history prepared by ``ResearchSnapshotBuilder``.
            output_path: Destination Markdown file. Existing files are rejected.

        Returns:
            Path to the generated Markdown document.

        Raises:
            FileExistsError: If the destination already exists.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        content = self.render(snapshot)
        try:
            with output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
        except FileExistsError as exc:
            raise FileExistsError(f"Markdown report already exists: {output}. Choose another path.") from exc
        except Exception:
            if output.exists():
                output.unlink()
            raise
        return output

    def render(self, snapshot: ResearchSnapshot) -> str:
        """Render a snapshot to Markdown without filesystem access.

        Args:
            snapshot: In-memory research history to render.

        Returns:
            UTF-8-ready Markdown text ending with a newline.
        """
        lines = ["# Research report", "", "## Summary", ""]
        summary = snapshot.summary
        lines.extend([
            f"- Total runs: {summary.total_runs}",
            f"- Completed: {summary.completed}",
            f"- Failed: {summary.failed}",
            f"- Aborted: {summary.aborted}",
            f"- Running: {summary.running}",
            f"- Reviewed: {summary.reviewed}",
            f"- Needs review: {summary.needs_review}",
            "",
            "## Research history",
            "",
        ])
        if snapshot.runs:
            for run in snapshot.runs:
                lines.extend(self._render_run(run))
        else:
            lines.append("No runs have been recorded.")

        lines.extend(["", "## Relations", ""])
        if snapshot.relations:
            for relation in snapshot.relations:
                lines.append(f"- `{self._inline(relation.get('run_id', ''))}` ← `{self._inline(relation.get('reference', ''))}`")
        else:
            lines.append("No run relations were recorded.")

        lines.extend(["", "## Collected examples", ""])
        if snapshot.samples:
            for index, sample in enumerate(snapshot.samples, start=1):
                run_id = sample.get("run_id")
                title = f"Sample {index}" + (f" — {run_id}" if run_id else "")
                lines.extend([f"### {self._inline(title)}", ""])
                description = sample.get("description")
                if isinstance(description, str) and description.strip():
                    lines.extend([f"**Description:** {self._inline(description.strip())}", ""])
                lines.extend(["````json", self._json(sample), "````", ""])
        else:
            lines.append("No compact diagnostic samples were collected.")

        lines.extend(["", "## Consistency", ""])
        errors = sum(issue.severity == "error" for issue in snapshot.findings)
        warnings = sum(issue.severity != "error" for issue in snapshot.findings)
        lines.append(f"Findings: {warnings} warnings, {errors} errors.")
        if snapshot.findings:
            lines.append("")
            for issue in snapshot.findings:
                lines.append(
                    f"- **{self._inline(issue.severity)}** — run `{self._inline(issue.run_id)}`, "
                    f"code `{self._inline(issue.code)}`: {self._inline(issue.message)}"
                )
        lines.extend([
            "",
            "## Conclusions",
            "",
            "Conclusions and next steps below are copied from existing run review records; "
            "ReMgu does not infer scientific conclusions.",
            "",
        ])
        reviewed_runs = [run for run in snapshot.runs if run.conclusion or run.next_step]
        if reviewed_runs:
            for run in reviewed_runs:
                lines.append(f"### {self._inline(run.run_id)}")
                if run.conclusion:
                    lines.extend(["", f"**Conclusion:** {self._inline(run.conclusion)}"])
                if run.next_step:
                    lines.extend(["", f"**Next step:** {self._inline(run.next_step)}"])
                lines.append("")
        else:
            lines.append("No conclusions or next steps have been recorded.")
            lines.append("")
        return "\n".join(lines)

    def _render_run(self, run: ResearchSnapshotRun) -> list[str]:
        """Render one run and its main metrics as Markdown lines.

        Args:
            run: Snapshot view of the run to render.

        Returns:
            Markdown lines for this run.
        """
        motivation_type = run.motivation.get("type", "unknown")
        reference = run.motivation.get("reference")
        motivation = str(motivation_type)
        if reference:
            motivation += f" (reference: {reference})"
        lines = [
            f"### {self._inline(run.run_id)}",
            "",
            f"- **Hypothesis:** {self._inline(run.hypothesis) or '_Not recorded_'}",
            f"- **Motivation:** {self._inline(motivation)}",
            f"- **Execution status:** `{self._inline(run.execution_status)}`",
            f"- **Review status:** `{self._inline(run.review_status)}`",
        ]
        if run.started_at is not None:
            lines.append(f"- **Started:** {run.started_at.isoformat()}")
        if run.finished_at is not None:
            lines.append(f"- **Finished:** {run.finished_at.isoformat()}")
        if run.conclusion:
            lines.append(f"- **Conclusion:** {self._inline(run.conclusion)}")
        if run.next_step:
            lines.append(f"- **Next step:** {self._inline(run.next_step)}")
        if run.params:
            lines.extend(["", "**Parameters:**", "", "````yaml", self._yaml_like(run.params), "````"])
        if run.metrics:
            lines.extend(["", "**Metrics:**", "", "| Step | Metric | Value |", "|---:|---|---:|"])
            for metric in run.metrics:
                lines.append(
                    f"| {self._cell(metric.get('step', ''))} | "
                    f"{self._cell(metric.get('metric_name', ''))} | "
                    f"{self._cell(metric.get('metric_value', ''))} |"
                )
        lines.append("")
        return lines

    @staticmethod
    def _inline(value: Any) -> str:
        """Normalize text for safe use in a single Markdown line.

        Args:
            value: Arbitrary snapshot value to display as inline text.
        """
        return " ".join(str(value).replace("`", "\\`").split())

    @staticmethod
    def _cell(value: Any) -> str:
        """Escape Markdown table separators and line breaks.

        Args:
            value: Value displayed in a Markdown table cell.
        """
        return MarkdownAdapter._inline(value).replace("|", "\\|")

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        """Serialize a compact sample record as readable JSON.

        Args:
            value: Snapshot sample record to serialize.
        """
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)

    @staticmethod
    def _yaml_like(value: dict[str, Any]) -> str:
        """Render parameter mappings in a readable YAML-style block.

        Args:
            value: Snapshot parameter mapping to render.
        """
        import yaml

        return yaml.safe_dump(value, allow_unicode=True, sort_keys=True, default_flow_style=False).rstrip()
