# -*- coding: utf8 -*-
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any


__author__ = 'Mstislav Maslennikov'

@dataclass(frozen=True)
class Motivation:
    type: str
    reference: str | None = None


@dataclass
class ResearchMetadata:
    hypothesis: str
    motivation: Motivation


@dataclass
class Execution:
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: dict[str, str] | None = None


@dataclass
class Review:
    status: str = "needs_review"
    conclusion: str | None = None
    next_step: str | None = None
