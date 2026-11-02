# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Common contract for ReMgu output renderers."""


class Renderer:
    """Base class for components that convert research data into a representation."""

    def render(self, data: object, **options: object) -> str:
        """Render ``data`` into a string representation. Subclasses must implement this."""
        raise NotImplementedError(f"{type(self).__name__} must implement render()")
