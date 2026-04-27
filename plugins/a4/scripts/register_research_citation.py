# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Atomically register a research → adr citation.

An adr file may cite a research artifact at
`<project-root>/research/<slug>.md`. The citation has four representations:

  - adr/<id>-<slug>.md frontmatter `research:` list
  - adr/<id>-<slug>.md body `## Research` section
  - research/<slug>.md frontmatter `cited_by:` list (stored reverse-link)
  - research/<slug>.md body `## Cited By` section

This script writes all four in a single invocation and bumps the research
file's `updated:` field to today. Idempotent: when a side already records
the citation that side is left alone.

Usage:
    uv run register_research_citation.py <a4-dir> <research-ref> <adr-ref>

  <a4-dir>        path to the a4/ workspace (research/ is a sibling of this)
  <research-ref>  research/<slug> (or a path that resolves to research/<slug>.md)
  <adr-ref>       adr/<id>-<slug> (or a path inside a4/adr/)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from common import normalize_ref
from markdown import parse


@dataclass
class Result:
    a4_dir: str = ""
    adr_file: str = ""
    research_file: str = ""
    adr_research_field_added: bool = False
    adr_body_added: bool = False
    research_cited_by_added: bool = False
    research_body_added: bool = False
    research_updated_bumped: bool = False
    dry_run: bool = False
    errors: list[str] = field(default_factory=list)


def _format_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return f"[{', '.join(values)}]"


def _rewrite_list_field(raw_fm: str, field_name: str, values: list[str]) -> str:
    """Set `field_name:` to a YAML flow-list. Add field if absent."""
    lines = raw_fm.split("\n")
    prefix = f"{field_name}:"
    yaml_value = _format_list(values)
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(prefix):
            indent = line[: len(line) - len(stripped)]
            end = i + 1
            list_indent = indent + "  "
            while end < len(lines):
                nxt = lines[end]
                if nxt.lstrip().startswith("- ") and nxt.startswith(list_indent):
                    end += 1
                    continue
                if nxt.strip() == "" or not nxt.startswith(indent):
                    break
                break
            new_line = f"{indent}{field_name}: {yaml_value}"
            return "\n".join(lines[:i] + [new_line] + lines[end:])
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"{field_name}: {yaml_value}")
    return "\n".join(lines)


def _bump_updated(raw_fm: str, today: str) -> tuple[str, bool]:
    """Set `updated:` to today. Append the field when absent."""
    lines = raw_fm.split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("updated:"):
            current = stripped[len("updated:") :].strip().strip("'\"")
            if current == today:
                return raw_fm, False
            indent = line[: len(line) - len(stripped)]
            lines[i] = f"{indent}updated: {today}"
            return "\n".join(lines), True
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"updated: {today}")
    return "\n".join(lines), True


def _write_file(path: Path, raw_fm: str, body: str) -> None:
    trimmed = raw_fm.rstrip("\n")
    content = f"---\n{trimmed}\n---\n{body.lstrip()}"
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _existing_list(fm: dict | None, field_name: str) -> list[str]:
    if fm is None:
        return []
    raw = fm.get(field_name)
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        n = normalize_ref(x)
        if n:
            out.append(n)
    return out


def _append_to_section(body: str, heading: str, line: str) -> tuple[str, bool]:
    """Append `line` to a `## <heading>` section, creating the section if absent.

    Idempotent: if the line already appears anywhere within the named
    section, no change is made.
    """
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    m = pattern.search(body)
    if m is None:
        prefix = body.rstrip()
        if prefix:
            new_body = f"{prefix}\n\n## {heading}\n\n{line}\n"
        else:
            new_body = f"## {heading}\n\n{line}\n"
        return new_body, True

    section_start = m.end()
    next_section = re.search(r"^##\s+", body[section_start:], re.MULTILINE)
    section_end = section_start + next_section.start() if next_section else len(body)
    section_text = body[section_start:section_end]

    if line in section_text:
        return body, False

    trimmed = section_text.rstrip("\n")
    if trimmed:
        appended = trimmed + "\n" + line + "\n\n"
    else:
        appended = "\n" + line + "\n\n"
    new_body = body[:section_start] + appended + body[section_end:]
    if next_section is None and not new_body.endswith("\n"):
        new_body += "\n"
    return new_body, True


def _resolve_research(a4_dir: Path, ref: str) -> Path | None:
    """Resolve a research reference to a filesystem path under <root>/research/."""
    project_root = a4_dir.parent
    research_dir = project_root / "research"
    candidate = Path(ref)

    if candidate.is_absolute():
        return candidate if candidate.is_file() else None

    if ref.startswith("research/"):
        rel = ref[len("research/") :]
        if not rel.endswith(".md"):
            rel += ".md"
        path = research_dir / rel
        return path if path.is_file() else None

    rel = ref if ref.endswith(".md") else f"{ref}.md"
    path = research_dir / rel
    if path.is_file():
        return path

    fallback = project_root / ref
    return fallback if fallback.is_file() else None


def _resolve_adr(a4_dir: Path, ref: str) -> Path | None:
    """Resolve an adr reference to a filesystem path under a4/adr/."""
    adr_dir = a4_dir / "adr"
    if Path(ref).is_absolute():
        path = Path(ref)
        return path if path.is_file() else None

    if ref.startswith("adr/"):
        rel = ref[len("adr/") :]
        if not rel.endswith(".md"):
            rel += ".md"
        path = adr_dir / rel
        return path if path.is_file() else None

    rel = ref if ref.endswith(".md") else f"{ref}.md"
    path = adr_dir / rel
    return path if path.is_file() else None


def register(
    a4_dir: Path,
    research_path: Path,
    adr_path: Path,
    dry_run: bool,
) -> Result:
    today = date.today().isoformat()
    result = Result(
        a4_dir=str(a4_dir),
        adr_file=str(adr_path),
        research_file=str(research_path),
        dry_run=dry_run,
    )

    research_ref = f"research/{research_path.stem}"
    adr_ref = f"adr/{adr_path.stem}"

    # ADR side.
    adr_md = parse(adr_path)
    adr_existing = _existing_list(adr_md.preamble.fm, "research")
    adr_fm = adr_md.preamble.raw
    adr_body = adr_md.body.content
    if research_ref not in adr_existing:
        adr_fm = _rewrite_list_field(
            adr_fm, "research", sorted(adr_existing + [research_ref])
        )
        result.adr_research_field_added = True
    new_adr_body, body_changed = _append_to_section(
        adr_body, "Research", f"- [[{research_ref}]]"
    )
    if body_changed:
        adr_body = new_adr_body
        result.adr_body_added = True

    # Research side.
    research_md = parse(research_path)
    research_existing = _existing_list(research_md.preamble.fm, "cited_by")
    research_fm = research_md.preamble.raw
    research_body = research_md.body.content
    if adr_ref not in research_existing:
        research_fm = _rewrite_list_field(
            research_fm, "cited_by", sorted(research_existing + [adr_ref])
        )
        result.research_cited_by_added = True
    new_research_body, body_changed = _append_to_section(
        research_body, "Cited By", f"- [[{adr_ref}]]"
    )
    if body_changed:
        research_body = new_research_body
        result.research_body_added = True
    research_fm, updated_bumped = _bump_updated(research_fm, today)
    if updated_bumped:
        result.research_updated_bumped = True

    if not dry_run:
        if result.adr_research_field_added or result.adr_body_added:
            _write_file(adr_path, adr_fm, adr_body)
        if (
            result.research_cited_by_added
            or result.research_body_added
            or result.research_updated_bumped
        ):
            _write_file(research_path, research_fm, research_body)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atomically register a research → adr citation."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "research_ref",
        help="research/<slug> or a path resolving to research/<slug>.md",
    )
    parser.add_argument(
        "adr_ref",
        help="adr/<id>-<slug> or a path inside a4/adr/",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="report planned changes without writing",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="emit structured JSON to stdout",
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    research_path = _resolve_research(a4_dir, args.research_ref)
    if research_path is None:
        print(
            f"Error: research file not found for ref {args.research_ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)

    adr_path = _resolve_adr(a4_dir, args.adr_ref)
    if adr_path is None:
        print(
            f"Error: adr file not found for ref {args.adr_ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)

    result = register(
        a4_dir, research_path.resolve(), adr_path.resolve(), args.dry_run
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        prefix = "(dry-run) " if args.dry_run else ""
        try:
            adr_disp = adr_path.relative_to(a4_dir.parent)
        except ValueError:
            adr_disp = adr_path
        try:
            research_disp = research_path.relative_to(a4_dir.parent)
        except ValueError:
            research_disp = research_path
        print(f"{prefix}adr: {adr_disp}")
        print(f"{prefix}research: {research_disp}")
        flags = [
            ("research field on adr", result.adr_research_field_added),
            ("Research section on adr", result.adr_body_added),
            ("cited_by field on research", result.research_cited_by_added),
            ("Cited By section on research", result.research_body_added),
            ("updated bumped on research", result.research_updated_bumped),
        ]
        if any(flag for _, flag in flags):
            print(f"{prefix}changes:")
            for label, flag in flags:
                if flag:
                    print(f"{prefix}  + {label}")
        else:
            print("OK — citation already recorded; nothing to do.")
        for e in result.errors:
            print(f"error: {e}", file=sys.stderr)

    sys.exit(2 if result.errors else 0)


if __name__ == "__main__":
    main()
