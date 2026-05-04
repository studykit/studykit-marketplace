"""PostToolUse subcommand: record + cascade + consistency.

Supports Claude Code Write/Edit/MultiEdit payloads and Codex apply_patch
payloads. Codex apply_patch can touch several files in one hook invocation,
so Codex-mode stdout is aggregated into a single JSON object before return.

Driver order in :func:`post_edit`:

1. Record the edited a4/*.md path (session-scoped, fail-open).
2. Run the status-change cascade if pre→post is a legal transition.
3. Report cross-file status-consistency mismatches on the post-cascade state.

Cascade results surface as additionalContext + systemMessage.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    display_rel,
    emit,
    project_dir_from_payload,
    read_prestatus,
    read_status_from_disk,
    record_edited,
    trace,
    write_prestatus,
)
from a4_hook._runtime import select_hook_strategy


def post_edit() -> int:
    """PostToolUse entry point. Always exits 0.

    Order matters: cascade runs *before* the consistency report so the
    report describes the post-cascade workspace (otherwise cascaded
    files would briefly look inconsistent and produce noise).
    """
    import contextlib
    import io
    import json
    import os

    raw = sys.stdin.read()
    if not raw:
        trace(project_dir_from_payload({}), None, "post-edit", "abort", reason="no_payload")
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        trace(project_dir_from_payload({}), None, "post-edit", "abort", reason="bad_json")
        return 0

    session_id = payload.get("session_id") or ""
    if not session_id:
        trace(
            project_dir_from_payload(payload),
            None,
            "post-edit",
            "abort",
            reason="no_session_id",
            tool_name=payload.get("tool_name"),
        )
        return 0

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        trace(None, session_id, "post-edit", "abort", reason="no_project_dir")
        return 0
    a4_dir = Path(project_dir) / "a4"
    a4_prefix = str(a4_dir) + os.sep

    strategy = select_hook_strategy(payload)
    targets = strategy.edit_targets(payload, project_dir)
    if not targets:
        trace(
            project_dir,
            session_id,
            "post-edit",
            "abort",
            reason="no_targets",
            runtime=strategy.name,
            tool_name=payload.get("tool_name"),
        )
        return 0

    if not a4_dir.is_dir():
        trace(
            project_dir,
            session_id,
            "post-edit",
            "abort",
            reason="no_a4_dir",
            a4_dir=str(a4_dir),
            targets=[t.path for t in targets],
        )
        return 0

    trace(
        project_dir,
        session_id,
        "post-edit",
        "targets",
        runtime=strategy.name,
        aggregate_output=strategy.aggregate_posttooluse_output,
        count=len(targets),
        paths=[t.path for t in targets],
    )

    if strategy.aggregate_posttooluse_output:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            for target in targets:
                _post_edit_one(
                    a4_dir, a4_prefix, target.path, project_dir, session_id
                )
        _emit_codex_post_aggregate(captured.getvalue())
    else:
        for target in targets:
            _post_edit_one(
                a4_dir, a4_prefix, target.path, project_dir, session_id
            )
    return 0


def _post_edit_one(
    a4_dir: Path,
    a4_prefix: str,
    file_path: str,
    project_dir: str,
    session_id: str,
) -> None:
    if not file_path.startswith(a4_prefix):
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip",
            reason="outside_a4",
            file_path=file_path,
            a4_dir=str(a4_dir),
        )
        return

    # Step 1 — record (session-scoped, fail-open).
    record_edited(project_dir, session_id, file_path)
    trace(
        project_dir,
        session_id,
        "post-edit",
        "record_edited",
        file_path=file_path,
    )

    # Step 2 — status-change cascade (runs before consistency report).
    _run_status_change_cascade(
        a4_dir, file_path, project_dir, session_id
    )

    # Step 3 — status-consistency report on the (now post-cascade) state.
    _report_status_consistency_post(a4_dir, file_path, project_dir)


def _emit_codex_post_aggregate(raw: str) -> None:
    """Collapse multiple internal post-edit emissions into one Codex JSON.

    Codex hook stdout is parsed as a single JSON object. The a4 post-edit
    pipeline can emit more than one JSON object when one patch touches several
    connected a4 files, so plugin-hook invocations aggregate them before
    returning to Codex.
    """
    import json

    contexts: list[str] = []
    messages: list[str] = []
    invalid: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            invalid.append(line.strip())
            continue
        if isinstance(payload, dict):
            msg = payload.get("systemMessage")
            if isinstance(msg, str) and msg.strip():
                messages.append(msg.strip())
            hook_specific = payload.get("hookSpecificOutput")
            if isinstance(hook_specific, dict):
                ctx = hook_specific.get("additionalContext")
                if isinstance(ctx, str) and ctx.strip():
                    contexts.append(ctx.strip())

    if invalid and not contexts and not messages:
        messages.append("\n".join(invalid))

    if not contexts and not messages:
        return

    out: dict = {}
    if contexts:
        out["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n\n---\n\n".join(contexts),
        }
    if messages:
        out["systemMessage"] = " | ".join(messages)
    emit(out)


def _run_status_change_cascade(
    a4_dir: Path, file_path: str, project_dir: str, session_id: str
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

    Returns True iff a cascade ran or reported errors; the post-edit driver
    currently ignores the value.
    """
    pre_map = read_prestatus(project_dir, session_id)
    pre_status = pre_map.get(file_path)
    if pre_status is None:
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="no_prestatus",
            file_path=file_path,
        )
        return False

    abs_path = Path(file_path)
    post_status = read_status_from_disk(abs_path)

    # Drop the entry regardless of outcome — the next edit's PreToolUse
    # will repopulate from disk, so we never act on a stale pre.
    pre_map.pop(file_path, None)
    write_prestatus(project_dir, session_id, pre_map)

    if post_status is None or post_status == pre_status:
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="status_unchanged_or_missing",
            file_path=file_path,
            pre_status=pre_status,
            post_status=post_status,
        )
        return False

    try:
        rel_path = str(abs_path.resolve().relative_to(a4_dir.resolve()))
    except (OSError, ValueError):
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="outside_a4_after_resolve",
            file_path=file_path,
        )
        return False

    try:
        from markdown_validator.refs import RefIndex
        from status_cascade import (
            Change,
            Report,
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
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="import_cascade_failed",
            file_path=file_path,
            error=str(e),
        )
        return False

    family = detect_family(rel_path)
    if family is None or family not in FAMILY_TRANSITIONS:
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="family_without_transitions",
            file_path=file_path,
            family=family,
        )
        return False
    if not is_transition_legal(family, pre_status, post_status):
        # Illegal direct edit — Stop hook will surface it. Don't cascade
        # off an illegal transition.
        trace(
            project_dir,
            session_id,
            "post-edit",
            "skip_cascade",
            reason="illegal_transition",
            file_path=file_path,
            family=family,
            pre_status=pre_status,
            post_status=post_status,
        )
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

    cascade_name = cascade_for(family, pre_status, post_status)
    if cascade_name is not None:
        try:
            index = RefIndex(a4_dir)
            run_cascade(
                cascade_name, a4_dir, family, rel_path, "",
                False, report, index,
            )
        except Exception as e:
            sys.stderr.write(
                f"a4_hook post-edit: cascade error ({e})\n"
            )
            trace(
                project_dir,
                session_id,
                "post-edit",
                "cascade_error",
                file_path=file_path,
                cascade=cascade_name,
                error=str(e),
            )
            return False

    if not report.cascades and not report.errors:
        trace(
            project_dir,
            session_id,
            "post-edit",
            "cascade_complete",
            file_path=file_path,
            family=family,
            cascade=cascade_name,
            cascades=0,
            errors=0,
        )
        return False

    _emit_cascade_context(report, file_path, project_dir)
    trace(
        project_dir,
        session_id,
        "post-edit",
        "cascade_complete",
        file_path=file_path,
        family=family,
        cascade=cascade_name,
        cascades=len(report.cascades),
        errors=len(report.errors),
    )
    return True


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
