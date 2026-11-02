# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Render GraphWorld as DOT, an edge list, or SVG."""
from html import escape
import math
from remgu.simulation.graph_world import GraphWorld


from remgu.visualization.renderer import Renderer

class GraphRenderer(Renderer):
    """Provide compact dependency-free graph representations."""

    def render(self, data: GraphWorld, **options: object) -> str:
        """Render a graph as SVG; use ``to_dot`` for DOT source."""
        return self.to_svg(data, **options)

    def to_dot(self, world: GraphWorld, *, max_nodes: int = 500) -> str:
        """Return a Graphviz DOT string for a bounded subgraph."""
        if max_nodes < 1: raise ValueError("max_nodes must be positive")
        nodes = world.node_ids[:max_nodes]; selected = set(nodes); lines = ["graph RemguGraph {"]
        for node in nodes: lines.append(f'  n{node} [label="{node} (c{world.communities[node]})"];')
        for left, right in world.edges:
            if left in selected and right in selected: lines.append(f"  n{left} -- n{right};")
        if len(world.node_ids) > max_nodes: lines.append(f"  // truncated: {len(world.node_ids)-max_nodes} nodes omitted")
        lines.append("}"); return "\n".join(lines)

    def to_edge_list(self, world: GraphWorld, *, max_edges: int = 500) -> str:
        """Return a bounded text edge list."""
        if max_edges < 0: raise ValueError("max_edges must be non-negative")
        lines = [f"Graph: {len(world.node_ids)} nodes, {len(world.edges)} edges"]
        lines.extend(f"{left} -- {right}" for left, right in world.edges[:max_edges])
        if len(world.edges) > max_edges: lines.append(f"... {len(world.edges)-max_edges} edges omitted")
        return "\n".join(lines)

    def to_svg(self, world: GraphWorld, *, max_nodes: int = 80) -> str:
        """Render a bounded graph with a deterministic circular layout."""
        if max_nodes < 1: raise ValueError("max_nodes must be positive")
        nodes = list(world.node_ids[:max_nodes]); selected = set(nodes); width, height = 800, 520
        if not nodes: return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 120"></svg>'
        positions = {node: (width/2 + 210*math.cos(2*math.pi*i/len(nodes)), height/2 + 190*math.sin(2*math.pi*i/len(nodes))) for i, node in enumerate(nodes)}
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Graph">']
        for left, right in world.edges:
            if left in selected and right in selected:
                x1,y1=positions[left]; x2,y2=positions[right]; parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#94a3b8"/>')
        for node in nodes:
            x,y=positions[node]; parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="18" fill="#dbeafe" stroke="#1d4ed8"/>')
            parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="12">{escape(str(node))}</text>')
        if len(world.node_ids)>max_nodes: parts.append(f'<text x="10" y="20">{len(world.node_ids)-max_nodes} nodes omitted</text>')
        parts.append("</svg>"); return "".join(parts)
