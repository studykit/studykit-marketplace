#!/usr/bin/env python3
"""Shared ``EditTarget`` value type for workflow hook write paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EditTarget:
    """Potential local workflow write target."""

    path: Path
    content: str | None = None
