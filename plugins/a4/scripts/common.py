"""Shared helpers for a4 scripts.

Imported by sibling scripts (validators, refresh_implemented_by, ...) and
transitively by the hook dispatcher `a4_hook.py`. Contains pure,
behavior-identical extractions of helpers that were previously duplicated
across multiple scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

WIKI_KINDS = frozenset(
    {"context", "domain", "architecture", "actors", "nfr", "plan", "bootstrap"}
)


@dataclass(frozen=True)
class ParsedMarkdown:
    """Structured result of parsing an a4/ markdown file.

    Attributes:
        fm: parsed YAML frontmatter dict; None if frontmatter is absent,
            malformed, or not a mapping.
        raw_fm: text between the `---` fences, without the wrapping
            newlines; empty string if frontmatter is absent. Suitable for
            surgical rewriting.
        body: text after the closing `---` fence, preserving any leading
            newline present in the source; full file text if no
            frontmatter. Leading newline is kept so body-local line
            indexing composes with `body_start_line` for file-coordinate
            reports in existing consumers.
        body_start_line: 1-based line number where `body` begins in the
            source file.
    """

    fm: dict | None
    raw_fm: str
    body: str
    body_start_line: int


def split_frontmatter(path: Path) -> ParsedMarkdown:
    """Parse an a4/ markdown file into frontmatter and body.

    Canonical implementation. Uses line-boundary `\\n---` detection so a
    stray `---` sequence inside the body cannot confuse the split. On
    missing or malformed frontmatter, `fm` is None and `raw_fm` / `body`
    are best-effort extracted so callers can still inspect or recover.
    """
    text = path.read_text(encoding="utf-8")

    if text.startswith("---\n"):
        after_open = text[4:]
    elif text.startswith("---\r\n"):
        after_open = text[5:]
    else:
        return ParsedMarkdown(fm=None, raw_fm="", body=text, body_start_line=1)

    # Empty frontmatter — closing fence immediately follows opening.
    if (
        after_open.startswith("---\n")
        or after_open.startswith("---\r\n")
        or after_open == "---"
    ):
        raw_fm = ""
        remaining = after_open[3:]
    else:
        end_marker_idx = after_open.find("\n---")
        if end_marker_idx == -1:
            return ParsedMarkdown(fm=None, raw_fm="", body=text, body_start_line=1)
        raw_fm = after_open[:end_marker_idx]
        remaining = after_open[end_marker_idx + len("\n---"):]

    # `body` retains any leading newline present in the source. Existing
    # consumers (notably validate_body's line-number formula) depend on
    # body[0] being the newline that ends the closing-fence line.
    body = remaining

    # Line map:
    #   line 1                   = opening "---"
    #   line 2..1 + raw_fm_lines = frontmatter content
    #   line 2 + raw_fm_lines    = closing "---"
    #   line 3 + raw_fm_lines    = body's first source line
    raw_fm_lines = raw_fm.count("\n") + 1 if raw_fm else 0
    body_start_line = 3 + raw_fm_lines

    try:
        fm_raw = yaml.safe_load(raw_fm) if raw_fm.strip() else None
    except yaml.YAMLError:
        return ParsedMarkdown(fm=None, raw_fm=raw_fm, body=body, body_start_line=body_start_line)

    fm = fm_raw if isinstance(fm_raw, dict) else None
    return ParsedMarkdown(fm=fm, raw_fm=raw_fm, body=body, body_start_line=body_start_line)


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
