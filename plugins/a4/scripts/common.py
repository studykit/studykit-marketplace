"""Shared helpers for a4 scripts.

Imported by sibling scripts (validators, refresh_implemented_by, ...) and
transitively by the hook dispatcher `a4_hook.py`. Only contains pure,
behavior-identical extractions of helpers that were previously duplicated
verbatim across multiple scripts. Signature-sensitive helpers such as
`split_frontmatter` still live in their originating modules pending a
later consolidation pass.
"""

from __future__ import annotations

from typing import Any

WIKI_KINDS = frozenset(
    {"context", "domain", "architecture", "actors", "nfr", "plan", "bootstrap"}
)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(x, str) and x.strip() for x in value
    )


def normalize_ref(ref: Any) -> str | None:
    """Normalize a frontmatter path reference for comparison.

    Strips a trailing `.md` so file-on-disk paths can be compared against
    frontmatter-declared references. Returns None for non-strings or empty
    strings.
    """
    if not isinstance(ref, str):
        return None
    cleaned = ref.strip()
    if not cleaned:
        return None
    if cleaned.endswith(".md"):
        cleaned = cleaned[:-3]
    return cleaned
