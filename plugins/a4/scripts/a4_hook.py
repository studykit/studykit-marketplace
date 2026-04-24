# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""a4 hook dispatcher.

Subcommands:
  post-edit      PostToolUse on Write|Edit|MultiEdit. Record the edited
                 a4/*.md path (session-scoped) and report cross-file
                 status-consistency mismatches within the edited file's
                 connected component.
  stop           Stop. Validate all a4/*.md edited in this session against
                 frontmatter and body schemas. rc=2 on violations (forces
                 Claude retry); rc=0 on clean or any internal failure.
  session-start  SessionStart. Refresh UC `implemented_by:` reverse-links,
                 then report workspace-wide status-consistency mismatches.

Conventions (state classification, lifecycle symmetry, language/invocation,
in-event ordering, non-blocking policy, output channel usage) live in
`plugins/a4/references/hook-conventions.md`.

Invoked from `plugins/a4/hooks/hooks.json` as
`uv run "${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py" <subcommand>`.

Every subcommand exits 0 except `stop`, which may exit 2 on validation
violations. Internal failures (missing env, missing scripts, subprocess
errors) never propagate — hooks must not block session/stop flows.
"""

from __future__ import annotations

import sys

# Keep top-level imports minimal so the `post-edit` fast path (fires on
# every Write/Edit/MultiEdit) pays the least per-invocation import cost.
# Each subcommand function imports what it needs locally.


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    sub = sys.argv[1]
    if sub == "post-edit":
        return _post_edit()
    if sub == "stop":
        return _stop()
    if sub == "session-start":
        return _session_start()
    return 0


# ------------------------- post-edit (PostToolUse) ------------------------


def _post_edit() -> int:
    """Record edited a4/*.md, then report status-consistency for it."""
    import json
    import os
    from pathlib import Path

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
    _record_edited(project_dir, session_id, file_path)

    # Step 2 — status-consistency report.
    if not a4_dir.is_dir():
        return 0
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        return 0
    script = Path(plugin_root) / "scripts" / "validate_status_consistency.py"
    if not script.is_file():
        return 0

    _report_status_consistency_post(a4_dir, script, file_path, project_dir)
    return 0


def _record_edited(project_dir: str, session_id: str, file_path: str) -> None:
    from pathlib import Path

    record_dir = Path(project_dir) / ".claude" / "tmp" / "a4-edited"
    try:
        record_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    record_file = record_dir / f"a4-edited-{session_id}.txt"
    try:
        with record_file.open("a") as f:
            f.write(file_path + "\n")
    except OSError:
        return


def _report_status_consistency_post(
    a4_dir, script, file_path: str, project_dir: str
) -> None:
    import subprocess

    try:
        completed = subprocess.run(
            ["uv", "run", str(script), str(a4_dir), "--file", file_path],
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return

    if completed.returncode != 2:
        return

    rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + "/")
        else file_path
    )
    body = (completed.stdout + completed.stderr).strip()
    context = (
        "## a4/ status consistency (post-edit check)\n\n"
        f"The file change to `{rel}` surfaced cross-file status "
        "inconsistencies in its connected component:\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "This is informational only — no retry is forced. Surface it to "
        "the user when relevant to the current task. Rules:\n"
        "- `decision.status = superseded` iff another decision declares "
        "`supersedes: [<this>]`.\n"
        "- `idea.status = promoted` iff own `promoted:` list is non-empty.\n"
        "- `spark/*.brainstorm.md` `status = promoted` iff own `promoted:` "
        "is non-empty."
    )
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }
    )


# -------------------------------- stop ------------------------------------


def _stop() -> int:
    """Validate a4/*.md files edited this session. rc=2 on violations."""
    import json
    import os
    import subprocess
    from pathlib import Path

    raw = sys.stdin.read()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    session_id = payload.get("session_id") or ""
    if not session_id or payload.get("stop_hook_active") is True:
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0
    record_file = (
        Path(project_dir) / ".claude" / "tmp" / "a4-edited"
        / f"a4-edited-{session_id}.txt"
    )
    if not record_file.is_file():
        return 0

    try:
        raw_paths = record_file.read_text().splitlines()
    except OSError:
        return 0

    a4_prefix = str(a4_dir) + os.sep
    edited = sorted(
        {p for p in raw_paths if p and p.startswith(a4_prefix) and Path(p).is_file()}
    )
    if not edited:
        _unlink_silent(record_file)
        return 0

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        sys.stderr.write(
            "a4_hook.py stop: CLAUDE_PLUGIN_ROOT not set — skipping validation\n"
        )
        return 0
    fm_script = Path(plugin_root) / "scripts" / "validate_frontmatter.py"
    body_script = Path(plugin_root) / "scripts" / "validate_body.py"
    if not fm_script.is_file():
        sys.stderr.write(
            f"a4_hook.py stop: {fm_script} not found — skipping validation\n"
        )
        return 0
    if not body_script.is_file():
        sys.stderr.write(
            f"a4_hook.py stop: {body_script} not found — skipping validation\n"
        )
        return 0

    fm_parts: list[str] = []
    body_parts: list[str] = []
    fm_any = False
    body_any = False

    for f in edited:
        rc, out = _run_validator(fm_script, a4_dir, f)
        if rc is None:
            sys.stderr.write(
                f"a4_hook.py stop: validate_frontmatter.py error on {f} — skipping validation\n"
            )
            return 0
        if rc == 2:
            fm_parts.append(out)
            fm_any = True
        elif rc != 0:
            sys.stderr.write(
                f"a4_hook.py stop: validate_frontmatter.py rc={rc} on {f} — skipping validation\n"
            )
            return 0

        rc, out = _run_validator(body_script, a4_dir, f)
        if rc is None:
            sys.stderr.write(
                f"a4_hook.py stop: validate_body.py error on {f} — skipping validation\n"
            )
            return 0
        if rc == 2:
            body_parts.append(out)
            body_any = True
        elif rc != 0:
            sys.stderr.write(
                f"a4_hook.py stop: validate_body.py rc={rc} on {f} — skipping validation\n"
            )
            return 0

    if not fm_any and not body_any:
        _unlink_silent(record_file)
        return 0

    out_lines = ["a4/ validators found issues in files edited this session:"]
    if fm_any:
        out_lines.append("")
        out_lines.append("--- validate_frontmatter.py ---")
        out_lines.extend(fm_parts)
    if body_any:
        out_lines.append("")
        out_lines.append("--- validate_body.py ---")
        out_lines.extend(body_parts)
    out_lines.append("")
    out_lines.append(
        "Fix the issues above before stopping. "
        "See plugins/a4/references/frontmatter-schema.md and obsidian-conventions.md."
    )
    out_lines.append(
        "For a full workspace sweep (id uniqueness etc.), run /a4:validate."
    )
    sys.stderr.write("\n".join(out_lines) + "\n")
    return 2


def _run_validator(script, a4_dir, file_path: str):
    """Return (rc, output) or (None, '') on subprocess error."""
    import subprocess

    try:
        completed = subprocess.run(
            ["uv", "run", str(script), str(a4_dir), file_path],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return (None, "")
    return (completed.returncode, completed.stdout + completed.stderr)


def _unlink_silent(path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# --------------------------- session-start --------------------------------


def _session_start() -> int:
    """Refresh implemented_by, then report status-consistency."""
    import os
    from pathlib import Path

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not project_dir or not plugin_root:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    # Order: write (refresh) → read (report).
    refresh_ctx, refresh_sys = _refresh_implemented_by(a4_dir, plugin_root)
    report_ctx = _report_status_consistency_session_start(a4_dir, plugin_root)

    ctx_parts = [p for p in (refresh_ctx, report_ctx) if p]
    if not ctx_parts and not refresh_sys:
        return 0

    payload: dict = {
        "hookSpecificOutput": {"hookEventName": "SessionStart"}
    }
    if ctx_parts:
        payload["hookSpecificOutput"]["additionalContext"] = "\n\n".join(ctx_parts)
    if refresh_sys:
        payload["systemMessage"] = refresh_sys
    _emit(payload)
    return 0


def _refresh_implemented_by(a4_dir, plugin_root: str) -> tuple[str, str]:
    """Return (additional_context_md, system_message). Empty strings on clean/fail."""
    import json
    import subprocess
    from pathlib import Path

    script = Path(plugin_root) / "scripts" / "refresh_implemented_by.py"
    if not script.is_file():
        return ("", "")
    try:
        completed = subprocess.run(
            ["uv", "run", str(script), str(a4_dir), "--json"],
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ("", "")
    if completed.returncode != 0:
        return ("", "")
    try:
        report = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return ("", "")

    changes = report.get("changes") or []
    errors = report.get("errors") or []
    if not changes and not errors:
        return ("", "")

    summary_parts: list[str] = []
    if changes:
        summary_parts.append(f"refreshed implemented_by on {len(changes)} UC(s)")
    if errors:
        summary_parts.append(f"{len(errors)} error(s)")
    system_message = ", ".join(summary_parts)
    if errors:
        system_message += " — see context"

    lines: list[str] = ["## a4/ implemented_by refresh (SessionStart)", ""]
    if changes:
        lines.append(f"Refreshed `implemented_by:` on {len(changes)} UC(s):")
        lines.append("")
        for ch in changes:
            uc = ch.get("uc", "?")
            prev = ch.get("previous") or []
            new = ch.get("new") or []
            lines.append(f"- `{uc}`: `{prev}` → `{new}`")
        lines.append("")
    if errors:
        lines.append(f"Errors ({len(errors)}):")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")
    lines.append(
        "`implemented_by:` is auto-maintained by "
        "`scripts/refresh_implemented_by.py`; the SessionStart hook "
        "reconciles drift from cross-branch edits or manual task edits."
    )
    return ("\n".join(lines), system_message)


def _report_status_consistency_session_start(a4_dir, plugin_root: str) -> str:
    """Return additional_context_md or empty string."""
    import subprocess
    from pathlib import Path

    script = Path(plugin_root) / "scripts" / "validate_status_consistency.py"
    if not script.is_file():
        return ""
    try:
        completed = subprocess.run(
            ["uv", "run", str(script), str(a4_dir)],
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""
    if completed.returncode != 2:
        return ""

    body = (completed.stdout + completed.stderr).strip()
    return (
        "## a4/ status consistency (SessionStart check)\n\n"
        "The following cross-file status inconsistencies exist in the "
        "current `a4/` workspace. They are informational only — no "
        "immediate action is required, but surface them when the user "
        "works on related files.\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "Rules checked:\n"
        "- `decision.status = superseded` iff another decision declares "
        "`supersedes: [<this>]`.\n"
        "- `idea.status = promoted` iff own `promoted:` list is non-empty.\n"
        "- `spark/*.brainstorm.md` `status = promoted` iff own `promoted:` "
        "is non-empty.\n\n"
        "See `plugins/a4/references/frontmatter-schema.md` for the "
        "underlying schema."
    )


# -------------------------- shared helpers --------------------------------


def _emit(payload: dict) -> None:
    import json

    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
