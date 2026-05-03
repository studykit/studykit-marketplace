"""PostToolUse subcommand: record + cascade + stamp/refresh + consistency.

Driver order in :func:`post_edit`:

1. Record the edited a4/*.md path (session-scoped, fail-open).
2. Stamp ``created:`` if PreToolUse marked the path as new.
3. Run the status-change cascade if pre→post is a legal transition.
4. Auto-refresh ``updated:`` on the primary if step 3 didn't.
5. Report cross-file status-consistency mismatches on the post-cascade state.

Cascade results surface as additionalContext + systemMessage. Also
auto-refreshes ``updated:`` on every a4/*.md edit (whether or not
``status:`` changed) so authors and the LLM never hand-bump it; on
new-file Writes the same value is stamped to both ``created:`` and
``updated:``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    display_rel,
    drop_newfile,
    emit,
    read_newfiles,
    read_prestatus,
    read_status_from_disk,
    record_edited,
    resolve_type_from_path,
    write_prestatus,
)


def post_edit() -> int:
    """PostToolUse entry point. Always exits 0.

    Order matters: cascade runs *before* the consistency report so the
    report describes the post-cascade workspace (otherwise cascaded
    files would briefly look inconsistent and produce noise).
    """
    import json
    import os

    raw = sys.stdin.read()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    session_id = payload.get("session_id") or ""
    if not file_path or not session_id or not file_path.endswith(".md"):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    a4_prefix = str(a4_dir) + os.sep
    if not file_path.startswith(a4_prefix):
        return 0

    # Step 1 — record (session-scoped, fail-open).
    record_edited(project_dir, session_id, file_path)

    if not a4_dir.is_dir():
        return 0

    # Single timestamp shared across stamp + cascade + auto-bump so a
    # new-file Write ends up with ``created == updated``, and so two
    # writes within the same minute can't drift across step boundaries.
    try:
        from common import now_kst
    except ImportError:
        return 0
    today = now_kst()

    # Step 2 — stamp `created:` if this Write created a new file. Runs
    # before the cascade so a status flip (which also touches `updated:`)
    # sees a frontmatter that already carries `created:`, and `created:`
    # ends up immediately above `updated:` (their canonical order).
    _maybe_stamp_created(a4_dir, file_path, project_dir, session_id, today)

    # Step 3 — status-change cascade (runs before consistency report).
    # Returns True iff it refreshed `updated:` on the primary itself
    # (legal transition triggered apply_status_change). Used to dedupe
    # the auto-bump in Step 4 — no point writing `updated:` twice.
    cascade_refreshed = _run_status_change_cascade(
        a4_dir, file_path, project_dir, session_id, today
    )

    # Step 4 — auto-refresh `updated:` on every a4/*.md edit.
    # The cascade already refreshes `updated:` on the primary on a legal
    # status flip; for everything else (body edit, wiki edit, frontmatter
    # field change without status flip) the LLM and authors hand-bumping
    # was the old contract — that responsibility now lives here so the
    # LLM never has to touch `updated:`.
    if not cascade_refreshed:
        _refresh_updated_on_primary(a4_dir, file_path, today)

    # Step 5 — status-consistency report on the (now post-cascade) state.
    _report_status_consistency_post(a4_dir, file_path, project_dir)
    return 0


def _maybe_stamp_created(
    a4_dir: Path, file_path: str, project_dir: str, session_id: str, today: str
) -> None:
    """Stamp `created:` on a freshly Written a4/*.md whose schema requires it.

    Triggers iff:
      - PreToolUse recorded the path as new (file did not exist on disk).
      - The file now exists.
      - Its `type:` (resolved by path) is in the schema-derived
        ``types_with_created()`` set.

    `created:` is hook-owned: any pre-populated value the LLM or author
    wrote is **overwritten** with the current KST timestamp. Backdating
    is not supported (record originating work date in body ``## Log``
    instead). Once stamped, immutable — never rewritten by hook or
    cascade on subsequent Edits (this function only fires when
    PreToolUse recorded the path as a new file).

    Inserts ``created: <today>`` immediately before ``updated:`` if
    that line exists, else appends at the frontmatter end. If a
    ``created:`` line is already present, it is rewritten in place.
    ``today`` is the same KST timestamp the post-edit driver uses for
    the auto-bump in Step 4, so a fresh Write ends up with
    ``created == updated``. Failure on any step is silent — stamping is
    a convenience, not a gate.
    """
    new_files = read_newfiles(project_dir, session_id)
    if file_path not in new_files:
        return

    abs_path = Path(file_path)
    if not abs_path.is_file():
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        type_value = resolve_type_from_path(abs_path, a4_dir)
    except Exception:
        drop_newfile(project_dir, session_id, file_path)
        return
    if not type_value:
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        from markdown_validator.frontmatter import types_with_created
    except ImportError:
        drop_newfile(project_dir, session_id, file_path)
        return
    if type_value not in types_with_created():
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        from markdown import extract_preamble
        from status_cascade import parse_fm, write_file
    except ImportError:
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        preamble = extract_preamble(abs_path)
    except (OSError, ValueError):
        drop_newfile(project_dir, session_id, file_path)
        return
    if preamble.fm is None:
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        _, raw_fm, body = parse_fm(abs_path)
    except (OSError, ValueError):
        drop_newfile(project_dir, session_id, file_path)
        return

    try:
        new_fm = _insert_created_before_updated(raw_fm, today)
        write_file(abs_path, new_fm, body)
    except (OSError, ValueError):
        pass
    finally:
        drop_newfile(project_dir, session_id, file_path)


def _insert_created_before_updated(raw_fm: str, value: str) -> str:
    """Insert or rewrite ``created: <value>`` in a YAML frontmatter block.

    Position rule: immediately before the ``updated:`` line if present,
    else appended at the end. Indentation matches the ``updated:`` line
    when inserting before it (frontmatter is canonically left-aligned,
    but the matching keeps the rule minimal). When ``created:`` already
    exists in the block, this function rewrites the existing line in
    place via ``rewrite_frontmatter_scalar`` — `created:` is hook-owned,
    so any pre-populated value the LLM wrote is overwritten.
    """
    from status_cascade import rewrite_frontmatter_scalar

    lines = raw_fm.split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("created:"):
            # Should not happen given the caller's gate, but rewrite in
            # place for safety.
            return rewrite_frontmatter_scalar(raw_fm, "created", value)

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("updated:"):
            indent = line[: len(line) - len(stripped)]
            lines.insert(i, f"{indent}created: {value}")
            return "\n".join(lines)

    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append(f"created: {value}")
    return "\n".join(lines)


def _refresh_updated_on_primary(
    a4_dir: Path, file_path: str, today: str
) -> None:
    """Rewrite ``updated:`` on the just-edited a4/*.md to ``today``.

    Called from the post-edit driver for every a4/*.md edit when the
    status-cascade did not already refresh `updated:` on the primary
    (i.e., no legal status transition fired). This is the mechanism that
    lets authors and the LLM stop hand-bumping `updated:` on body /
    field / wiki edits — the hook owns the bump unconditionally.

    Skips silently when:
      - The file's `type:` cannot be resolved by path (archive files,
        unrecognized layout) — those files are out of the workspace
        contract and should not be touched.
      - The file is missing or has no parseable frontmatter — schema
        violations are the Stop-hook validator's job to surface, not
        this convenience hook's.

    Idempotent on minute-resolution: a second call within the same KST
    minute writes the same value. ``rewrite_frontmatter_scalar`` appends
    `updated:` if absent — safe even on author-malformed files (the
    validator will still flag any other schema issue).
    """
    abs_path = Path(file_path)
    if not abs_path.is_file():
        return
    type_value = resolve_type_from_path(abs_path, a4_dir)
    if not type_value:
        return

    try:
        from status_cascade import parse_fm, rewrite_frontmatter_scalar, write_file
    except ImportError:
        return

    try:
        fm, raw_fm, body = parse_fm(abs_path)
    except (OSError, ValueError):
        return
    if fm is None:
        return

    try:
        new_fm = rewrite_frontmatter_scalar(raw_fm, "updated", today)
        write_file(abs_path, new_fm, body)
    except (OSError, ValueError):
        return


def _run_status_change_cascade(
    a4_dir: Path, file_path: str, project_dir: str, session_id: str, today: str
) -> bool:
    """Detect a `status:` transition on the edited file and run the
    cascade engine on related files.

    Pre-status comes from the `pre-edit` stash (PreToolUse snapshot of
    on-disk frontmatter); post-status comes from the just-written file.
    No stashed pre → silent skip (covers fresh writes, files outside
    the family-transition table, and PreToolUse no-snapshot cases).

    The hook never blocks an edit — illegal direct status edits stay
    the responsibility of the Stop-hook safety net
    (`markdown_validator.transitions`). Only legal transitions trigger
    a cascade here.

    Returns True iff `apply_status_change` ran on the primary (and thus
    refreshed `updated:` on disk). The post-edit driver uses the return
    value to dedupe its own auto-bump in Step 4 — when the cascade
    already wrote `updated:`, a second write would be redundant.
    """
    pre_map = read_prestatus(project_dir, session_id)
    pre_status = pre_map.get(file_path)
    if pre_status is None:
        return False

    abs_path = Path(file_path)
    post_status = read_status_from_disk(abs_path)

    # Drop the entry regardless of outcome — the next edit's PreToolUse
    # will repopulate from disk, so we never act on a stale pre.
    pre_map.pop(file_path, None)
    write_prestatus(project_dir, session_id, pre_map)

    if post_status is None or post_status == pre_status:
        return False

    try:
        rel_path = str(abs_path.resolve().relative_to(a4_dir.resolve()))
    except (OSError, ValueError):
        return False

    try:
        from markdown_validator.refs import RefIndex
        from status_cascade import (
            Change,
            Report,
            apply_status_change,
            detect_family,
            run_cascade,
        )
        from status_model import (
            FAMILY_TRANSITIONS,
            cascade_for,
            is_transition_legal,
        )
    except ImportError as e:
        sys.stderr.write(
            f"a4_hook post-edit: failed to import cascade modules ({e}) "
            "— skipping cascade\n"
        )
        return False

    family = detect_family(rel_path)
    if family is None or family not in FAMILY_TRANSITIONS:
        return False
    if not is_transition_legal(family, pre_status, post_status):
        # Illegal direct edit — Stop hook will surface it. Don't cascade
        # off an illegal transition.
        return False

    report = Report(
        a4_dir=str(a4_dir),
        file=rel_path,
        family=family,
        current_status=pre_status,
        target_status=post_status,
        primary=Change(
            path=rel_path,
            from_status=pre_status,
            to_status=post_status,
            reason="direct edit",
        ),
    )

    # Refresh `updated:` on the primary — the LLM wrote `status:` but
    # may not have touched `updated:`. apply_status_change is idempotent
    # on `status:` (already at post) and refreshes `updated:`.
    primary_refreshed = False
    try:
        apply_status_change(
            abs_path, pre_status, post_status, "direct edit",
            dry_run=False, today=today,
        )
        primary_refreshed = True
    except (RuntimeError, OSError) as e:
        report.errors.append(f"{rel_path}: failed to refresh updated: {e}")

    cascade_name = cascade_for(family, pre_status, post_status)
    if cascade_name is not None:
        try:
            index = RefIndex(a4_dir)
            run_cascade(
                cascade_name, a4_dir, family, rel_path, today,
                False, report, index,
            )
        except Exception as e:
            sys.stderr.write(
                f"a4_hook post-edit: cascade error ({e})\n"
            )
            return primary_refreshed

    if not report.cascades and not report.errors:
        return primary_refreshed

    _emit_cascade_context(report, file_path, project_dir)
    return primary_refreshed


def _emit_cascade_context(report, file_path: str, project_dir: str) -> None:
    """Surface cascade results as additionalContext + systemMessage.

    Per `dev/hook-conventions.md` §6: "both channels together" when a
    hook affects workspace state the user should be aware of — cascades
    rewrite related files, so a short systemMessage summary plus a
    per-file additionalContext detail is the right shape.
    """
    rel = display_rel(file_path, project_dir)
    n = len(report.cascades)
    summary = (
        f"a4 cascade: {report.primary.from_status} → "
        f"{report.primary.to_status} on {rel} "
        f"flipped {n} related file(s)"
    )

    body_lines: list[str] = []
    if report.cascades:
        body_lines.append(f"{n} cascade flip(s):")
        for c in report.cascades:
            tail = f" — {c.reason}" if c.reason else ""
            body_lines.append(
                f"  {c.path}: {c.from_status} → {c.to_status}{tail}"
            )
    if report.skipped:
        body_lines.append("")
        body_lines.append(f"{len(report.skipped)} skipped:")
        for s in report.skipped:
            body_lines.append(
                f"  {s.get('path', '?')} ({s.get('reason', '?')})"
            )
    if report.errors:
        body_lines.append("")
        body_lines.append(f"{len(report.errors)} error(s):")
        for e in report.errors:
            body_lines.append(f"  {e}")
    body = "\n".join(body_lines)

    context = (
        "## a4/ status cascade (post-edit)\n\n"
        f"`{rel}` transitioned "
        f"`{report.primary.from_status}` → `{report.primary.to_status}` "
        f"({report.family}). Related files were flipped automatically:\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "`updated:` on the primary file was refreshed to today. "
        "No action required — surface this to the user when relevant."
    )
    payload: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        },
        "systemMessage": summary,
    }
    emit(payload)


def _report_status_consistency_post(
    a4_dir: Path, file_path: str, project_dir: str
) -> None:
    try:
        from markdown_validator import status_consistency as vsc
    except ImportError:
        return

    try:
        abs_path = Path(file_path).resolve()
        rel = abs_path.relative_to(a4_dir.resolve())
    except (OSError, ValueError):
        return

    try:
        mismatches = vsc.collect_file_mismatches(a4_dir, str(rel))
    except Exception:
        return

    if not mismatches:
        return

    body_lines = [f"{len(mismatches)} status-consistency mismatch(es):"]
    for m in mismatches:
        body_lines.append(f"  {m.path} ({m.rule}): {m.message}")
    body = "\n".join(body_lines)

    rel_disp = display_rel(file_path, project_dir)
    context = (
        "## a4/ status consistency (post-edit check)\n\n"
        f"The file change to `{rel_disp}` surfaced cross-file status "
        "inconsistencies in its connected component:\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "This is informational only — no retry is forced. Surface it to "
        "the user when relevant to the current task. Rules:\n"
        "- `spec.status = superseded` iff another spec at `active` declares "
        "`supersedes: [<this>]`.\n"
        "- `idea.status = promoted` iff own `promoted:` list is non-empty.\n"
        "- `brainstorm.status = promoted` iff own `promoted:` list is "
        "non-empty."
    )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }
    )
