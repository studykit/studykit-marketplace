"""Status cascade primitives shared by the validator sweep and hook dispatcher.

Holds the cascade engines that flip related files when a primary
``status:`` change occurs on a usecase / spec / issue-family file:

  - reverse-link cascades: tasks implementing a UC, reviews targeting a
    UC (revising / discarded propagation).
  - supersedes-chain cascade: predecessor flip on usecase / spec when
    the successor becomes the live revision.

Two callers consume this module in-process:

  - ``validate.py --fix`` — supersedes-chain recovery sweep for edits
    that bypassed the hook (manual git checkout, external editors).
  - ``a4_hook.py post-edit`` (PostToolUse hook) — primary write is the
    LLM's direct ``status:`` edit; the hook calls cascade primitives to
    flip related files and refresh ``updated:`` on the primary.

Authoring invariants beyond legality (UC ``actors:`` non-empty at
``>= ready``, placeholder tokens in ``title:``, etc.) are enforced
statically by ``markdown_validator.frontmatter`` at the Stop hook, not
here.

Non-runnable module — no PEP-723 header. Importers must declare
``pyyaml>=6.0`` in their own header so ``uv run`` provisions yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from common import iter_family, normalize_ref
from markdown import parse
from markdown_validator.refs import RefIndex
from status_model import (
    FAMILY_TRANSITIONS,
    ISSUE_FAMILY_TYPES,
    REVIEW_TERMINAL,
    SUPERSEDABLE_FROM_STATUSES,
    SUPERSEDES_TRIGGER_STATUS,
    TASK_RESET_ON_REVISING,
    TASK_RESET_TARGET,
)


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


SkipDecision = tuple[str, str | None] | None


# ---------------------------------------------------------------------------
# Family detection
# ---------------------------------------------------------------------------


def detect_family(rel_path: str) -> str | None:
    """Return the family folder for an a4-workspace-relative path, or None.

    Reads the leading path component (``usecase/`` / ``spec/`` /
    ``task/`` / ...) and returns it only if it appears in
    ``FAMILY_TRANSITIONS``. Used by the cascade hook (to gate cascade
    on legal transitions) and the recovery sweep.
    """
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


def parse_fm(path: Path) -> tuple[dict | None, str, str]:
    """Returns the ``(fm | None, raw_fm, body_content)`` 3-tuple.

    ``body_content`` retains the leading newline from the closing-fence
    line; ``write_file`` applies ``body.lstrip()`` before emitting so
    output stays byte-identical. Substring-probing call sites
    (validation) are insensitive to the leading newline.
    """
    parsed = parse(path)
    return parsed.preamble.fm, parsed.preamble.raw, parsed.body.content


def rewrite_frontmatter_scalar(raw_fm: str, field_name: str, new_value: str) -> str:
    """Replace ``field: ...`` with a new scalar value.

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
# Discovery — reverse-link scans
# ---------------------------------------------------------------------------


def find_tasks_implementing(
    a4_dir: Path, uc_canonical: str, index: RefIndex
) -> list[Path]:
    """Tasks whose ``implements:`` list contains the given UC.

    ``uc_canonical`` is the UC's canonical ref form (``usecase/<stem>``).
    Each ``implements:`` entry is resolved through ``index`` so all
    accepted ref forms — ``#<id>``, ``<family>/<id>``,
    ``<family>/<id>-<slug>``, bare ``<id>-<slug>`` — match the same
    target. Walks the four issue family folders in
    ``ISSUE_FAMILY_TYPES``.
    """
    out: list[Path] = []
    for family in ISSUE_FAMILY_TYPES:
        for p, fm in iter_family(a4_dir, family):
            implements = fm.get("implements")
            if not isinstance(implements, list):
                continue
            if any(index.canonical(r) == uc_canonical for r in implements):
                out.append(p)
    return out


def find_reviews_targeting(
    a4_dir: Path, canonical: str, index: RefIndex
) -> list[Path]:
    """Review items whose ``target:`` references the given canonical ref.

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
# Engines
# ---------------------------------------------------------------------------


def apply_status_change(
    path: Path,
    from_status: str,
    to_status: str,
    log_reason: str,
    dry_run: bool,
    today: str,
) -> None:
    """Rewrite ``status:`` and ``updated:`` in frontmatter; leave body untouched.

    The ``## Log`` body section, when present, is hand-maintained — this
    primitive never reads or rewrites it. ``log_reason`` is preserved on
    the in-memory ``Change`` record so the report can surface it; it has
    no on-disk effect.

    ``dry_run`` skips only the final disk write — parsing and rewriting
    still run, so a true preview surfaces any parse / rewrite failure
    that a real run would hit.
    """
    fm, raw_fm, body = parse_fm(path)
    if fm is None:
        raise RuntimeError(f"{path}: unreadable frontmatter")
    new_fm = rewrite_frontmatter_scalar(raw_fm, "status", to_status)
    new_fm = rewrite_frontmatter_scalar(new_fm, "updated", today)
    if dry_run:
        return
    write_file(path, new_fm, body)


def apply_reverse_cascade(
    a4_dir: Path,
    targets: list[Path],
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

    Path labels in skipped/cascade rows are derived from
    ``path.parent.name`` — in the flat post-v12 layout that is the
    family folder (``task``/``bug``/``spike``/``research``/``review``).
    Unreadable frontmatter — surfaced either by the pre-parse check or
    by ``apply_status_change`` raising ``RuntimeError`` at write time —
    is recorded as an error on the report rather than crashing.
    """
    for path in targets:
        rel_label = f"{path.parent.name}/{path.stem}.md"
        fm, _, _ = parse_fm(path)
        if fm is None:
            report.errors.append(f"{path}: unreadable frontmatter")
            continue
        current = fm.get("status")
        skip = skip_when(current)
        if skip is not None:
            reason, detail = skip
            entry: dict[str, Any] = {
                "path": rel_label,
                "reason": reason,
            }
            if detail is not None:
                entry["detail"] = detail
            report.skipped.append(entry)
            continue
        try:
            apply_status_change(
                path, str(current), to_status, reason_text, dry_run, today
            )
        except RuntimeError as e:
            report.errors.append(f"{rel_label}: {e}")
            continue
        report.cascades.append(
            Change(
                path=rel_label,
                from_status=str(current),
                to_status=to_status,
                reason=reason_text,
            )
        )


def apply_supersedes_chain(
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
    id-bearing forms become a missing-target error directly so the
    diagnostic is sharp; everything else falls back to path-form parsing
    so cross-family-by-prefix skips and missing-file errors stay visible.
    """
    src_path = a4_dir / rel_path
    fm, _, _ = parse_fm(src_path)
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

        tfm, _, _ = parse_fm(target_path)
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
        try:
            apply_status_change(
                target_path,
                str(tstatus),
                "superseded",
                f"superseded by {src_ref}",
                dry_run,
                today,
            )
        except RuntimeError as e:
            report.errors.append(f"{canon}.md: {e}")
            continue
        report.cascades.append(
            Change(
                path=f"{canon}.md",
                from_status=str(tstatus),
                to_status="superseded",
                reason=f"superseded by {src_ref}",
            )
        )


def run_cascade(
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
        apply_reverse_cascade(
            a4_dir,
            find_tasks_implementing(a4_dir, uc_ref, index),
            skip_when=lambda s: (
                None
                if s in TASK_RESET_ON_REVISING
                else ("not-in-reset-state", f"status={s!r}")
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
        apply_reverse_cascade(
            a4_dir,
            find_tasks_implementing(a4_dir, uc_ref, index),
            skip_when=lambda s: (
                ("already-discarded", None) if s == "discarded" else None
            ),
            to_status="discarded",
            reason_text=f"cascade: {uc_ref} discarded",
            today=today,
            dry_run=dry_run,
            report=report,
        )
        apply_reverse_cascade(
            a4_dir,
            find_reviews_targeting(a4_dir, uc_ref, index),
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
        apply_supersedes_chain(
            a4_dir, family, rel_path, today, dry_run, report, index
        )
        return


# ---------------------------------------------------------------------------
# Recovery sweep
# ---------------------------------------------------------------------------


def apply_supersedes_sweep(a4_dir: Path, dry_run: bool) -> list[Report]:
    """Walk all live-successor files and run the supersedes cascade.

    Recovery path for edits that bypassed the PostToolUse cascade hook
    (manual git checkout, external editor, scripts that wrote
    frontmatter directly). Covers both families that carry
    ``supersedes:``:

      - usecase @ ``shipped`` → flip same-family targets
        ``shipped → superseded``.
      - spec @ ``active`` → flip same-family targets
        ``{active|deprecated} → superseded``.

    Idempotent — a second run on the same workspace produces no
    further changes.
    """
    from datetime import date

    reports: list[Report] = []
    today = date.today().isoformat()
    index = RefIndex(a4_dir)

    for family in ("usecase", "spec"):
        trigger = SUPERSEDES_TRIGGER_STATUS[family]
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
            apply_supersedes_chain(
                a4_dir, family, rel, today, dry_run, report, index
            )
            report.ok = not report.errors
            if report.cascades or report.errors:
                reports.append(report)

    return reports
