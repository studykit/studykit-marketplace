# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Single writer for status transitions across the a4/ workspace.

All status changes on usecase, task, review, and spec files flow
through this script. Skills and agents call it with the target file and
the desired new status. The script:

  1. Detects the family from the file path.
  2. Checks the current → new transition is legal per the family's
     transition table.
  3. Writes `status:` and `updated:` in the frontmatter. The body is
     left untouched — the `## Log` body section, when present, is
     hand-maintained by authors and is not written by this script.
  4. Runs cascades — cross-file status changes that are semantically
     implied by the primary transition:

        usecase implementing → revising        → related tasks reset:
                                                  progress/failing → pending
        usecase * → discarded                  → related tasks → discarded
                                                  related open reviews → discarded
        usecase shipped → discarded            → same as above
        usecase → shipped                      → supersedes chain: each same-
                                                  family target currently
                                                  `shipped` flips to `superseded`
        spec → active                          → supersedes chain: each same-
                                                  family target currently
                                                  `active` or `deprecated` flips
                                                  to `superseded`

All cascades happen in the same invocation so the caller only needs to
commit the unstaged working-tree delta once.

Authoring invariants beyond legality (e.g., UC `actors:` non-empty at
`>= ready`, placeholder tokens in `title:`) are enforced statically by
``markdown_validator.frontmatter`` at the Stop hook, not here.

Exit codes:
  0 — clean run, transition applied (or dry-run validated)
  2 — illegal transition or hard error

Usage:
    uv run transition_status.py <a4-dir> --file <path> --to <status>
    uv run transition_status.py <a4-dir> --file <path> --to <status> --reason "text"
    uv run transition_status.py <a4-dir> --file <path> --to <status> --dry-run --json
    uv run transition_status.py <a4-dir> --file <path> --validate --to <status>
    uv run transition_status.py <a4-dir> --sweep              # supersedes recovery
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable

from common import iter_family, normalize_ref
from markdown import parse
from markdown_validator.refs import RefIndex
from status_model import (
    FAMILY_TRANSITIONS,
    REVIEW_TERMINAL,
    STATUS_BY_FOLDER as FAMILY_STATES,
    SUPERSEDABLE_FROM_STATUSES,
    SUPERSEDES_TRIGGER_STATUS,
    TASK_RESET_ON_REVISING,
    TASK_RESET_TARGET,
    cascade_for,
    is_transition_legal,
    legal_targets_from,
)


# ---------------------------------------------------------------------------
# Family model
# ---------------------------------------------------------------------------
#
# Status enums and transition tables are imported from status_model
# (canonical source). FAMILY_STATES is the issue-family subset of
# STATUS_BY_FOLDER — the writer only handles families with mechanical
# transitions (idea/spark are user-driven and absent from
# FAMILY_TRANSITIONS).


def detect_family(rel_path: str) -> str | None:
    parts = rel_path.split("/", 1)
    if len(parts) < 2:
        return None
    folder = parts[0]
    if folder in FAMILY_TRANSITIONS:
        return folder
    return None


# ---------------------------------------------------------------------------
# Frontmatter IO
# ---------------------------------------------------------------------------


def _parse(path: Path) -> tuple[dict | None, str, str]:
    """Preserves the pre-shared-module `_parse(path)` 3-tuple
    contract: (fm | None, raw_fm, body_content).

    `body_content` retains the leading newline from the closing-fence
    line (unlike the old local `split_frontmatter`, which stripped it);
    `write_file` applies `body.lstrip()` before emitting so output stays
    byte-identical. Substring-probing call sites (validation) are
    insensitive to the leading newline.
    """
    parsed = parse(path)
    return parsed.preamble.fm, parsed.preamble.raw, parsed.body.content


def rewrite_frontmatter_scalar(raw_fm: str, field_name: str, new_value: str) -> str:
    """Replace `field: ...` with a new scalar value.

    Preserves indent and any other lines. Appends the field when absent.
    """
    lines = raw_fm.split("\n")
    prefix = f"{field_name}:"
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(prefix):
            indent = line[: len(line) - len(stripped)]
            lines[i] = f"{indent}{field_name}: {new_value}"
            return "\n".join(lines)
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"{field_name}: {new_value}")
    return "\n".join(lines)


def write_file(path: Path, raw_fm: str, body: str) -> None:
    trimmed = raw_fm.rstrip("\n")
    content = f"---\n{trimmed}\n---\n{body.lstrip()}"
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Scanning helpers for cascade discovery
# ---------------------------------------------------------------------------


def find_tasks_implementing(
    a4_dir: Path, uc_canonical: str, index: RefIndex
) -> list[Path]:
    """Tasks whose `implements:` list contains the given UC.

    ``uc_canonical`` is the UC's canonical ref form (``usecase/<stem>``).
    Each ``implements:`` entry is resolved through ``index`` so all
    accepted ref forms — ``#<id>``, ``usecase/<id>``, ``usecase/<id>-<slug>``,
    bare ``<id>-<slug>`` — match the same target. Recurses through
    ``task/{feature,bug,spike}/`` kind subfolders via ``iter_family``.
    """
    return [
        p for p, fm in iter_family(a4_dir, "task")
        if isinstance(fm.get("implements"), list)
        and any(index.canonical(r) == uc_canonical for r in fm["implements"])
    ]


def find_reviews_targeting(
    a4_dir: Path, canonical: str, index: RefIndex
) -> list[Path]:
    """Review items whose `target:` references the given canonical ref.

    Accepts both string-scalar and list-of-strings shapes for ``target:``,
    matching the schema and ``status_consistency.check_discarded_cascade``.
    Resolves each entry through ``index`` so short forms match.
    """
    matching: list[Path] = []
    for p, fm in iter_family(a4_dir, "review"):
        target = fm.get("target")
        if isinstance(target, str):
            if index.canonical(target) == canonical:
                matching.append(p)
        elif isinstance(target, list):
            if any(index.canonical(e) == canonical for e in target):
                matching.append(p)
    return matching


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass
class Change:
    path: str
    from_status: str
    to_status: str
    reason: str = ""


@dataclass
class Report:
    a4_dir: str = ""
    file: str = ""
    family: str = ""
    current_status: str | None = None
    target_status: str | None = None
    primary: Change | None = None
    cascades: list[Change] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False
    ok: bool = False


# ---------------------------------------------------------------------------
# Primary write + cascades
# ---------------------------------------------------------------------------
#
# Post-draft authoring invariants (UC `actors:` non-empty at `>= ready`,
# placeholder tokens in `title:`, etc.) live in
# ``markdown_validator.frontmatter`` and are enforced statically at the
# Stop hook. They are intentionally not duplicated here — the writer's
# job is the legality table + atomic ``status:``/``updated:`` write +
# cascades, not authoring shape.


def _apply_status_change(
    path: Path,
    from_status: str,
    to_status: str,
    log_reason: str,
    dry_run: bool,
    today: str,
) -> None:
    """Rewrite ``status:`` and ``updated:`` in frontmatter; leave body untouched.

    The ``## Log`` body section, when present, is hand-maintained — this
    writer never reads or rewrites it. ``log_reason`` is preserved on
    the in-memory ``Change`` record so the report can surface it; it
    has no on-disk effect.

    ``dry_run`` skips only the final disk write — parsing and rewriting
    still run, so a true preview surfaces any parse / rewrite failure
    that a real run would hit.
    """
    fm, raw_fm, body = _parse(path)
    if fm is None:
        raise RuntimeError(f"{path}: unreadable frontmatter")
    new_fm = rewrite_frontmatter_scalar(raw_fm, "status", to_status)
    new_fm = rewrite_frontmatter_scalar(new_fm, "updated", today)
    if dry_run:
        return
    write_file(path, new_fm, body)


SkipDecision = tuple[str, str | None] | None


def _apply_reverse_cascade(
    a4_dir: Path,
    targets: list[Path],
    target_kind: str,
    skip_when: Callable[[Any], SkipDecision],
    to_status: str,
    reason_text: str,
    today: str,
    dry_run: bool,
    report: Report,
) -> None:
    """Reverse-link cascade engine.

    For each target path, parse the current ``status:`` and consult
    ``skip_when``: a tuple ``(reason, detail|None)`` records a skip and
    moves on; ``None`` triggers a status flip to ``to_status`` with
    ``reason_text`` and a ``Change`` row in the report.

    ``target_kind`` ("task" or "review") prefixes the path label in
    skipped/cascade rows. Unreadable frontmatter is recorded as an error
    on the report rather than raising.
    """
    for path in targets:
        fm, _, _ = _parse(path)
        if fm is None:
            report.errors.append(f"{path}: unreadable frontmatter")
            continue
        current = fm.get("status")
        skip = skip_when(current)
        if skip is not None:
            reason, detail = skip
            entry: dict[str, Any] = {
                "path": f"{target_kind}/{path.stem}.md",
                "reason": reason,
            }
            if detail is not None:
                entry["detail"] = detail
            report.skipped.append(entry)
            continue
        _apply_status_change(
            path, str(current), to_status, reason_text, dry_run, today
        )
        report.cascades.append(
            Change(
                path=f"{target_kind}/{path.stem}.md",
                from_status=str(current),
                to_status=to_status,
                reason=reason_text,
            )
        )


def _apply_supersedes_chain(
    a4_dir: Path,
    family: str,
    rel_path: str,
    today: str,
    dry_run: bool,
    report: Report,
    index: RefIndex,
) -> None:
    """Supersedes-chain cascade engine for usecase / spec.

    Reads ``supersedes:`` on the source file and flips each same-family
    target to ``superseded`` if its current status is in
    ``SUPERSEDABLE_FROM_STATUSES[family]``. Cross-family entries, missing
    files, already-superseded targets, and targets in non-supersedable
    statuses are surfaced as skips or errors. Idempotent — safe to call
    twice.

    Each ``supersedes:`` entry is resolved through ``index`` so all
    accepted ref forms (``#<id>``, ``<family>/<id>``,
    ``<family>/<id>-<slug>``, ``<id>-<slug>``) reach the same file. An
    entry the index cannot resolve splits on ``index.is_id_bearing``:
    id-bearing forms (``#<id>``, ``<family>/<id>``, etc.) become a
    missing-target error directly so the diagnostic is sharp; everything
    else falls back to path-form parsing so cross-family-by-prefix skips
    and missing-file errors stay visible.
    """
    src_path = a4_dir / rel_path
    fm, _, _ = _parse(src_path)
    if fm is None:
        return
    supersedes = fm.get("supersedes")
    if not isinstance(supersedes, list):
        return
    src_ref = rel_path.removesuffix(".md")
    family_prefix = f"{family}/"
    supersedable_from = SUPERSEDABLE_FROM_STATUSES[family]
    for entry in supersedes:
        resolved = index.resolve(entry)
        if resolved is not None:
            if resolved.folder != family:
                report.skipped.append(
                    {
                        "path": f"{resolved.canonical}.md",
                        "reason": "cross-family-supersedes",
                        "detail": f"ignored non-{family} target in {src_ref}",
                    }
                )
                continue
            target_path = resolved.path
            canon = resolved.canonical
        else:
            if index.is_id_bearing(entry):
                report.errors.append(
                    f"supersedes target missing: {entry!r} (no file with "
                    "this id in workspace)"
                )
                continue
            norm = normalize_ref(entry)
            if norm is None:
                continue
            if not norm.startswith(family_prefix):
                report.skipped.append(
                    {
                        "path": f"{norm}.md",
                        "reason": "cross-family-supersedes",
                        "detail": f"ignored non-{family} target in {src_ref}",
                    }
                )
                continue
            report.errors.append(f"supersedes target missing: {norm}.md")
            continue

        tfm, _, _ = _parse(target_path)
        if tfm is None:
            report.errors.append(
                f"{target_path}: unreadable frontmatter (supersedes target)"
            )
            continue
        tstatus = tfm.get("status")
        if tstatus == "superseded":
            report.skipped.append(
                {"path": f"{canon}.md", "reason": "already-superseded"}
            )
            continue
        if tstatus not in supersedable_from:
            expected = sorted(supersedable_from)
            report.skipped.append(
                {
                    "path": f"{canon}.md",
                    "reason": "not-supersedable",
                    "detail": f"status={tstatus!r}, expected one of {expected}",
                }
            )
            continue
        _apply_status_change(
            target_path,
            str(tstatus),
            "superseded",
            f"superseded by {src_ref}",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=f"{canon}.md",
                from_status=str(tstatus),
                to_status="superseded",
                reason=f"superseded by {src_ref}",
            )
        )


def _run_cascade(
    cascade_name: str,
    a4_dir: Path,
    family: str,
    rel_path: str,
    today: str,
    dry_run: bool,
    report: Report,
    index: RefIndex,
) -> None:
    """Dispatch cascade by name. Drives both engines off ``CASCADE_TRIGGERS``."""
    if cascade_name == "uc_revising":
        uc_ref = rel_path.removesuffix(".md")
        _apply_reverse_cascade(
            a4_dir,
            find_tasks_implementing(a4_dir, uc_ref, index),
            target_kind="task",
            skip_when=lambda s: (
                None
                if s in TASK_RESET_ON_REVISING
                else ("task-not-in-reset-state", f"status={s!r}")
            ),
            to_status=TASK_RESET_TARGET,
            reason_text=f"revising cascade: {uc_ref}",
            today=today,
            dry_run=dry_run,
            report=report,
        )
        return
    if cascade_name == "uc_discarded":
        uc_ref = rel_path.removesuffix(".md")
        _apply_reverse_cascade(
            a4_dir,
            find_tasks_implementing(a4_dir, uc_ref, index),
            target_kind="task",
            skip_when=lambda s: (
                ("already-discarded", None) if s == "discarded" else None
            ),
            to_status="discarded",
            reason_text=f"cascade: {uc_ref} discarded",
            today=today,
            dry_run=dry_run,
            report=report,
        )
        _apply_reverse_cascade(
            a4_dir,
            find_reviews_targeting(a4_dir, uc_ref, index),
            target_kind="review",
            skip_when=lambda s: (
                ("review-terminal", f"status={s!r}")
                if s in REVIEW_TERMINAL
                else None
            ),
            to_status="discarded",
            reason_text=f"cascade: target {uc_ref} discarded",
            today=today,
            dry_run=dry_run,
            report=report,
        )
        return
    if cascade_name in ("uc_supersedes_chain", "spec_supersedes_chain"):
        _apply_supersedes_chain(
            a4_dir, family, rel_path, today, dry_run, report, index
        )
        return


def transition(
    a4_dir: Path,
    rel_path: str,
    new_status: str,
    reason: str | None,
    dry_run: bool,
) -> Report:
    today = date.today().isoformat()
    report = Report(
        a4_dir=str(a4_dir),
        file=rel_path,
        target_status=new_status,
        dry_run=dry_run,
    )

    family = detect_family(rel_path)
    if family is None:
        report.errors.append(
            f"cannot detect family from path {rel_path!r}. Expected "
            "usecase/, task/, review/, or spec/ prefix."
        )
        return report
    report.family = family

    if new_status not in FAMILY_STATES[family]:
        report.errors.append(
            f"`{new_status}` is not a valid {family} status "
            f"(expected one of {sorted(FAMILY_STATES[family])})"
        )
        return report

    target_path = a4_dir / rel_path
    if not target_path.is_file():
        report.errors.append(f"file not found: {target_path}")
        return report

    fm, _, _ = _parse(target_path)
    if fm is None:
        report.errors.append(f"{target_path}: unreadable frontmatter")
        return report

    current = fm.get("status")
    if not isinstance(current, str):
        report.errors.append(
            f"{target_path}: current `status:` missing or non-string "
            f"(got {current!r})"
        )
        return report
    report.current_status = current

    if current not in FAMILY_STATES[family]:
        report.errors.append(
            f"current status `{current}` not in {family} enum; cannot "
            "transition safely. Fix the file first."
        )
        return report

    if current == new_status:
        report.skipped.append(
            {"path": rel_path, "reason": "already-at-target", "detail": current}
        )
        report.ok = True
        return report

    if not is_transition_legal(family, current, new_status):
        allowed = legal_targets_from(family, current)
        report.errors.append(
            f"illegal transition for {family}: `{current}` → `{new_status}`. "
            f"Allowed from `{current}`: {sorted(allowed) if allowed else 'none (terminal)'}."
        )
        return report

    try:
        _apply_status_change(
            target_path,
            current,
            new_status,
            reason or "",
            dry_run,
            today,
        )
    except RuntimeError as e:
        report.errors.append(str(e))
        return report

    report.primary = Change(
        path=rel_path,
        from_status=current,
        to_status=new_status,
        reason=reason or "",
    )

    cascade_name = cascade_for(family, current, new_status)
    if cascade_name is not None:
        index = RefIndex(a4_dir)
        _run_cascade(
            cascade_name, a4_dir, family, rel_path, today, dry_run, report, index
        )

    report.ok = not report.errors
    return report


# ---------------------------------------------------------------------------
# Sweep mode — supersedes-chain recovery
# ---------------------------------------------------------------------------


def sweep(a4_dir: Path, dry_run: bool) -> list[Report]:
    """Walk all live-successor files and run the supersedes cascade.

    Covers both families that carry `supersedes:`:

      - usecase @ `shipped` → flip same-family targets `shipped → superseded`.
      - spec @ `active` → flip same-family targets
        `{active|deprecated} → superseded`.

    Used when edits bypassed the script (e.g., manual git checkout) so
    a derived `superseded` flip never landed. Idempotent.
    """
    reports: list[Report] = []
    today = date.today().isoformat()
    index = RefIndex(a4_dir)

    uc_trigger = SUPERSEDES_TRIGGER_STATUS["usecase"]
    spec_trigger = SUPERSEDES_TRIGGER_STATUS["spec"]

    for family, trigger in (
        ("usecase", uc_trigger),
        ("spec", spec_trigger),
    ):
        for p, fm in iter_family(a4_dir, family):
            if fm.get("status") != trigger:
                continue
            supersedes = fm.get("supersedes")
            if not isinstance(supersedes, list) or not supersedes:
                continue
            rel = f"{family}/{p.name}"
            report = Report(
                a4_dir=str(a4_dir),
                file=rel,
                family=family,
                current_status=trigger,
                target_status=trigger,
                dry_run=dry_run,
            )
            _apply_supersedes_chain(
                a4_dir, family, rel, today, dry_run, report, index
            )
            report.ok = not report.errors
            if report.cascades or report.errors:
                reports.append(report)

    return reports


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_rel(a4_dir: Path, raw: str) -> str | None:
    p = Path(raw)
    abs_path = p if p.is_absolute() else (a4_dir / p)
    try:
        rel = abs_path.resolve().relative_to(a4_dir.resolve())
    except ValueError:
        return None
    return str(rel)


def _report_to_dict(report: Report) -> dict:
    return {
        "a4_dir": report.a4_dir,
        "file": report.file,
        "family": report.family,
        "current_status": report.current_status,
        "target_status": report.target_status,
        "primary": asdict(report.primary) if report.primary else None,
        "cascades": [asdict(c) for c in report.cascades],
        "skipped": report.skipped,
        "errors": report.errors,
        "dry_run": report.dry_run,
        "ok": report.ok,
    }


def _print_report_human(report: Report, dry_run: bool) -> None:
    prefix = "(dry-run) " if dry_run else ""
    if report.primary is not None:
        p = report.primary
        tail = f" — {p.reason}" if p.reason else ""
        print(f"{prefix}{p.path}: {p.from_status} → {p.to_status}{tail}")
    for c in report.cascades:
        tail = f" — {c.reason}" if c.reason else ""
        print(f"{prefix}  cascade: {c.path}: {c.from_status} → {c.to_status}{tail}")
    for s in report.skipped:
        print(f"  skipped: {s.get('path', '?')} ({s.get('reason', '?')})")
    for e in report.errors:
        print(f"  error: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Single writer for status transitions across the a4/ workspace. "
            "Validates, writes, and cascades related changes."
        )
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--file", type=str, default=None,
        help="target file (absolute or workspace-relative)",
    )
    parser.add_argument(
        "--to", dest="to_status", type=str, default=None,
        help="desired new status",
    )
    parser.add_argument(
        "--reason", type=str, default=None,
        help=(
            "one-line rationale captured in the report. The body's `## Log` "
            "section is hand-maintained — this script does not write to it."
        ),
    )
    parser.add_argument(
        "--validate", action="store_true",
        help=(
            "validate only; do not write. Requires --file and --to. "
            "Reports whether the proposed transition is legal per the "
            "family transition table."
        ),
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help=(
            "walk all shipped UCs and run the supersedes-chain cascade. "
            "Recovery for edits that bypassed the script."
        ),
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

    # Mode dispatch.
    if args.sweep:
        reports = sweep(a4_dir, dry_run=args.dry_run)
        total_cascades = sum(len(r.cascades) for r in reports)
        total_errors = sum(len(r.errors) for r in reports)
        if args.json:
            out = {
                "a4_dir": str(a4_dir),
                "mode": "sweep",
                "dry_run": args.dry_run,
                "reports": [_report_to_dict(r) for r in reports],
                "total_cascades": total_cascades,
                "total_errors": total_errors,
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            for r in reports:
                _print_report_human(r, args.dry_run)
            if not reports:
                print("OK — no supersedes cascades needed.")
        sys.exit(2 if total_errors else 0)

    if args.file is None or args.to_status is None:
        print(
            "Error: --file and --to are required (or use --sweep).",
            file=sys.stderr,
        )
        sys.exit(2)

    rel = _resolve_rel(a4_dir, args.file)
    if rel is None:
        print(
            f"Error: --file {args.file} is not inside {a4_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.validate:
        # Load current state and compute would-be issues without writing.
        family = detect_family(rel)
        target_path = a4_dir / rel
        if family is None or not target_path.is_file():
            report = Report(
                a4_dir=str(a4_dir), file=rel,
                target_status=args.to_status,
                errors=[f"cannot validate: file {rel!r} missing or unsupported family"],
            )
        else:
            fm, _, _ = _parse(target_path)
            if fm is None:
                report = Report(
                    a4_dir=str(a4_dir), file=rel, family=family,
                    target_status=args.to_status,
                    errors=[f"{target_path}: unreadable frontmatter"],
                )
            else:
                current = fm.get("status")
                errors: list[str] = []
                if args.to_status not in FAMILY_STATES.get(family, set()):
                    errors.append(
                        f"`{args.to_status}` is not a valid {family} status"
                    )
                elif not is_transition_legal(
                    family, str(current), args.to_status
                ):
                    allowed = legal_targets_from(family, str(current))
                    errors.append(
                        f"illegal transition: `{current}` → `{args.to_status}`. "
                        f"Allowed from `{current}`: "
                        f"{sorted(allowed) if allowed else 'none (terminal)'}"
                    )
                report = Report(
                    a4_dir=str(a4_dir), file=rel, family=family,
                    current_status=str(current) if current else None,
                    target_status=args.to_status,
                    errors=errors,
                    ok=not errors,
                )
        if args.json:
            print(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False))
        else:
            _print_report_human(report, dry_run=True)
            if report.ok:
                print("OK — transition is legal and validations pass.")
        sys.exit(0 if report.ok else 2)

    report = transition(
        a4_dir=a4_dir,
        rel_path=rel,
        new_status=args.to_status,
        reason=args.reason,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False))
    else:
        _print_report_human(report, args.dry_run)

    sys.exit(0 if report.ok else 2)


if __name__ == "__main__":
    main()
