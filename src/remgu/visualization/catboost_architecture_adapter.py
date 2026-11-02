# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Optional compact ensemble summary for CatBoost-like models."""


from remgu.visualization.architecture_adapter import ArchitectureAdapter

class CatBoostArchitectureAdapter(ArchitectureAdapter):
    """Represent an ensemble as a bounded set of tree nodes, not individual split graphs."""

    def __init__(self, max_trees: int = 40) -> None:
        """Set a hard upper bound on the number of tree nodes rendered."""
        if max_trees < 1: raise ValueError("max_trees must be positive")
        self.max_trees = max_trees

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a compact DOT ensemble summary when tree count is available."""
        count = getattr(model, "tree_count_", None)
        if count is None:
            getter = getattr(model, "get_tree_count", None)
            count = getter() if callable(getter) else None
        if count is None: return None
        count = int(count)
        if count < 1: return None
        shown = min(count, self.max_trees)
        lines = ["digraph CatBoostEnsemble {", f'  ensemble [label="Ensemble: {count} trees"];']
        for index in range(shown):
            lines.append(f'  tree{index} [label="Tree {index}"];')
            lines.append(f"  ensemble -> tree{index};")
        if count > shown: lines.append(f'  more [label="{count-shown} additional trees omitted"]; ensemble -> more;')
        lines.append("}")
        return "\n".join(lines)
