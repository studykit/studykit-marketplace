# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "xmlschema>=3.4"]
# ///
"""Validate body XML structure across an a4/ workspace.

Each markdown file declares ``type: <root>`` in its YAML frontmatter. The
body is a sequence of top-level ``<tag>...</tag>`` blocks on column 0,
with markdown content (free-form, possibly empty) between the open and
close lines. The body is validated against
``body_schemas/<type>.xsd`` (loaded via ``body_schemas.schema_path``)
using XSD 1.1 through the xmlschema library.

Section boundary convention (mirrors the CommonMark HTML-block shape so
the file still renders sanely in any markdown viewer):

    <tag>          ← line of the form `^<name>$`, column 0, kebab-case
    ... markdown content ...
    </tag>         ← line of the form `^</name>$`, column 0

Anything outside a section is allowed only if blank or whitespace —
stray prose between sections is reported.

Validation pipeline:

    1. Parse frontmatter (re-uses ``markdown.parse``).
    2. Extract ``type:`` and resolve the XSD.
    3. Walk the body with the state machine above. Sections collect raw
       text between the open/close lines (exclusive).
    4. Build a synthetic XML document::

           <{type}>
             <{section}><![CDATA[{content}]]></{section}>
             ...
           </{type}>

       Any ``]]>`` literal in section content is split into two CDATA
       segments to keep the wrapper valid.
    5. ``xmlschema.XMLSchema11.iter_errors`` collects every XSD failure.

Rules emitted:

    - body-type-missing      ``type:`` absent from frontmatter.
    - body-type-unknown      ``type:`` value has no matching XSD.
    - body-stray-content     non-whitespace text outside any section.
    - body-tag-invalid       open tag fails ``^[a-z][a-z0-9-]*$``.
    - body-tag-unclosed      EOF reached inside an open section.
    - body-xsd               XSD validation error (missing required,
                              duplicate of a known tag, unknown content
                              that violates the schema's openContent
                              rule, etc.).

Exit codes: 0 = clean, 1 = invocation/IO error, 2 = at least one
violation.

Usage::

    uv run validate_body.py <a4-dir>
    uv run validate_body.py <a4-dir> <file>
    uv run validate_body.py <a4-dir> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import xmlschema

from body_schemas import schema_path
from common import discover_files
from markdown import parse

OPEN_TAG_RE = re.compile(r"^<([a-z][a-z0-9-]*)>\s*$")
CLOSE_TAG_RE = re.compile(r"^</([a-z][a-z0-9-]*)>\s*$")
INVALID_TAG_RE = re.compile(r"^<(/?)([^>\s]+)>\s*$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str
    line: int | None
    message: str


@dataclass(frozen=True)
class Section:
    name: str
    content: str
    open_line: int
    close_line: int


def _scan_sections(
    body_text: str,
    body_start_line: int,
    rel_str: str,
) -> tuple[list[Section], list[Violation]]:
    """Walk ``body_text`` line by line and extract top-level sections.

    Returns ``(sections, violations)``. Violations cover stray content
    between sections, malformed open tags, and unclosed sections.
    """
    sections: list[Section] = []
    violations: list[Violation] = []

    lines = body_text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        abs_line = body_start_line + i

        if not line.strip():
            i += 1
            continue

        open_match = OPEN_TAG_RE.match(line)
        if open_match:
            tag = open_match.group(1)
            close_marker = f"</{tag}>"
            content_lines: list[str] = []
            j = i + 1
            closed_at: int | None = None
            # Track the active fenced code block (``` or ~~~) so an
            # outline-shaped tag inside a code example does not get
            # mistaken for a section close.
            fence: str | None = None
            while j < n:
                inner = lines[j]
                stripped = inner.lstrip()
                fence_match = FENCE_RE.match(stripped)
                if fence is None:
                    if fence_match:
                        fence = fence_match.group(1)[0] * 3
                else:
                    if fence_match and stripped.startswith(fence):
                        fence = None
                # Match close on column 0, exact name, no attributes —
                # but only when not inside a fenced code block.
                if fence is None and inner.rstrip() == close_marker:
                    closed_at = j
                    break
                content_lines.append(inner)
                j += 1
            if closed_at is None:
                violations.append(
                    Violation(
                        rel_str,
                        "body-tag-unclosed",
                        abs_line,
                        f"<{tag}> opened at line {abs_line} has no matching "
                        f"</{tag}> on column 0",
                    )
                )
                i = n  # stop scanning; rest is inside the unclosed section
                break
            sections.append(
                Section(
                    name=tag,
                    content="\n".join(content_lines),
                    open_line=abs_line,
                    close_line=body_start_line + closed_at,
                )
            )
            i = closed_at + 1
            continue

        # Line is non-blank but is not a recognized open tag at column 0.
        # Distinguish "looks like a tag but isn't valid" from "stray prose".
        invalid_match = INVALID_TAG_RE.match(line)
        if invalid_match:
            slash, name = invalid_match.group(1), invalid_match.group(2)
            if slash:
                # Stray close tag with no matching open.
                violations.append(
                    Violation(
                        rel_str,
                        "body-stray-content",
                        abs_line,
                        f"`</{name}>` outside any open section",
                    )
                )
            else:
                violations.append(
                    Violation(
                        rel_str,
                        "body-tag-invalid",
                        abs_line,
                        f"`<{name}>` is not a valid section tag — "
                        "lowercase kebab-case (`^[a-z][a-z0-9-]*$`), no "
                        "attributes, on column 0",
                    )
                )
        else:
            preview = line.strip()
            if len(preview) > 60:
                preview = preview[:57] + "…"
            violations.append(
                Violation(
                    rel_str,
                    "body-stray-content",
                    abs_line,
                    f"non-whitespace text outside any section: {preview!r}",
                )
            )
        i += 1

    return sections, violations


def _build_xml(type_: str, sections: list[Section]) -> str:
    """Build a synthetic XML document for XSD validation."""
    parts: list[str] = [f"<{type_}>"]
    for s in sections:
        safe = s.content.replace("]]>", "]]]]><![CDATA[>")
        parts.append(f"  <{s.name}><![CDATA[{safe}]]></{s.name}>")
    parts.append(f"</{type_}>")
    return "\n".join(parts) + "\n"


def _xsd_errors(
    rel_str: str,
    type_: str,
    schema_file: Path,
    sections: list[Section],
) -> list[Violation]:
    """Run the XSD against the synthetic XML and translate errors."""
    xml_doc = _build_xml(type_, sections)
    schema = xmlschema.XMLSchema11(str(schema_file))
    out: list[Violation] = []
    # Map a section name → its source open line so XSD errors can point
    # at the right place in the source file when possible.
    name_to_line = {s.name: s.open_line for s in sections}
    for err in schema.iter_errors(xml_doc):
        target_line: int | None = None
        # ``err.path`` looks like `/spec/specification` for content
        # errors. Use the deepest path segment we can map.
        path = getattr(err, "path", "") or ""
        if path:
            tail = path.rstrip("/").split("/")[-1]
            target_line = name_to_line.get(tail)
        out.append(
            Violation(
                rel_str,
                "body-xsd",
                target_line,
                _summarize_xsd_error(err, type_),
            )
        )
    return out


def _summarize_xsd_error(err: xmlschema.XMLSchemaValidationError, type_: str) -> str:
    reason = (err.reason or str(err)).strip()
    # xmlschema reasons can be very long; trim to the first sentence/line.
    short = reason.splitlines()[0]
    if len(short) > 240:
        short = short[:237] + "…"
    path = getattr(err, "path", "") or f"/{type_}"
    return f"XSD: {short} (at {path})"


def validate_file(path: Path, a4_dir: Path) -> list[Violation]:
    parsed = parse(path)
    rel_str = str(path.relative_to(a4_dir))
    fm = parsed.preamble.fm or {}
    type_ = fm.get("type")

    if not isinstance(type_, str) or not type_:
        return [
            Violation(
                rel_str,
                "body-type-missing",
                1,
                "frontmatter is missing required `type:` field",
            )
        ]

    schema_file = schema_path(type_)
    if schema_file is None:
        return [
            Violation(
                rel_str,
                "body-type-unknown",
                1,
                f"`type: {type_}` has no matching XSD under body_schemas/",
            )
        ]

    sections, violations = _scan_sections(
        parsed.body.content, parsed.body.line_start, rel_str
    )
    # Even on parse errors we still hand the partial section list to the
    # XSD so the user sees "missing required X" alongside the structural
    # complaint, instead of getting only one error at a time.
    violations.extend(_xsd_errors(rel_str, type_, schema_file, sections))
    return violations


def run(
    a4_dir: Path, file: Path | None = None
) -> tuple[list[Violation], list[Path]]:
    """Library API. Pure: returns ``(violations, files_scanned)``."""
    files = [file] if file else discover_files(a4_dir)
    violations: list[Violation] = []
    for path in files:
        violations.extend(validate_file(path, a4_dir))
    return violations, files


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate body XML structure (per-type XSD) across an a4/ workspace."
        ),
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "file", type=Path, nargs="?", help="validate a single file only"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    target: Path | None = None
    if args.file:
        resolved = args.file.resolve()
        try:
            resolved.relative_to(a4_dir)
        except ValueError:
            print(f"Error: {resolved} is not inside {a4_dir}", file=sys.stderr)
            sys.exit(1)
        target = resolved

    violations, files = run(a4_dir, target)

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "scanned": [str(p.relative_to(a4_dir)) for p in files],
            "violations": [asdict(v) for v in violations],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(2 if violations else 0)

    if not violations:
        print(f"OK — {len(files)} file(s) scanned, no body violations.")
        sys.exit(0)

    file_count = len({v.path for v in violations})
    print(
        f"{len(violations)} violation(s) across {file_count} file(s):",
        file=sys.stderr,
    )
    for v in violations:
        loc = v.path
        if v.line is not None:
            loc += f":{v.line}"
        print(f"  {loc} ({v.rule}): {v.message}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
