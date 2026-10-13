# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Static HTML site publication adapter for in-memory research snapshots."""
from __future__ import annotations

import html
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from remgu.research_snapshot import ResearchSnapshot, ResearchSnapshotRun


class StaticSiteAdapter:
    """Publish a ``ResearchSnapshot`` as a self-contained static HTML site."""

    def export(self, snapshot: ResearchSnapshot, output_path: str | Path = "site") -> Path:
        """Write a static site without reading or modifying the research store.

        Args:
            snapshot: In-memory research history prepared by the snapshot builder.
            output_path: Destination directory. Existing directories are rejected.

        Returns:
            Path to the generated site directory.

        Raises:
            FileExistsError: If the destination already exists.
        """
        output = Path(output_path)
        if output.exists():
            raise FileExistsError(f"Static site destination already exists: {output}. Choose another path.")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
        try:
            (temporary / "runs").mkdir()
            (temporary / "examples").mkdir()
            (temporary / "style.css").write_text(self._stylesheet(), encoding="utf-8", newline="\n")
            (temporary / "index.html").write_text(self._render_index(snapshot), encoding="utf-8", newline="\n")
            (temporary / "examples" / "index.html").write_text(
                self._render_examples(snapshot, "../"), encoding="utf-8", newline="\n"
            )
            for run in snapshot.runs:
                (temporary / "runs" / f"{self._safe_id(run.run_id)}.html").write_text(
                    self._render_run(snapshot, run), encoding="utf-8", newline="\n"
                )
            temporary.rename(output)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return output

    def render_index(self, snapshot: ResearchSnapshot) -> str:
        """Render the site home page from snapshot data only.

        Args:
            snapshot: In-memory research history to render.

        Returns:
            Complete HTML document.
        """
        return self._render_index(snapshot)

    def _render_index(self, snapshot: ResearchSnapshot) -> str:
        """Build the home page with summary, history, conclusions, and findings."""
        summary = snapshot.summary
        body = ["<main>", "<h1>Research overview</h1>", "<section><h2>Summary</h2><dl class=\"summary\">"]
        for label, value in (
            ("Total runs", summary.total_runs), ("Completed", summary.completed),
            ("Failed", summary.failed), ("Aborted", summary.aborted),
            ("Running", summary.running), ("Reviewed", summary.reviewed),
            ("Needs review", summary.needs_review),
        ):
            body.append(f"<div><dt>{label}</dt><dd>{value}</dd></div>")
        body.extend(["</dl></section>", "<section><h2>Research history</h2>"])
        if snapshot.runs:
            body.append("<ol class=\"history\">")
            for run in snapshot.runs:
                run_file = self._safe_id(run.run_id) + ".html"
                body.append(
                    f'<li><a href="runs/{self._attr(run_file)}">{self._text(run.run_id)}</a> '
                    f'<span class="status">{self._text(run.execution_status)}</span> — '
                    f'{self._text(run.hypothesis or "Hypothesis not recorded")}</li>'
                )
            body.append("</ol>")
        else:
            body.append("<p>No runs have been recorded.</p>")
        body.extend(["</section>", "<section><h2>Conclusions</h2>"])
        reviewed = [run for run in snapshot.runs if run.conclusion or run.next_step]
        if reviewed:
            for run in reviewed:
                body.append(f"<article><h3>{self._text(run.run_id)}</h3>")
                if run.conclusion:
                    body.append(f"<p><strong>Conclusion:</strong> {self._text(run.conclusion)}</p>")
                if run.next_step:
                    body.append(f"<p><strong>Next step:</strong> {self._text(run.next_step)}</p>")
                body.append("</article>")
        else:
            body.append("<p>No conclusions or next steps have been recorded.</p>")
        body.extend(["</section>", "<section><h2>Consistency findings</h2>"])
        if snapshot.findings:
            body.append("<ul>")
            for issue in snapshot.findings:
                body.append(
                    f'<li class="finding {self._attr(issue.severity)}"><strong>{self._text(issue.severity)}</strong> '
                    f'[{self._text(issue.code)}] {self._text(issue.message)} '
                    f'(run: {self._text(issue.run_id)})</li>'
                )
            body.append("</ul>")
        else:
            body.append("<p>No consistency findings.</p>")
        body.extend([
            "</section>", '<p><a href="examples/index.html">Collected examples</a></p>',
            "</main>",
        ])
        return self._document("Research overview", "".join(body), "")

    def _render_run(self, snapshot: ResearchSnapshot, run: ResearchSnapshotRun) -> str:
        """Build one run page with metadata, metrics, and compact samples.

        Args:
            snapshot: Snapshot containing all compact samples and relations.
            run: Run view whose details are displayed.

        Returns:
            Complete HTML document with paths relative to ``runs/``.
        """
        body = ["<main>", '<p><a href="../index.html">← Research overview</a></p>',
                f"<h1>{self._text(run.run_id)}</h1>", "<section><h2>Research</h2><dl>"]
        for label, value in (
            ("Hypothesis", run.hypothesis),
            ("Motivation", self._motivation(run)),
            ("Execution status", run.execution_status),
            ("Review status", run.review_status),
            ("Started", run.started_at.isoformat() if run.started_at else "Not recorded"),
            ("Finished", run.finished_at.isoformat() if run.finished_at else "Not recorded"),
        ):
            body.append(f"<dt>{label}</dt><dd>{self._text(value or 'Not recorded')}</dd>")
        body.append("</dl>")
        if run.params:
            body.extend(["<h3>Parameters</h3>", f"<pre><code>{self._text(self._json(run.params))}</code></pre>"])
        body.append("</section><section><h2>Review</h2>")
        body.append(f"<p><strong>Conclusion:</strong> {self._text(run.conclusion or 'Not recorded')}</p>")
        body.append(f"<p><strong>Next step:</strong> {self._text(run.next_step or 'Not recorded')}</p>")
        body.append("</section><section><h2>Metrics</h2>")
        if run.metrics:
            body.append("<div class=\"table-wrap\"><table><thead><tr><th>Step</th><th>Metric</th><th>Value</th></tr></thead><tbody>")
            for metric in run.metrics:
                body.append("<tr>" + "".join(
                    f"<td>{self._text(metric.get(key, ''))}</td>" for key in ("step", "metric_name", "metric_value")
                ) + "</tr>")
            body.append("</tbody></table></div>")
        else:
            body.append("<p>No metrics recorded.</p>")
        run_samples = [sample for sample in snapshot.samples if sample.get("run_id") == run.run_id]
        body.extend(["</section><section><h2>Collected examples</h2>"])
        if run_samples:
            for sample in run_samples:
                body.append(f"<pre><code>{self._text(self._json(sample))}</code></pre>")
        else:
            body.append("<p>No compact diagnostic examples recorded.</p>")
        body.extend(["</section>", "</main>"])
        return self._document(f"{run.run_id} — Research run", "".join(body), "../")

    def _render_examples(self, snapshot: ResearchSnapshot, root_prefix: str) -> str:
        """Render the compact diagnostic sample catalogue.

        Args:
            snapshot: Snapshot containing compact sample records.
            root_prefix: Relative prefix from the examples page to the site root.
        """
        body = ["<main>", f'<p><a href="{root_prefix}index.html">← Research overview</a></p>',
                "<h1>Collected examples</h1>",
                "<p>These are compact diagnostic records, not source datasets or serialized domain objects.</p>"]
        if snapshot.samples:
            for index, sample in enumerate(snapshot.samples, start=1):
                body.append(f"<section><h2>Example {index}</h2><pre><code>{self._text(self._json(sample))}</code></pre></section>")
        else:
            body.append("<p>No compact diagnostic examples have been collected.</p>")
        body.append("</main>")
        return self._document("Collected examples", "".join(body), root_prefix)

    @staticmethod
    def _document(title: str, body: str, root_prefix: str) -> str:
        """Wrap HTML body in a complete document with a relative stylesheet link."""
        return (
            "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{html.escape(title)}</title><link rel=\"stylesheet\" href=\"{root_prefix}style.css\">"
            f"</head><body>{body}</body></html>\n"
        )

    @staticmethod
    def _stylesheet() -> str:
        """Return the self-contained site's small, framework-free CSS stylesheet."""
        return """*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#202938;font:16px/1.6 system-ui,-apple-system,sans-serif}main{max-width:960px;margin:0 auto;padding:2rem 1.25rem}h1,h2,h3{line-height:1.25}h1{margin-top:.5rem}section,article{background:#fff;border:1px solid #dce2ea;border-radius:10px;padding:1rem 1.25rem;margin:1rem 0}a{color:#1557a6}a:focus,a:hover{text-decoration-thickness:2px}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.75rem}.summary div{background:#eef3f8;border-radius:7px;padding:.75rem}.summary dt{font-size:.85rem;color:#536174}.summary dd{font-size:1.5rem;font-weight:700;margin:0}.history li{padding:.25rem 0}.status{display:inline-block;background:#eef3f8;border-radius:4px;padding:0 .4rem;font-size:.85rem}pre{overflow:auto;background:#f0f3f7;border-radius:7px;padding:1rem}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.9em}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{text-align:left;border-bottom:1px solid #dce2ea;padding:.5rem}.finding.error{color:#9d2020}.finding.warning{color:#805300}@media(max-width:600px){main{padding:1rem .75rem}section{padding:.8rem}}"""

    @staticmethod
    def _motivation(run: ResearchSnapshotRun) -> str:
        """Format existing motivation fields without inventing relationships."""
        motivation_type = run.motivation.get("type", "unknown")
        reference = run.motivation.get("reference")
        return f"{motivation_type} (reference: {reference})" if reference else str(motivation_type)

    @staticmethod
    def _safe_id(value: str) -> str:
        """Restrict run identifiers to safe filename characters."""
        safe = "".join(char if char.isalnum() or char in "-_." else "_" for char in value)
        return safe.strip("._") or "run"

    @staticmethod
    def _text(value: Any) -> str:
        """HTML-escape arbitrary snapshot values for text-node contexts."""
        return html.escape(str(value), quote=False)

    @staticmethod
    def _attr(value: Any) -> str:
        """HTML-escape arbitrary snapshot values for attribute contexts."""
        return html.escape(str(value), quote=True)

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        """Serialize a compact mapping as stable, readable JSON."""
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
