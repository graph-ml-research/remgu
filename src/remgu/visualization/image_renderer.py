# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Render self-contained images in static HTML."""
from html import escape
import re


class ImageRenderer:
    """Render a relative local image path or a base64 data image URI."""
    _DATA_URI = re.compile(r"^data:image/(png|jpeg|gif|webp|svg\+xml);base64,[A-Za-z0-9+/=\r\n]+$")

    def render(self, source: str, alt: str, *, max_width: int = 720) -> str:
        """Create an image tag after validating source and width."""
        if max_width < 1:
            raise ValueError("max_width must be positive")
        local = bool(source and not source.startswith(("/", "\\")) and ":" not in source
                     and "\\" not in source and ".." not in source.split("/")
                     and not any(ord(char) < 32 for char in source))
        if not (self._DATA_URI.fullmatch(source) or local):
            raise ValueError("source must be a relative local path or supported base64 image data URI")
        return (f'<img src="{escape(source, quote=True)}" alt="{escape(alt, quote=True)}" '
                f'style="max-width:{int(max_width)}px;width:100%;height:auto">')
