# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional duck-typed adapter for Keras-like sequential layer collections."""
from html import escape


from remgu.visualization.architecture_adapter import ArchitectureAdapter

class KerasArchitectureAdapter(ArchitectureAdapter):
    """Describe the exposed Keras layer order without importing TensorFlow/Keras."""

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a sequential DOT view when a non-empty ``layers`` sequence exists."""
        layers = getattr(model, "layers", None)
        if layers is None: return None
        layers = list(layers)
        if not layers: return None
        lines = ["digraph KerasLayers {"]
        for index, layer in enumerate(layers):
            name = getattr(layer, "name", type(layer).__name__)
            label = escape(f"{name}\\n{type(layer).__name__}", quote=True)
            lines.append(f'  layer{index} [label="{label}"];')
            if index: lines.append(f"  layer{index-1} -> layer{index};")
        lines.append("}")
        return "\n".join(lines)
