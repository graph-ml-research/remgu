# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Generic text renderer for any simulation world implementing its shared contract."""
from html import escape

from remgu.simulation.simulation_world import SimulationWorld
from remgu.visualization.renderer import Renderer


class WorldRenderer(Renderer):
    """Render a world through its generic summary and text representation.

    Domain-specific renderers, such as ``GraphRenderer``, can provide richer visual
    layouts. This renderer is a fallback that also works for future text or user-history
    worlds as long as they implement ``SimulationWorld``.
    """

    def render(self, data: SimulationWorld, *, max_chars: int = 12000) -> str:
        """Return escaped HTML containing a summary and bounded text view."""
        if not isinstance(data, SimulationWorld):
            raise TypeError("data must implement SimulationWorld")
        if max_chars < 1:
            raise ValueError("max_chars must be positive")
        text = data.to_text()
        truncated = len(text) > max_chars
        text = text[:max_chars]
        if truncated:
            text += "\n… (output truncated)"
        return (f'<section class="remgu-world"><h3>{escape(data.summary())}</h3>'
                f'<pre>{escape(text)}</pre></section>')
