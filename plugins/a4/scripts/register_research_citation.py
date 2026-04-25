# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Atomically register a research → decision citation.

A decision file may cite a research artifact at
`<project-root>/research/<slug>.md`. The citation has four representations:

  - decision/<id>-<slug>.md frontmatter `research:` list
  - decision/<id>-<slug>.md body `## Research` section
  - research/<slug>.md frontmatter `cited_by:` list (stored reverse-link)
  - research/<slug>.md body `## Cited By` section

This script writes all four in a single invocation and bumps the research
file's `updated:` field to today. Idempotent: when a side already records
the citation that side is left alone.

Usage:
    uv run register_research_citation.py <a4-dir> <research-ref> <decision-ref>

  <a4-dir>        path to the a4/ workspace (research/ is a sibling of this)
  <research-ref>  research/<slug> (or a path that resolves to research/<slug>.md)
  <decision-ref>  decision/<id>-<slug> (or a path inside a4/decision/)
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
    decision_file: str = ""
    research_file: str = ""
    decision_research_field_added: bool = False
    decision_body_added: bool = False
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


def _resolve_decision(a4_dir: Path, ref: str) -> Path | None:
    """Resolve a decision reference to a filesystem path under a4/decision/."""
    decision_dir = a4_dir / "decision"
    if Path(ref).is_absolute():
        path = Path(ref)
        return path if path.is_file() else None

    if ref.startswith("decision/"):
        rel = ref[len("decision/") :]
        if not rel.endswith(".md"):
            rel += ".md"
        path = decision_dir / rel
        return path if path.is_file() else None

    rel = ref if ref.endswith(".md") else f"{ref}.md"
    path = decision_dir / rel
    return path if path.is_file() else None


def register(
    a4_dir: Path,
    research_path: Path,
    decision_path: Path,
    dry_run: bool,
) -> Result:
    today = date.today().isoformat()
    result = Result(
        a4_dir=str(a4_dir),
        decision_file=str(decision_path),
        research_file=str(research_path),
        dry_run=dry_run,
    )

    research_ref = f"research/{research_path.stem}"
    decision_ref = f"decision/{decision_path.stem}"

    # Decision side.
    decision_md = parse(decision_path)
    decision_existing = _existing_list(decision_md.preamble.fm, "research")
    decision_fm = decision_md.preamble.raw
    decision_body = decision_md.body.content
    if research_ref not in decision_existing:
        decision_fm = _rewrite_list_field(
            decision_fm, "research", sorted(decision_existing + [research_ref])
        )
        result.decision_research_field_added = True
    new_decision_body, body_changed = _append_to_section(
        decision_body, "Research", f"- [[{research_ref}]]"
    )
    if body_changed:
        decision_body = new_decision_body
        result.decision_body_added = True

    # Research side.
    research_md = parse(research_path)
    research_existing = _existing_list(research_md.preamble.fm, "cited_by")
    research_fm = research_md.preamble.raw
    research_body = research_md.body.content
    if decision_ref not in research_existing:
        research_fm = _rewrite_list_field(
            research_fm, "cited_by", sorted(research_existing + [decision_ref])
        )
        result.research_cited_by_added = True
    new_research_body, body_changed = _append_to_section(
        research_body, "Cited By", f"- [[{decision_ref}]]"
    )
    if body_changed:
        research_body = new_research_body
        result.research_body_added = True
    research_fm, updated_bumped = _bump_updated(research_fm, today)
    if updated_bumped:
        result.research_updated_bumped = True

    if not dry_run:
        if result.decision_research_field_added or result.decision_body_added:
            _write_file(decision_path, decision_fm, decision_body)
        if (
            result.research_cited_by_added
            or result.research_body_added
            or result.research_updated_bumped
        ):
            _write_file(research_path, research_fm, research_body)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atomically register a research → decision citation."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "research_ref",
        help="research/<slug> or a path resolving to research/<slug>.md",
    )
    parser.add_argument(
        "decision_ref",
        help="decision/<id>-<slug> or a path inside a4/decision/",
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

    decision_path = _resolve_decision(a4_dir, args.decision_ref)
    if decision_path is None:
        print(
            f"Error: decision file not found for ref {args.decision_ref!r}",
            file=sys.stderr,
        )
        sys.exit(2)

    result = register(
        a4_dir, research_path.resolve(), decision_path.resolve(), args.dry_run
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        prefix = "(dry-run) " if args.dry_run else ""
        try:
            decision_disp = decision_path.relative_to(a4_dir.parent)
        except ValueError:
            decision_disp = decision_path
        try:
            research_disp = research_path.relative_to(a4_dir.parent)
        except ValueError:
            research_disp = research_path
        print(f"{prefix}decision: {decision_disp}")
        print(f"{prefix}research: {research_disp}")
        flags = [
            ("research field on decision", result.decision_research_field_added),
            ("Research section on decision", result.decision_body_added),
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
