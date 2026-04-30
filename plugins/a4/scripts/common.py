"""Shared helpers for a4 scripts.

Imported by sibling scripts (validators, status_cascade, search, ...) and
transitively by the hook dispatcher `a4_hook.py`. Contains pure,
behavior-identical extractions of helpers that were previously duplicated
across multiple scripts. Markdown parsing (frontmatter split, parsed
document dataclass) lives in the sibling `markdown.py` module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from markdown import read_fm

WIKI_TYPES = frozenset(
    {"context", "domain", "architecture", "actors", "nfr", "roadmap", "bootstrap"}
)

# Top-level issue folders under `<a4-dir>/`. a4 v12.0.0 split the former
# combined `task/` folder (with a `kind:` discriminator) into four flat
# sibling top-level folders (`task`, `bug`, `spike`, `research`) — each
# is its own issue family with its own type literal. Iteration order
# matches a coarse topological flow (UC → task families → reviews → specs
# → ideas).
ISSUE_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "bug",
    "spike",
    "research",
    "review",
    "spec",
    "idea",
    "brainstorm",
)


def iter_issue_files(a4_dir: Path, folder: str) -> list[Path]:
    """Sorted `.md` files in an issue folder.

    All issue folders are flat after a4 v12.0.0. Returns `[]` if the
    folder is absent.
    """
    sub = a4_dir / folder
    if not sub.is_dir():
        return []
    return sorted(sub.glob("*.md"))


def discover_files(a4_dir: Path) -> list[Path]:
    """All a4/*.md files the validators should scan.

    Top-level wiki pages + every file in each issue folder. Order is
    deterministic: wiki pages first, then issue folders in
    ISSUE_FOLDERS order.
    """
    out: list[Path] = list(sorted(a4_dir.glob("*.md")))
    for folder in ISSUE_FOLDERS:
        out.extend(iter_issue_files(a4_dir, folder))
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


def iter_family(a4_dir: Path, family: str) -> list[tuple[Path, dict]]:
    """Walk a family folder, returning ``(path, fm)`` pairs.

    Skips files whose preamble is absent or malformed. Order matches
    ``iter_issue_files`` (sorted, flat).
    """
    out: list[tuple[Path, dict]] = []
    for p in iter_issue_files(a4_dir, family):
        fm = read_fm(p)
        if fm is None:
            continue
        out.append((p, fm))
    return out


def collect_family(a4_dir: Path, family: str) -> dict[str, dict]:
    """Map ``<family>/<id>-<slug>`` → frontmatter for parseable files."""
    return {f"{family}/{p.stem}": fm for p, fm in iter_family(a4_dir, family)}


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
