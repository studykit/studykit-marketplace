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
  3. Runs mechanical validation for that specific transition (e.g.,
     `actors:` non-empty and `title:` placeholder check for
     `revising → ready` re-approval).
  4. Writes `status:` and `updated:` in the frontmatter. The body is
     left untouched — the `## Log` body section, when present, is
     hand-maintained by authors and is not written by this script.
  5. Runs cascades — cross-file status changes that are semantically
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

Exit codes:
  0 — clean run, transition applied (or dry-run validated)
  2 — illegal transition, validation failure, or hard error

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
from typing import Any

from common import iter_issue_files, normalize_ref
from markdown import parse
from status_model import (
    FAMILY_TRANSITIONS,
    REVIEW_TERMINAL,
    STATUS_BY_FOLDER as FAMILY_STATES,
    SUPERSEDABLE_FROM_STATUSES,
    SUPERSEDES_TRIGGER_STATUS,
    TASK_RESET_ON_REVISING,
    TASK_RESET_TARGET,
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


def find_tasks_implementing(a4_dir: Path, uc_ref: str) -> list[Path]:
    """Tasks whose `implements:` list contains the given UC reference.

    Recurses through `task/{feature,bug,spike}/` kind subfolders.
    """
    matching: list[Path] = []
    for p in iter_issue_files(a4_dir, "task"):
        fm, _, _ = _parse(p)
        if fm is None:
            continue
        implements = fm.get("implements")
        if not isinstance(implements, list):
            continue
        for ref in implements:
            if normalize_ref(ref) == uc_ref:
                matching.append(p)
                break
    return matching


def find_reviews_targeting(a4_dir: Path, ref: str) -> list[Path]:
    """Review items whose `target:` equals the given reference."""
    matching: list[Path] = []
    for p in iter_issue_files(a4_dir, "review"):
        fm, _, _ = _parse(p)
        if fm is None:
            continue
        target = fm.get("target")
        if isinstance(target, str) and normalize_ref(target) == ref:
            matching.append(p)
    return matching


def find_usecases_superseded_by(a4_dir: Path, ref: str) -> list[Path]:
    """Usecases whose `supersedes:` list contains the given UC reference."""
    matching: list[Path] = []
    for p in iter_issue_files(a4_dir, "usecase"):
        fm, _, _ = _parse(p)
        if fm is None:
            continue
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for entry in supersedes:
            if normalize_ref(entry) == ref:
                matching.append(p)
                break
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
    validation_issues: list[str] = field(default_factory=list)
    dry_run: bool = False
    ok: bool = False


# ---------------------------------------------------------------------------
# Mechanical validation
# ---------------------------------------------------------------------------


PLACEHOLDER_TOKENS = ("TBD", "???", "<placeholder>", "<todo>", "TODO:")


def _placeholder_in(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    upper = value.upper()
    for token in PLACEHOLDER_TOKENS:
        if token.upper() in upper:
            return token
    return None


def _is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(x, str) and x.strip() for x in value
    )


def validate_transition(
    a4_dir: Path,
    rel_path: str,
    family: str,
    fm: dict,
    from_status: str,
    to_status: str,
) -> list[str]:
    """Return mechanical validation issues for this transition.

    Empty list means the transition may proceed. `--force` in the caller
    bypasses these checks.
    """
    issues: list[str] = []
    if family == "usecase":
        if from_status == "revising" and to_status == "ready":
            _validate_revising_to_ready(a4_dir, rel_path, fm, issues)
            return issues
        return issues
    if family == "spec":
        if from_status == "draft" and to_status == "active":
            _validate_draft_to_active(a4_dir, rel_path, fm, issues)
            return issues
        return issues
    return issues


def _validate_revising_to_ready(
    a4_dir: Path, rel_path: str, fm: dict, issues: list[str]
) -> None:
    # Re-approval shape checks after a `revising` spec edit.
    actors = fm.get("actors")
    if not _is_non_empty_list(actors):
        issues.append("`actors:` is empty — UC has no actors declared.")
    for field_name in ("title",):
        placeholder = _placeholder_in(fm.get(field_name))
        if placeholder:
            issues.append(
                f"`{field_name}:` contains placeholder `{placeholder}`."
            )


def _validate_draft_to_active(
    a4_dir: Path, rel_path: str, fm: dict, issues: list[str]
) -> None:
    """Spec draft → active: title placeholder check."""
    for field_name in ("title",):
        placeholder = _placeholder_in(fm.get(field_name))
        if placeholder:
            issues.append(
                f"`{field_name}:` contains placeholder `{placeholder}`."
            )


# ---------------------------------------------------------------------------
# Primary write + cascades
# ---------------------------------------------------------------------------


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
    """
    if dry_run:
        return
    fm, raw_fm, body = _parse(path)
    if fm is None:
        raise RuntimeError(f"{path}: unreadable frontmatter")
    new_fm = rewrite_frontmatter_scalar(raw_fm, "status", to_status)
    new_fm = rewrite_frontmatter_scalar(new_fm, "updated", today)
    write_file(path, new_fm, body)


def _cascade_uc_revising(
    a4_dir: Path,
    uc_rel: str,
    today: str,
    dry_run: bool,
    report: Report,
) -> None:
    """UC implementing → revising: reset related tasks to pending."""
    uc_ref = uc_rel.removesuffix(".md")
    for task_path in find_tasks_implementing(a4_dir, uc_ref):
        fm, _, _ = _parse(task_path)
        if fm is None:
            report.errors.append(f"{task_path}: unreadable frontmatter")
            continue
        current = fm.get("status")
        if current not in TASK_RESET_ON_REVISING:
            report.skipped.append(
                {
                    "path": f"task/{task_path.stem}",
                    "reason": "task-not-in-reset-state",
                    "detail": f"status={current!r}",
                }
            )
            continue
        rel_str = f"task/{task_path.stem}.md"
        _apply_status_change(
            task_path,
            str(current),
            TASK_RESET_TARGET,
            f"revising cascade: {uc_ref}",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=rel_str,
                from_status=str(current),
                to_status=TASK_RESET_TARGET,
                reason=f"revising cascade: {uc_ref}",
            )
        )


def _cascade_uc_discarded(
    a4_dir: Path,
    uc_rel: str,
    today: str,
    dry_run: bool,
    report: Report,
) -> None:
    """UC → discarded: discard related tasks and open review items."""
    uc_ref = uc_rel.removesuffix(".md")
    for task_path in find_tasks_implementing(a4_dir, uc_ref):
        fm, _, _ = _parse(task_path)
        if fm is None:
            report.errors.append(f"{task_path}: unreadable frontmatter")
            continue
        current = fm.get("status")
        if current == "discarded":
            report.skipped.append(
                {
                    "path": f"task/{task_path.stem}",
                    "reason": "already-discarded",
                }
            )
            continue
        rel_str = f"task/{task_path.stem}.md"
        _apply_status_change(
            task_path,
            str(current),
            "discarded",
            f"cascade: {uc_ref} discarded",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=rel_str,
                from_status=str(current),
                to_status="discarded",
                reason=f"cascade: {uc_ref} discarded",
            )
        )
    for review_path in find_reviews_targeting(a4_dir, uc_ref):
        fm, _, _ = _parse(review_path)
        if fm is None:
            report.errors.append(f"{review_path}: unreadable frontmatter")
            continue
        current = fm.get("status")
        if current in REVIEW_TERMINAL:
            report.skipped.append(
                {
                    "path": f"review/{review_path.stem}",
                    "reason": "review-terminal",
                    "detail": f"status={current!r}",
                }
            )
            continue
        rel_str = f"review/{review_path.stem}.md"
        _apply_status_change(
            review_path,
            str(current),
            "discarded",
            f"cascade: target {uc_ref} discarded",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=rel_str,
                from_status=str(current),
                to_status="discarded",
                reason=f"cascade: target {uc_ref} discarded",
            )
        )


def _cascade_uc_shipped(
    a4_dir: Path,
    uc_rel: str,
    today: str,
    dry_run: bool,
    report: Report,
    from_status: str,
) -> None:
    """UC → shipped: flip supersedes targets (shipped → superseded)."""
    if from_status != "implementing":
        return
    uc_path = a4_dir / uc_rel
    fm, _, _ = _parse(uc_path)
    if fm is None:
        return
    supersedes = fm.get("supersedes")
    if not isinstance(supersedes, list):
        return
    uc_ref = uc_rel.removesuffix(".md")
    for entry in supersedes:
        norm = normalize_ref(entry)
        if norm is None:
            continue
        # Same-family only.
        if not norm.startswith("usecase/"):
            report.skipped.append(
                {
                    "path": norm,
                    "reason": "cross-family-supersedes",
                    "detail": f"ignored non-usecase target in {uc_ref}",
                }
            )
            continue
        target_path = a4_dir / f"{norm}.md"
        if not target_path.is_file():
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
                {"path": f"{norm}.md", "reason": "already-superseded"}
            )
            continue
        if tstatus not in SUPERSEDABLE_FROM_STATUSES["usecase"]:
            expected = sorted(SUPERSEDABLE_FROM_STATUSES["usecase"])
            report.skipped.append(
                {
                    "path": f"{norm}.md",
                    "reason": "not-terminal-active",
                    "detail": f"status={tstatus!r}, expected one of {expected}",
                }
            )
            continue
        _apply_status_change(
            target_path,
            str(tstatus),
            "superseded",
            f"superseded by {uc_ref}",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=f"{norm}.md",
                from_status=str(tstatus),
                to_status="superseded",
                reason=f"superseded by {uc_ref}",
            )
        )


def _cascade_spec_active(
    a4_dir: Path,
    spec_rel: str,
    today: str,
    dry_run: bool,
    report: Report,
    from_status: str,
) -> None:
    """Spec → active: flip supersedes targets ({active|deprecated} → superseded)."""
    if from_status != "draft":
        return
    spec_path = a4_dir / spec_rel
    fm, _, _ = _parse(spec_path)
    if fm is None:
        return
    supersedes = fm.get("supersedes")
    if not isinstance(supersedes, list):
        return
    spec_ref = spec_rel.removesuffix(".md")
    for entry in supersedes:
        norm = normalize_ref(entry)
        if norm is None:
            continue
        if not norm.startswith("spec/"):
            report.skipped.append(
                {
                    "path": norm,
                    "reason": "cross-family-supersedes",
                    "detail": f"ignored non-spec target in {spec_ref}",
                }
            )
            continue
        target_path = a4_dir / f"{norm}.md"
        if not target_path.is_file():
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
                {"path": f"{norm}.md", "reason": "already-superseded"}
            )
            continue
        if tstatus not in SUPERSEDABLE_FROM_STATUSES["spec"]:
            expected = sorted(SUPERSEDABLE_FROM_STATUSES["spec"])
            report.skipped.append(
                {
                    "path": f"{norm}.md",
                    "reason": "not-supersedable",
                    "detail": f"status={tstatus!r}, expected one of {expected}",
                }
            )
            continue
        _apply_status_change(
            target_path,
            str(tstatus),
            "superseded",
            f"superseded by {spec_ref}",
            dry_run,
            today,
        )
        report.cascades.append(
            Change(
                path=f"{norm}.md",
                from_status=str(tstatus),
                to_status="superseded",
                reason=f"superseded by {spec_ref}",
            )
        )


def transition(
    a4_dir: Path,
    rel_path: str,
    new_status: str,
    reason: str | None,
    force: bool,
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

    issues = validate_transition(
        a4_dir, rel_path, family, fm, current, new_status
    )
    report.validation_issues = list(issues)
    if issues and not force:
        report.errors.append(
            "mechanical validation failed; pass --force to override."
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

    if family == "usecase":
        if current == "implementing" and new_status == "revising":
            _cascade_uc_revising(a4_dir, rel_path, today, dry_run, report)
        elif new_status == "discarded":
            _cascade_uc_discarded(a4_dir, rel_path, today, dry_run, report)
        elif new_status == "shipped":
            _cascade_uc_shipped(
                a4_dir, rel_path, today, dry_run, report, current
            )
    elif family == "spec":
        if new_status == "active":
            _cascade_spec_active(
                a4_dir, rel_path, today, dry_run, report, current
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

    uc_trigger = SUPERSEDES_TRIGGER_STATUS["usecase"]
    spec_trigger = SUPERSEDES_TRIGGER_STATUS["spec"]

    for p in iter_issue_files(a4_dir, "usecase"):
        fm, _, _ = _parse(p)
        if fm is None:
            continue
        if fm.get("status") != uc_trigger:
            continue
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list) or not supersedes:
            continue
        rel = f"usecase/{p.name}"
        report = Report(
            a4_dir=str(a4_dir),
            file=rel,
            family="usecase",
            current_status=uc_trigger,
            target_status=uc_trigger,
            dry_run=dry_run,
        )
        _cascade_uc_shipped(
            a4_dir, rel, today, dry_run, report, from_status="implementing"
        )
        report.ok = not report.errors
        if report.cascades or report.errors:
            reports.append(report)

    for p in iter_issue_files(a4_dir, "spec"):
        fm, _, _ = _parse(p)
        if fm is None:
            continue
        if fm.get("status") != spec_trigger:
            continue
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list) or not supersedes:
            continue
        rel = f"spec/{p.name}"
        report = Report(
            a4_dir=str(a4_dir),
            file=rel,
            family="spec",
            current_status=spec_trigger,
            target_status=spec_trigger,
            dry_run=dry_run,
        )
        _cascade_spec_active(
            a4_dir, rel, today, dry_run, report, from_status="draft"
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
        "validation_issues": report.validation_issues,
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
    for i in report.validation_issues:
        print(f"  validation: {i}", file=sys.stderr)
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
            "Outputs the mechanical-validation verdict for the proposed "
            "transition."
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
        "--force", action="store_true",
        help="bypass mechanical validation (e.g., emergency flip)",
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
                issues: list[str] = []
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
                else:
                    issues = validate_transition(
                        a4_dir, rel, family, fm,
                        str(current), args.to_status,
                    )
                report = Report(
                    a4_dir=str(a4_dir), file=rel, family=family,
                    current_status=str(current) if current else None,
                    target_status=args.to_status,
                    validation_issues=issues,
                    errors=errors,
                    ok=not errors and not issues,
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
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False))
    else:
        _print_report_human(report, args.dry_run)

    sys.exit(0 if report.ok else 2)


if __name__ == "__main__":
    main()
