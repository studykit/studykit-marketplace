"""a4 workspace markdown validators.

Library home for the validator categories:

  - ``frontmatter`` — YAML schema (required fields, enums, types,
    path-reference format, wiki ``type:`` matches filename, id
    uniqueness).
  - ``status_consistency`` — cross-file derived status (``superseded``,
    ``promoted``, cascaded ``discarded``).
  - ``transitions`` — git-diff-based status transition legality (HEAD
    vs working tree). Safety net for hand edits that bypass
    ``transition_status.py``.

Plus a shared resolver:

  - ``refs`` — translate any accepted reference form (``#<id>``,
    ``<folder>/<id>``, ``<folder>/<id>-<slug>``, bare ``<id>-<slug>``,
    wiki basename, spark stem) into a single ``ResolvedRef``.

The unified CLI lives at ``scripts/validate.py`` and dispatches via the
``CHECKS`` registry exported from ``markdown_validator.registry``. The
hook dispatcher (``scripts/a4_hook.py``) imports the submodules
directly when it needs category-specific output shapes.
"""

from __future__ import annotations

from . import frontmatter, refs, registry, status_consistency, transitions
from .refs import RefIndex, ResolvedRef
from .registry import CHECKS, Check, Issue

__all__ = [
    "frontmatter",
    "refs",
    "status_consistency",
    "transitions",
    "registry",
    "CHECKS",
    "Check",
    "Issue",
    "RefIndex",
    "ResolvedRef",
]
