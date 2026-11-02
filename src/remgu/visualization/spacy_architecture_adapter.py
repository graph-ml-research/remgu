# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional adapter for spaCy-like processing pipelines."""
from html import escape


from remgu.visualization.architecture_adapter import ArchitectureAdapter

class SpacyPipelineArchitectureAdapter(ArchitectureAdapter):
    """Describe pipeline components as an ordered processing chain."""

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a DOT pipeline when ``pipe_names`` is available."""
        names = getattr(model, "pipe_names", None)
        if names is None: return None
        names = list(names)
        if not names: return None
        lines = ["digraph SpacyPipeline {"]
        for index, name in enumerate(names):
            lines.append(f'  pipe{index} [label="{escape(str(name), quote=True)}"];')
            if index: lines.append(f"  pipe{index-1} -> pipe{index};")
        lines.append("}")
        return "\n".join(lines)
