# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Safe HTML rendering for plain text."""
from html import escape


from remgu.visualization.renderer import Renderer

class TextRenderer(Renderer):
    """Render untrusted text as escaped HTML."""

    def render(self, value: object, *, css_class: str = "remgu-text") -> str:
        """Return an escaped text block; CSS class is supplied by trusted code."""
        return f'<pre class="{escape(css_class, quote=True)}">{escape(str(value))}</pre>'
