# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Small dependency-free SVG renderer for a safe subset of Graphviz DOT."""
from html import escape
import re


class DotSvgRenderer:
    """Render simple DOT node and edge declarations into a self-contained SVG."""
    _NODE = re.compile(r'(?m)^\s*([A-Za-z0-9_.:-]+)\s*\[(?:label\s*=\s*"([^"]*)")?[^\]]*\]\s*;?\s*$')
    _EDGE = re.compile(r'(?m)^\s*([A-Za-z0-9_.:-]+)\s*(?:->|--)\s*([A-Za-z0-9_.:-]+)(?:\s*\[[^\]]*\])?\s*;?\s*$')

    def render(self, dot: str, *, max_nodes: int = 80) -> str:
        """Render supported DOT statements; fail explicitly for unsupported/large input."""
        if not isinstance(dot, str) or not re.search(r'\b(?:di)?graph\b', dot):
            raise ValueError("input must be Graphviz DOT text")
        if max_nodes < 1:
            raise ValueError("max_nodes must be positive")
        nodes, edges = {}, []
        body = re.sub(r"^\s*(?:di)?graph\s+[A-Za-z0-9_]*\s*\{", "", dot.strip(), count=1)
        body = body.rsplit("}", 1)[0]
        for statement in body.split(";"):
            statement = statement.strip()
            if not statement or statement.startswith("//") or statement.startswith("#"):
                continue
            edge_match = re.fullmatch(r'([A-Za-z0-9_.:-]+)\s*(?:->|--)\s*([A-Za-z0-9_.:-]+)(?:\s*\[[^\]]*\])?', statement)
            if edge_match:
                left, right = edge_match.groups()
                nodes.setdefault(left, left); nodes.setdefault(right, right); edges.append((left, right))
                continue
            node_match = re.fullmatch(r'([A-Za-z0-9_.:-]+)\s*\[(.*)\]', statement)
            if node_match:
                node_id, attributes = node_match.groups()
                label_match = re.search(r'\blabel\s*=\s*"([^"]*)"', attributes)
                nodes[node_id] = label_match.group(1) if label_match else node_id
        if not nodes:
            raise ValueError("DOT contains no supported node or edge declarations")
        if len(nodes) > max_nodes:
            raise ValueError(f"graph has {len(nodes)} nodes; limit is {max_nodes}")
        ordered = sorted(nodes); width = 800; height = max(140, 100 * ((len(ordered) + 3) // 4)); positions = {}
        for index, node_id in enumerate(ordered):
            positions[node_id] = (100 + (index % 4) * 195, 50 + (index // 4) * 100)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Model architecture graph">']
        for left, right in edges:
            x1, y1 = positions[left]; x2, y2 = positions[right]
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748b" stroke-width="2"/>')
        for node_id in ordered:
            x, y = positions[node_id]
            parts.append(f'<rect x="{x-70}" y="{y-22}" width="140" height="44" rx="8" fill="#e2e8f0" stroke="#475569"/>')
            parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#0f172a">{escape(nodes[node_id][:48])}</text>')
        parts.append("</svg>")
        return "".join(parts)
