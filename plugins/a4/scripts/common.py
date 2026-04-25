"""Shared helpers for a4 scripts.

Imported by sibling scripts (validators, refresh_implemented_by, ...) and
transitively by the hook dispatcher `a4_hook.py`. Contains pure,
behavior-identical extractions of helpers that were previously duplicated
across multiple scripts. Markdown parsing (frontmatter split, parsed
document dataclass) lives in the sibling `markdown.py` module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

WIKI_KINDS = frozenset(
    {"context", "domain", "architecture", "actors", "nfr", "roadmap", "bootstrap"}
)

ISSUE_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "review",
    "decision",
    "idea",
)


def discover_files(a4_dir: Path) -> list[Path]:
    """All a4/*.md files the validators should scan.

    Top-level wiki pages + every file in each issue folder + every file in
    `spark/`. Order is deterministic: wiki pages first, then issue folders
    in ISSUE_FOLDERS order, then sparks.
    """
    out: list[Path] = list(sorted(a4_dir.glob("*.md")))
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if sub.is_dir():
            out.extend(sorted(sub.glob("*.md")))
    spark = a4_dir / "spark"
    if spark.is_dir():
        out.extend(sorted(spark.glob("*.md")))
    return out


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
