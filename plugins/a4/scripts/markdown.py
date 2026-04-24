"""Markdown parsing helpers for a4 scripts.

Public surface:

    Classes
      Preamble        YAML frontmatter block at the top of a file.
      Body            Text after the preamble; carries `line_start` so
                      body-local indexing composes into source-file
                      line numbers.
      Markdown        Preamble + Body.
      Heading         ATX heading discovered inside a Body.

    Functions
      parse(path)              -> Markdown
      extract_preamble(path)   -> Preamble
      extract_body(path)       -> Body

    Methods
      Body.extract_headings()  -> list[Heading]

Imported by sibling scripts (validators, refresh_implemented_by, ...)
and transitively by the hook dispatcher `a4_hook.py`. "Preamble" is the
a4 term for YAML frontmatter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Preamble:
    """YAML frontmatter block at the top of a markdown file.

    Attributes:
        fm: parsed YAML mapping; None if the preamble is absent,
            malformed, or not a mapping.
        raw: text between the `---` fences, without the wrapping
            newlines; empty string if absent. Suitable for surgical
            rewriting.
    """

    fm: dict | None
    raw: str


@dataclass(frozen=True)
class Body:
    """Everything after the preamble's closing fence.

    Attributes:
        line_start: 1-based line number in the source file where the
            body begins (the first line after the closing `---` fence,
            or line 1 if there is no preamble).
        content: body text. Retains the leading newline from the
            closing-fence line when a preamble is present — existing a4
            line-number arithmetic (`line_start + i` against
            `content.splitlines()`) depends on this. Off-by-one cleanup
            is tracked as a deferred follow-up.
    """

    line_start: int
    content: str

    def extract_headings(self) -> list[Heading]:
        """Extract ATX headings (`# ...` through `###### ...`).

        Skips lines inside fenced code blocks (``` or ~~~). Setext-style
        underline headings (`===` / `---`) are not recognized. Heading
        line numbers are computed as `self.line_start + i` over
        `self.content.splitlines()`, matching the indexing convention
        used by other a4 body scanners.
        """
        headings: list[Heading] = []
        fence: str | None = None
        for i, line in enumerate(self.content.splitlines()):
            stripped = line.lstrip()
            if fence is not None:
                if stripped.startswith(fence):
                    fence = None
                continue
            if stripped.startswith("```"):
                fence = "```"
                continue
            if stripped.startswith("~~~"):
                fence = "~~~"
                continue
            m = _ATX_HEADING_RE.match(line)
            if not m:
                continue
            headings.append(
                Heading(
                    level=len(m.group(1)),
                    text=m.group(2).rstrip(),
                    line=self.line_start + i,
                )
            )
        return headings


@dataclass(frozen=True)
class Markdown:
    preamble: Preamble
    body: Body


@dataclass(frozen=True)
class Heading:
    """ATX-style heading found in a Body.

    Attributes:
        level: 1–6, the count of leading `#` characters.
        text: heading text, trailing closing `#`s stripped.
        line: 1-based line number in the source file, using the same
            indexing convention as `Body.line_start + i`.
    """

    level: int
    text: str
    line: int


_ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")


def _locate_preamble(text: str) -> tuple[str, int, int] | None:
    """Locate the preamble fences in `text` without parsing YAML.

    Returns `(raw, body_offset, body_line_start)` on success, where:
      raw              — text between the fences, no wrapping newlines.
      body_offset      — byte offset of the body's first character in
                         `text`.
      body_line_start  — 1-based line number of the body's first source
                         line.

    Returns None when no valid preamble is present (missing opening
    fence, or opening without a matching closing fence). Callers treat
    None as "no preamble; body is the whole text starting at line 1".

    Uses line-boundary `\\n---` detection so a stray `---` inside the
    body cannot confuse the split. Empty preambles (`---\\n---\\n...`)
    are handled explicitly.
    """
    if text.startswith("---\n"):
        open_len = 4
    elif text.startswith("---\r\n"):
        open_len = 5
    else:
        return None

    after_open = text[open_len:]

    if (
        after_open.startswith("---\n")
        or after_open.startswith("---\r\n")
        or after_open == "---"
    ):
        raw = ""
        body_offset = open_len + 3
    else:
        end_marker_idx = after_open.find("\n---")
        if end_marker_idx == -1:
            return None
        raw = after_open[:end_marker_idx]
        body_offset = open_len + end_marker_idx + len("\n---")

    # Line map:
    #   line 1                   = opening "---"
    #   line 2..1 + raw_lines    = preamble content
    #   line 2 + raw_lines       = closing "---"
    #   line 3 + raw_lines       = body's first source line
    raw_lines = raw.count("\n") + 1 if raw else 0
    body_line_start = 3 + raw_lines
    return raw, body_offset, body_line_start


def _load_yaml(raw: str) -> dict | None:
    """Parse a preamble's raw text into a dict, or None on any issue."""
    if not raw.strip():
        return None
    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def parse(path: Path) -> Markdown:
    """Parse a markdown file into Preamble + Body."""
    text = path.read_text(encoding="utf-8")
    located = _locate_preamble(text)
    if located is None:
        return Markdown(
            preamble=Preamble(fm=None, raw=""),
            body=Body(line_start=1, content=text),
        )
    raw, body_offset, line_start = located
    return Markdown(
        preamble=Preamble(fm=_load_yaml(raw), raw=raw),
        body=Body(line_start=line_start, content=text[body_offset:]),
    )


def extract_preamble(path: Path) -> Preamble:
    """Parse only the preamble of a markdown file."""
    text = path.read_text(encoding="utf-8")
    located = _locate_preamble(text)
    if located is None:
        return Preamble(fm=None, raw="")
    raw, _, _ = located
    return Preamble(fm=_load_yaml(raw), raw=raw)


def extract_body(path: Path) -> Body:
    """Parse only the body of a markdown file."""
    text = path.read_text(encoding="utf-8")
    located = _locate_preamble(text)
    if located is None:
        return Body(line_start=1, content=text)
    _, body_offset, line_start = located
    return Body(line_start=line_start, content=text[body_offset:])


