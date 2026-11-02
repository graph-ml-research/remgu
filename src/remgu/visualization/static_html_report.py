# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Generate a self-contained, safe static HTML report for an experiment."""
from __future__ import annotations
from html import escape
import json
from pathlib import Path
from typing import Any
from remgu.visualization.graph_renderer import GraphRenderer
from remgu.visualization.dot_svg_renderer import DotSvgRenderer
from remgu.visualization.metric_renderer import MetricRenderer
from remgu.visualization.table_renderer import TableRenderer
from remgu.visualization.text_renderer import TextRenderer
from remgu.example.example_report_selector import ExampleReportSelector


class StaticHtmlReport:
    """Write an offline HTML report from a simulation result or JSON-compatible mapping."""

    def __init__(self) -> None:
        """Initialize dependency-free renderers."""
        self.graph_renderer = GraphRenderer()
        self.dot_renderer = DotSvgRenderer()
        self.metric_renderer = MetricRenderer()
        self.table_renderer = TableRenderer()
        self.text_renderer = TextRenderer()
        self.example_selector = ExampleReportSelector(limit=100)

    def render(self, result: Any, output: str | Path, *, examples: list[dict[str, Any]] | None = None,
               events: list[dict[str, Any]] | None = None, resource_summary: dict[str, Any] | None = None,
               architecture_dot: str | None = None, metric_history: dict[str, list[float | int | None]] | None = None) -> Path:
        """Write a standalone HTML report and return its path.

        Args:
            result: ``SimulationResult`` or a mapping containing its serialized fields.
            output: Destination HTML path.
            examples: Optional selected examples to display without changing source data.
            events: Optional structured diagnostics, including Probe events.
            resource_summary: Optional observed duration and peak resource measurements.
        """
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        metrics = data.get("metrics") or {}
        rows = [{"Metric": key, "Value": value} for key, value in metrics.items()]
        checks = data.get("checks") or []
        resources = resource_summary or data.get("resource_summary") or {}
        duration = resources.get("duration_seconds", data.get("duration_seconds"))
        peak_ram = resources.get("peak_ram_bytes_process")
        peak_vram = resources.get("peak_vram_bytes_device")
        resource_rows = [{"Metric": "Total duration (seconds)", "Value": duration if duration is not None else "not measured"},
                         {"Metric": "Peak process RAM (bytes)", "Value": peak_ram if peak_ram is not None else "not measured"},
                         {"Metric": "Peak device VRAM (bytes)", "Value": peak_vram if peak_vram is not None else "not measured"}]
        graph_svg = ""
        architecture_svg = "<p>Architecture introspection unavailable.</p>"
        if architecture_dot:
            try:
                architecture_svg = self.dot_renderer.render(architecture_dot)
            except ValueError:
                architecture_svg = "<p>Architecture visualization unavailable for this DOT subset.</p>"
        metric_history_svg = self.metric_renderer.render(metric_history or {})
        world_data = data.get("world") or {}
        if world_data.get("adjacency"):
            try:
                from remgu.simulation.graph_world import GraphWorld
                adjacency = {int(key): value for key, value in world_data["adjacency"].items()}
                features = {int(key): value for key, value in world_data["features"].items()}
                communities = {int(key): value for key, value in world_data["communities"].items()}
                bridge = world_data.get("critical_bridge")
                world = GraphWorld(adjacency, features, communities, tuple(bridge) if bridge else None)
                graph_svg = self.graph_renderer.to_svg(world)
            except (KeyError, TypeError, ValueError):
                graph_svg = "<p>Graph visualization unavailable.</p>"
        safe_title = escape(str(data.get("experiment_id", "Experiment")))
        checks_html = self.table_renderer.render(checks) if checks else "<p>No checks recorded.</p>"
        example_records = examples if examples is not None else data.get("examples", data.get("selected_examples", []))
        selected_examples = self.example_selector.select(example_records or [])
        examples_html = self.table_renderer.render(selected_examples, max_rows=100) if selected_examples else "<p>No examples selected.</p>"
        if selected_examples:
            examples_html = examples_html.replace('<table class="remgu-table">', '<table id="examples-table" class="remgu-table">', 1)
            examples_html += '<p id="examples-page-status" aria-live="polite"></p><button type="button" id="examples-prev">Previous</button> <button type="button" id="examples-next">Next</button>' 
        events_html = self.table_renderer.render(events or []) if events else "<p>No diagnostic events recorded.</p>"
        display_data = dict(data)
        source_examples = data.get("examples", data.get("selected_examples", []))
        display_data.pop("examples", None)
        display_data.pop("selected_examples", None)
        if source_examples:
            display_data["examples_summary"] = {"source_count": len(source_examples), "selected_count": len(selected_examples)}
        if world_data:
            display_data["world"] = {"node_count": len(world_data.get("adjacency", {})),
                                     "edge_count": sum(len(neighbors) for neighbors in world_data.get("adjacency", {}).values()) // 2,
                                     "critical_bridge": world_data.get("critical_bridge")}
        if isinstance(display_data.get("predictions"), dict) and len(display_data["predictions"]) > 100:
            predictions = display_data["predictions"]
            display_data["predictions"] = dict(list(predictions.items())[:100])
            display_data["predictions_truncated"] = len(predictions) - 100
        serialized = self.text_renderer.render(json.dumps(display_data, ensure_ascii=False, indent=2), css_class="json-data")
        html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReMgu report — {safe_title}</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#172033}}section{{margin:1.5rem 0;padding:1rem;border:1px solid #d6dbe4;border-radius:10px;overflow:auto}}h1,h2{{line-height:1.2}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;border-bottom:1px solid #d6dbe4;padding:.45rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:1rem}}svg{{max-width:100%;height:auto}}.status{{font-weight:700}}
</style></head><body><h1>ReMgu experiment report: {safe_title}</h1>
<p class="status">Status: {escape(str(data.get("status", "unknown")))}</p>
<section><h2>Metrics</h2>{self.table_renderer.render(rows) if rows else "<p>No metrics recorded.</p>"}{metric_history_svg}</section>
<section><h2>Resources (historical)</h2><p>Current live usage is available only in server dashboard mode.</p>{self.table_renderer.render(resource_rows)}</section>
<section><h2>Graph</h2>{graph_svg or "<p>Graph data unavailable.</p>"}</section><section><h2>Model architecture</h2>{architecture_svg}</section>
<section><h2>Checks</h2>{checks_html}</section><section><h2>Examples</h2>{examples_html}</section>
<section><h2>Probe and diagnostic events</h2>{events_html}</section>
<section><h2>Configuration and raw result</h2>{serialized}</section><script>const et=document.querySelector("#examples-table");if(et){{const rows=Array.from(et.querySelectorAll("tbody tr"));let page=0;const size=10;const render=()=>{{rows.forEach((r,i)=>r.hidden=i<page*size||i>=(page+1)*size);document.getElementById("examples-page-status").textContent=`Page ${{page+1}} of ${{Math.max(1,Math.ceil(rows.length/size))}}`;document.getElementById("examples-prev").disabled=page===0;document.getElementById("examples-next").disabled=(page+1)*size>=rows.length;}};document.getElementById("examples-prev").addEventListener("click",()=>{{page=Math.max(0,page-1);render()}});document.getElementById("examples-next").addEventListener("click",()=>{{if((page+1)*size<rows.length)page++;render()}});render();}}</script></body></html>'''
        destination.write_text(html, encoding="utf-8")
        return destination
