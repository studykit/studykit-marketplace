# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate cross-file status consistency across an a4/ workspace.

Some status enum values are semantically derived from cross-file state:

  - decision.status = "superseded" iff another decision/*.md at
    `status: final` declares `supersedes: [<this-path>]`.
  - usecase.status = "superseded" iff another usecase/*.md at
    `status: shipped` declares `supersedes: [<this-path>]`.
  - task.status = "discarded" iff every UC in the task's `implements:`
    is at `status: discarded`.
  - review.status = "discarded" iff the review's `target:` points at a
    usecase with `status: discarded`.
  - idea.status = "promoted" iff the idea's own `promoted:` list is
    non-empty.
  - spark/*.brainstorm.md status = "promoted" iff own `promoted:` is
    non-empty.

These are normally materialized by active writers:
  - `scripts/transition_status.py` cascades UC `shipped → superseded`
    (on successor ship), UC `discarded` → task/review discard,
    UC `revising` → task reset, and decision `final → superseded`
    (on successor finalization). It is the single writer across
    usecase / task / review / decision.

This validator is the safety net — it catches drift left behind if a
writer was skipped, bypassed, or ran before the successor reached its
terminal-active state. Report-only; no file is mutated.

Two modes:

  Workspace mode (default) — scan every decision/usecase/idea/brainstorm
  file and report all mismatches. Used by SessionStart and `/a4:validate`.

  File-scoped mode (`--file <path>`) — report only mismatches involving
  the given file's "related set":
    - idea/<id>-<slug>.md        → that file only (self-contained rule)
    - spark/<...>.brainstorm.md  → that file only (self-contained rule)
    - decision/<id>-<slug>.md    → that file + files it supersedes +
                                   files that supersede it (connected
                                   component via `supersedes:`)
    - usecase/<id>-<slug>.md     → same as decision, walked via
                                   usecase-to-usecase `supersedes:`
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

from common import (
    is_non_empty_list as _is_non_empty_list,
    normalize_ref as _normalize_ref,
    split_frontmatter as _split_frontmatter,
)


@dataclass(frozen=True)
class Mismatch:
    path: str
    rule: str
    message: str


def split_frontmatter(path: Path) -> dict | None:
    return _split_frontmatter(path).fm


# Families for which a `superseded` status is actively materialized by
# transition_status.py when a successor reaches its terminal-active
# state. Both sides must be same-family — a decision does not supersede
# a usecase and vice versa.
SUPERSEDES_FAMILIES: dict[str, str] = {
    "decision": "final",
    "usecase": "shipped",
}


def collect_family(a4_dir: Path, family: str) -> dict[str, dict]:
    """Map `<family>/<id>-<slug>` → frontmatter for every .md in folder."""
    out: dict[str, dict] = {}
    folder = a4_dir / family
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.md")):
        fm = split_frontmatter(p)
        if fm is None:
            continue
        key = f"{family}/{p.stem}"
        out[key] = fm
    return out


def collect_decisions(a4_dir: Path) -> dict[str, dict]:
    """Back-compat alias for `collect_family(a4_dir, "decision")`."""
    return collect_family(a4_dir, "decision")


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


def check_superseded(items: dict[str, dict], family: str) -> list[Mismatch]:
    """Check supersedes-↔-status consistency within a single family.

    A target artifact is expected to be at `status: superseded` iff it is
    named in the `supersedes:` list of another artifact in the same family
    that is itself at its terminal-active status (decision=final,
    usecase=shipped). Draft/implementing successors do NOT yet render
    their targets superseded.
    """
    mismatches: list[Mismatch] = []
    terminal_active = SUPERSEDES_FAMILIES.get(family)
    if terminal_active is None:
        return mismatches

    # Build: for each target key, the list of live-successor keys
    # that claim to supersede it.
    superseded_by: dict[str, list[str]] = {}
    for key, fm in items.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        successor_status = fm.get("status")
        if successor_status != terminal_active:
            continue
        for entry in supersedes:
            norm = _normalize_ref(entry)
            if norm is None:
                continue
            superseded_by.setdefault(norm, []).append(key)

    for key, fm in items.items():
        status = fm.get("status")
        is_targeted = key in superseded_by

        if status == "superseded" and not is_targeted:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"stale-superseded-status-{family}",
                    message=(
                        f"status=superseded but no {terminal_active!r} "
                        f"{family} declares `supersedes: [{key}]`"
                    ),
                )
            )
        elif status != "superseded" and is_targeted:
            superseders = sorted(superseded_by[key])
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"missing-superseded-status-{family}",
                    message=(
                        f"status={status!r} but superseded by {superseders} "
                        f"(each at {terminal_active!r}). Expected "
                        "status=superseded — transition_status.py should "
                        "have flipped this; re-run it against the successor."
                    ),
                )
            )

    for key, fm in items.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for entry in supersedes:
            norm = _normalize_ref(entry)
            if norm is None:
                continue
            if norm not in items:
                mismatches.append(
                    Mismatch(
                        path=f"{key}.md",
                        rule=f"superseded-target-missing-{family}",
                        message=(
                            f"`supersedes: [{norm}]` points at a {family} "
                            "that does not exist in the workspace"
                        ),
                    )
                )

    return mismatches


def check_discarded_cascade(
    a4_dir: Path,
    usecases: dict[str, dict],
) -> list[Mismatch]:
    """Flag drift when a UC is `discarded` but its cascades did not run.

    - task: each task with `implements: [usecase/<discarded>]` where all
      implemented UCs are discarded is expected at `discarded` too.
    - review: each review with `target: usecase/<discarded>` at `open`
      or `in-progress` is expected at `discarded`.
    """
    mismatches: list[Mismatch] = []
    discarded_uc_keys = {
        key for key, fm in usecases.items()
        if fm.get("status") == "discarded"
    }
    if not discarded_uc_keys:
        return mismatches

    task_dir = a4_dir / "task"
    if task_dir.is_dir():
        for p in sorted(task_dir.glob("*.md")):
            fm = split_frontmatter(p)
            if fm is None:
                continue
            implements = fm.get("implements") or []
            if not isinstance(implements, list) or not implements:
                continue
            implemented_keys = {
                _normalize_ref(x) for x in implements
            }
            implemented_keys.discard(None)
            if not implemented_keys or not implemented_keys.issubset(discarded_uc_keys):
                continue
            status = fm.get("status")
            if status == "discarded":
                continue
            mismatches.append(
                Mismatch(
                    path=f"task/{p.stem}.md",
                    rule="missing-discarded-status-task",
                    message=(
                        f"status={status!r} but every UC this task "
                        f"implements is discarded. Expected "
                        "status=discarded — transition_status.py should "
                        "have cascaded from the UC discard."
                    ),
                )
            )

    review_dir = a4_dir / "review"
    if review_dir.is_dir():
        for p in sorted(review_dir.glob("*.md")):
            fm = split_frontmatter(p)
            if fm is None:
                continue
            target = _normalize_ref(fm.get("target"))
            if target is None or target not in discarded_uc_keys:
                continue
            status = fm.get("status")
            if status in {"discarded", "resolved"}:
                continue
            mismatches.append(
                Mismatch(
                    path=f"review/{p.stem}.md",
                    rule="missing-discarded-status-review",
                    message=(
                        f"status={status!r} but target {target!r} is "
                        f"discarded. Expected status=discarded — "
                        "transition_status.py should have cascaded."
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
    ideas = collect_with_promoted(a4_dir, "idea", "*.md")
    brainstorms = collect_with_promoted(a4_dir, "spark", "*.brainstorm.md")

    mismatches: list[Mismatch] = []
    usecases: dict[str, dict] = {}
    for family in SUPERSEDES_FAMILIES:
        items = collect_family(a4_dir, family)
        mismatches.extend(check_superseded(items, family))
        if family == "usecase":
            usecases = items
    if usecases:
        mismatches.extend(check_discarded_cascade(a4_dir, usecases))
    mismatches.extend(check_promoted(ideas, "idea"))
    mismatches.extend(check_promoted(brainstorms, "brainstorm"))
    return mismatches


def _supersedes_component(items: dict[str, dict], key: str) -> set[str]:
    """Walk the supersedes chain within a single family, both directions."""
    component = {key}
    fm = items.get(key)
    if fm is not None:
        for entry in fm.get("supersedes") or []:
            norm = _normalize_ref(entry)
            if norm:
                component.add(norm)
    for other_key, other_fm in items.items():
        for entry in other_fm.get("supersedes") or []:
            if _normalize_ref(entry) == key:
                component.add(other_key)
                break
    return component


# Back-compat alias used by older callers.
def _decision_component(decisions: dict[str, dict], key: str) -> set[str]:
    return _supersedes_component(decisions, key)


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

    if folder in SUPERSEDES_FAMILIES:
        if not basename.endswith(".md"):
            return []
        items = collect_family(a4_dir, folder)
        stem = basename[:-3]
        key = f"{folder}/{stem}"
        component = _supersedes_component(items, key)
        component_paths = {f"{k}.md" for k in component}
        return [
            m
            for m in check_superseded(items, folder)
            if m.path in component_paths
        ]

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
