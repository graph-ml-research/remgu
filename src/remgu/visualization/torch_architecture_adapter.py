# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional duck-typed adapter for PyTorch-like named-module models."""
from html import escape


from remgu.visualization.architecture_adapter import ArchitectureAdapter

class TorchArchitectureAdapter(ArchitectureAdapter):
    """Build a DOT module hierarchy without importing PyTorch as a dependency."""

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a module-hierarchy DOT graph when ``named_modules`` is available."""
        getter = getattr(model, "named_modules", None)
        if not callable(getter): return None
        modules = list(getter())
        if not modules: return None
        ids = {name: f"m{index}" for index, (name, _) in enumerate(modules)}
        lines = ["digraph PyTorchModules {"]
        for name, module in modules:
            label = (name or "model") + "\\n" + type(module).__name__
            lines.append(f'  {ids[name]} [label="{escape(label, quote=True)}"];')
        for name, _ in modules:
            if not name: continue
            parent = name.rpartition(".")[0]
            if parent in ids: lines.append(f"  {ids[parent]} -> {ids[name]};")
            elif "" in ids: lines.append(f"  {ids['']} -> {ids[name]};")
        lines.append("}")
        return "\n".join(lines)
