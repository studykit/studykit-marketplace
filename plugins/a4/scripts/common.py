"""Shared helpers for a4 scripts.

Imported by sibling scripts (validators, transition_status, search, ...) and
transitively by the hook dispatcher `a4_hook.py`. Contains pure,
behavior-identical extractions of helpers that were previously duplicated
across multiple scripts. Markdown parsing (frontmatter split, parsed
document dataclass) lives in the sibling `markdown.py` module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

WIKI_TYPES = frozenset(
    {"context", "domain", "architecture", "actors", "nfr", "roadmap", "bootstrap"}
)

ISSUE_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "review",
    "spec",
    "idea",
)

# Issue folders that hold kind-scoped subfolders. Files live one level
# deeper (e.g. `task/feature/<id>-<slug>.md`), so discovery and
# back-scans must recurse rather than glob a flat `*.md`.
NESTED_ISSUE_FOLDERS: frozenset[str] = frozenset({"task"})


def issue_glob(folder: str) -> str:
    """Glob pattern to enumerate `.md` files in an issue folder."""
    return "**/*.md" if folder in NESTED_ISSUE_FOLDERS else "*.md"


def iter_issue_files(a4_dir: Path, folder: str) -> list[Path]:
    """Sorted `.md` files in an issue folder, recursing for kind subfolders.

    Folders in `NESTED_ISSUE_FOLDERS` (currently `task`) descend into kind
    subfolders (`task/feature/`, `task/bug/`, `task/spike/`); others stay
    flat. Returns `[]` if the folder is absent.
    """
    sub = a4_dir / folder
    if not sub.is_dir():
        return []
    return sorted(sub.glob(issue_glob(folder)))


def discover_files(a4_dir: Path) -> list[Path]:
    """All a4/*.md files the validators should scan.

    Top-level wiki pages + every file in each issue folder (recursing into
    kind subfolders for `NESTED_ISSUE_FOLDERS`) + every file in `spark/`.
    Order is deterministic: wiki pages first, then issue folders in
    ISSUE_FOLDERS order, then sparks.
    """
    out: list[Path] = list(sorted(a4_dir.glob("*.md")))
    for folder in ISSUE_FOLDERS:
        out.extend(iter_issue_files(a4_dir, folder))
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
