# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Render already-projected 2D embeddings without performing dimensionality reduction."""
from html import escape
import math
from collections.abc import Iterable, Mapping
from itertools import islice


from remgu.visualization.renderer import Renderer

class EmbeddingRenderer(Renderer):
    """Draw bounded 2D points; projection/training remains the caller's responsibility."""

    def render(self, points: Iterable[Mapping[str, object]], *, max_points: int = 2000) -> str:
        """Render points with numeric x/y and optional label/group fields as SVG."""
        if max_points < 1: raise ValueError("max_points must be positive")
        rows = list(islice(iter(points), max_points + 1))
        truncated = len(rows) > max_points
        rows = rows[:max_points]
        parsed = []
        for row in rows:
            if "x" not in row or "y" not in row: raise ValueError("each point requires x and y")
            x, y = float(row["x"]), float(row["y"])
            if not math.isfinite(x) or not math.isfinite(y): raise ValueError("coordinates must be finite")
            parsed.append((x, y, str(row.get("label", "")), str(row.get("group", "default"))))
        if not parsed: return '<p class="remgu-empty">No embedding points available.</p>'
        xmin, xmax = min(p[0] for p in parsed), max(p[0] for p in parsed)
        ymin, ymax = min(p[1] for p in parsed), max(p[1] for p in parsed)
        if xmin == xmax: xmax += 1
        if ymin == ymax: ymax += 1
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 480" role="img" aria-label="Embedding projection">']
        for x, y, label, group in parsed:
            px = 30 + (x-xmin)/(xmax-xmin)*660; py = 30 + (1-(y-ymin)/(ymax-ymin))*420
            parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#2563eb"><title>{escape(label)} ({escape(group)})</title></circle>')
        if truncated: parts.append(f'<text x="12" y="18" font-size="11">Showing first {max_points} points</text>')
        parts.append("</svg>"); return "".join(parts)
