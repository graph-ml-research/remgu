# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Dependency-free HTML table renderer."""
from collections.abc import Iterable, Mapping
from html import escape
from itertools import islice
from typing import Any


class TableRenderer:
    """Render mappings or sequences as an HTML table with escaped cells."""

    def render(self, rows: Iterable[Mapping[str, Any] | Iterable[Any]], columns: Iterable[str] | None = None,
               *, max_rows: int = 200) -> str:
        """Render a bounded number of rows without interpreting cells as markup."""
        if max_rows < 1: raise ValueError("max_rows must be positive")
        materialized = list(islice(iter(rows), max_rows + 1))
        truncated = len(materialized) > max_rows
        materialized = materialized[:max_rows]
        selected = list(columns) if columns is not None else None
        if selected is None:
            if materialized and isinstance(materialized[0], Mapping):
                selected = list(materialized[0].keys())
            elif materialized:
                selected = [f"Column {index + 1}" for index in range(len(materialized[0]))]
            else:
                selected = []
        parts = ['<table class="remgu-table"><thead><tr>']
        parts.extend(f"<th>{escape(str(column))}</th>" for column in selected)
        parts.append("</tr></thead><tbody>")
        for row in materialized:
            parts.append("<tr>")
            values = list(row) if not isinstance(row, Mapping) else []
            for index, column in enumerate(selected):
                value = row.get(column, "") if isinstance(row, Mapping) else (values[index] if index < len(values) else "")
                parts.append(f"<td>{escape(str(value))}</td>")
            parts.append("</tr>")
        if truncated:
            parts.append(f'<tr><td colspan="{max(1, len(selected))}">Additional rows omitted (limit: {max_rows}).</td></tr>')
        parts.append("</tbody></table>")
        return "".join(parts)
