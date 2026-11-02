# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Render metric histories as self-contained SVG charts."""
from collections.abc import Mapping, Sequence
from html import escape
import math


class MetricRenderer:
    """Create simple SVG line charts without third-party plotting dependencies."""

    def render(self, series: Mapping[str, Sequence[float | int | None]], *, width: int = 720, height: int = 260,
               max_points: int = 1000) -> str:
        """Render named sequences; None values create gaps and long histories are downsampled."""
        if width < 240 or height < 140: raise ValueError("chart dimensions are too small")
        if max_points < 2: raise ValueError("max_points must be at least 2")
        bounded = {}
        for name, values in series.items():
            if len(values) > max_points:
                stride = (len(values) - 1) / (max_points - 1)
                bounded[name] = [values[round(index * stride)] for index in range(max_points)]
            else:
                bounded[name] = values
        series = bounded
        numeric = [float(v) for values in series.values() for v in values if v is not None and math.isfinite(float(v))]
        if not numeric: return '<p class="remgu-empty">No metric measurements available.</p>'
        low, high = min(numeric), max(numeric)
        if low == high: low -= .5; high += .5
        left, right, top, bottom = 54, width-18, 18, height-42
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Metric history">',
                 f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#64748b"/>',
                 f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#64748b"/>',
                 f'<text x="6" y="{top+8}" font-size="11">{high:.4g}</text>', f'<text x="6" y="{bottom}" font-size="11">{low:.4g}</text>']
        palette = ["#2563eb", "#dc2626", "#059669", "#9333ea", "#d97706"]
        for si, (name, values) in enumerate(series.items()):
            points=[]
            for i, value in enumerate(values):
                if value is None or not math.isfinite(float(value)):
                    if len(points)>1: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{palette[si%len(palette)]}" stroke-width="2"/>')
                    points=[]; continue
                x=left if len(values)<2 else left+(right-left)*i/(len(values)-1); y=bottom-(float(value)-low)/(high-low)*(bottom-top)
                points.append(f"{x:.2f},{y:.2f}")
            if len(points)>1: parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{palette[si%len(palette)]}" stroke-width="2"/>')
            parts.append(f'<text x="{left+8}" y="{top+14+si*14}" font-size="11" fill="{palette[si%len(palette)]}">{escape(str(name))}</text>')
        parts.append("</svg>"); return "".join(parts)
