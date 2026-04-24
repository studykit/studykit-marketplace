# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate cross-file status consistency across an a4/ workspace.

Some status enum values are semantically derived from cross-file state:

  - decision.status = "superseded" iff another decision/*.md declares
    `supersedes: [<this-path>]`.
  - idea.status = "promoted" iff the idea's own `promoted:` list is
    non-empty.
  - spark/*.brainstorm.md status = "promoted" iff own `promoted:` is
    non-empty.

This validator flags either direction of mismatch. The other validators
(validate_frontmatter.py, validate_body.py, drift_detector.py) do not
look across files for these semantic rules — this script closes the gap.

Two modes:

  Workspace mode (default) — scan every decision/idea/brainstorm file
  and report all mismatches. Used by SessionStart and `/a4:validate`.

  File-scoped mode (`--file <path>`) — report only mismatches involving
  the given file's "related set":
    - idea/<id>-<slug>.md        → that file only (self-contained rule)
    - spark/<...>.brainstorm.md  → that file only (self-contained rule)
    - decision/<id>-<slug>.md    → that file + files it supersedes +
                                   files that supersede it (connected
                                   component via `supersedes:`)
    - anything else              → no output (no consistency rule applies)
  Used by the PostToolUse hook so edits do not re-surface unrelated
  legacy mismatches elsewhere in the workspace.

Exit 2 on any reported mismatch, 0 on clean run.

Usage:
    uv run validate_status_consistency.py <a4-dir>
    uv run validate_status_consistency.py <a4-dir> --json
    uv run validate_status_consistency.py <a4-dir> --file <path>
    uv run validate_status_consistency.py <a4-dir> --file <path> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Mismatch:
    path: str
    rule: str
    message: str


def split_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def _normalize_ref(ref: Any) -> str | None:
    """Normalize a frontmatter path reference for comparison.

    Strips a trailing `.md` if present so file-on-disk paths can be
    compared against frontmatter-declared references.
    """
    if not isinstance(ref, str):
        return None
    cleaned = ref.strip()
    if not cleaned:
        return None
    if cleaned.endswith(".md"):
        cleaned = cleaned[:-3]
    return cleaned


def _is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(x, str) and x.strip() for x in value
    )


def collect_decisions(a4_dir: Path) -> dict[str, dict]:
    """Map `decision/<id>-<slug>` → frontmatter."""
    out: dict[str, dict] = {}
    folder = a4_dir / "decision"
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.md")):
        fm = split_frontmatter(p)
        if fm is None:
            continue
        key = f"decision/{p.stem}"
        out[key] = fm
    return out


def collect_with_promoted(
    a4_dir: Path, subfolder: str, file_glob: str
) -> list[tuple[str, dict]]:
    """Return (rel_ref, frontmatter) for items in a folder.

    `rel_ref` is the reference form (folder/<basename-without-.md>).
    """
    out: list[tuple[str, dict]] = []
    folder = a4_dir / subfolder
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob(file_glob)):
        fm = split_frontmatter(p)
        if fm is None:
            continue
        out.append((f"{subfolder}/{p.stem}", fm))
    return out


def check_superseded(decisions: dict[str, dict]) -> list[Mismatch]:
    mismatches: list[Mismatch] = []

    superseded_by: dict[str, list[str]] = {}
    for key, fm in decisions.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for entry in supersedes:
            norm = _normalize_ref(entry)
            if norm is None:
                continue
            superseded_by.setdefault(norm, []).append(key)

    for key, fm in decisions.items():
        status = fm.get("status")
        is_targeted = key in superseded_by

        if status == "superseded" and not is_targeted:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule="stale-superseded-status",
                    message=(
                        "status=superseded but no other decision declares "
                        f"`supersedes: [{key}]`"
                    ),
                )
            )
        elif status != "superseded" and is_targeted:
            superseders = sorted(superseded_by[key])
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule="missing-superseded-status",
                    message=(
                        f"status={status!r} but superseded by: "
                        f"{superseders}. Expected status=superseded."
                    ),
                )
            )

    for key, fm in decisions.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for entry in supersedes:
            norm = _normalize_ref(entry)
            if norm is None:
                continue
            if norm not in decisions:
                mismatches.append(
                    Mismatch(
                        path=f"{key}.md",
                        rule="superseded-target-missing",
                        message=(
                            f"`supersedes: [{norm}]` points at a decision "
                            "that does not exist in the workspace"
                        ),
                    )
                )

    return mismatches


def check_promoted(items: list[tuple[str, dict]], kind: str) -> list[Mismatch]:
    mismatches: list[Mismatch] = []
    for key, fm in items:
        status = fm.get("status")
        has_entries = _is_non_empty_list(fm.get("promoted"))

        if status == "promoted" and not has_entries:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"empty-promoted-list-{kind}",
                    message=(
                        "status=promoted but `promoted:` list is empty. "
                        "Populate with the target artifact path(s) or revert "
                        "the status."
                    ),
                )
            )
        elif status != "promoted" and has_entries:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"missing-promoted-status-{kind}",
                    message=(
                        f"status={status!r} but `promoted:` is populated. "
                        "Expected status=promoted."
                    ),
                )
            )
    return mismatches


def collect_workspace_mismatches(a4_dir: Path) -> list[Mismatch]:
    decisions = collect_decisions(a4_dir)
    ideas = collect_with_promoted(a4_dir, "idea", "*.md")
    brainstorms = collect_with_promoted(a4_dir, "spark", "*.brainstorm.md")

    mismatches: list[Mismatch] = []
    mismatches.extend(check_superseded(decisions))
    mismatches.extend(check_promoted(ideas, "idea"))
    mismatches.extend(check_promoted(brainstorms, "brainstorm"))
    return mismatches


def _decision_component(decisions: dict[str, dict], key: str) -> set[str]:
    component = {key}
    fm = decisions.get(key)
    if fm is not None:
        for entry in fm.get("supersedes") or []:
            norm = _normalize_ref(entry)
            if norm:
                component.add(norm)
    for other_key, other_fm in decisions.items():
        for entry in other_fm.get("supersedes") or []:
            if _normalize_ref(entry) == key:
                component.add(other_key)
                break
    return component


def collect_file_mismatches(a4_dir: Path, rel_file: str) -> list[Mismatch]:
    """Return mismatches in the connected component of `rel_file`.

    `rel_file` is workspace-relative: `decision/1-x.md`, `idea/3-y.md`,
    `spark/2026-04-24-1200-z.brainstorm.md`. Anything else returns [].
    """
    parts = rel_file.split("/", 1)
    if len(parts) < 2:
        return []
    folder, basename = parts[0], parts[1]

    if folder == "idea":
        if not basename.endswith(".md"):
            return []
        abs_path = a4_dir / rel_file
        if not abs_path.is_file():
            return []
        fm = split_frontmatter(abs_path)
        if fm is None:
            return []
        return check_promoted([(f"idea/{abs_path.stem}", fm)], "idea")

    if folder == "spark":
        if not basename.endswith(".brainstorm.md"):
            return []
        abs_path = a4_dir / rel_file
        if not abs_path.is_file():
            return []
        fm = split_frontmatter(abs_path)
        if fm is None:
            return []
        return check_promoted([(f"spark/{abs_path.stem}", fm)], "brainstorm")

    if folder == "decision":
        if not basename.endswith(".md"):
            return []
        decisions = collect_decisions(a4_dir)
        stem = basename[:-3]
        key = f"decision/{stem}"
        component = _decision_component(decisions, key)
        component_paths = {f"{k}.md" for k in component}
        return [m for m in check_superseded(decisions) if m.path in component_paths]

    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate cross-file status consistency in an a4/ workspace."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--file",
        dest="file",
        type=str,
        default=None,
        help=(
            "restrict to the connected component of this file "
            "(absolute or workspace-relative path)"
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.file:
        raw = Path(args.file)
        abs_path = raw if raw.is_absolute() else (a4_dir / raw)
        try:
            rel = abs_path.resolve().relative_to(a4_dir)
        except ValueError:
            print(
                f"Error: --file {args.file} is not inside {a4_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        mismatches = collect_file_mismatches(a4_dir, str(rel))
    else:
        mismatches = collect_workspace_mismatches(a4_dir)

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "mismatches": [asdict(m) for m in mismatches],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(2 if mismatches else 0)

    if not mismatches:
        print("OK — no status-consistency mismatches.")
        sys.exit(0)

    print(
        f"{len(mismatches)} status-consistency mismatch(es):",
        file=sys.stderr,
    )
    for m in mismatches:
        print(f"  {m.path} ({m.rule}): {m.message}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
