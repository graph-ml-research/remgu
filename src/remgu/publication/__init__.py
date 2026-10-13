# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Publication adapters for ReMgu research snapshots."""

from .archive_adapter import ArchiveAdapter
from .markdown_adapter import MarkdownAdapter
from .static_site_adapter import StaticSiteAdapter

__all__ = ["ArchiveAdapter", "MarkdownAdapter", "StaticSiteAdapter"]
