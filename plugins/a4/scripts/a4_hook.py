# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
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
  user-prompt    UserPromptSubmit. Scan the prompt for `#<id>` references
                 and inject resolved `a4/<type>/<id>-<slug>.md` paths as
                 `additionalContext` so Claude reads the file directly
                 instead of searching for it.

Conventions (state classification, lifecycle symmetry, language/invocation,
in-event ordering, non-blocking policy, output channel usage) live in
`plugins/a4/references/hook-conventions.md`.

Invoked from `plugins/a4/hooks/hooks.json` as
`uv run "${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py" <subcommand>`.

Sibling scripts (`validate_frontmatter.py`, `validate_body.py`,
`validate_status_consistency.py`, `refresh_implemented_by.py`) are called
in-process via `import` rather than `uv run` subprocess, so per-invocation
interpreter startup is paid once — not once per validator call.

Every subcommand exits 0 except `stop`, which may exit 2 on validation
violations. Internal failures (missing env, missing modules, library
errors) never propagate — hooks must not block session/stop flows.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Sibling scripts live next to this file. Make them importable regardless of
# how uv invokes python (explicit — do not rely on sys.path[0] auto-insertion).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

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
    if sub == "user-prompt":
        return _user_prompt()
    return 0


# ------------------------- post-edit (PostToolUse) ------------------------


def _post_edit() -> int:
    """Record edited a4/*.md, then report status-consistency for it."""
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
    _record_edited(project_dir, session_id, file_path)

    # Step 2 — status-consistency report.
    if not a4_dir.is_dir():
        return 0

    _report_status_consistency_post(a4_dir, file_path, project_dir)
    return 0


def _record_edited(project_dir: str, session_id: str, file_path: str) -> None:
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
    a4_dir: Path, file_path: str, project_dir: str
) -> None:
    try:
        import validate_status_consistency as vsc
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

    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + "/")
        else file_path
    )
    context = (
        "## a4/ status consistency (post-edit check)\n\n"
        f"The file change to `{display_rel}` surfaced cross-file status "
        "inconsistencies in its connected component:\n\n"
        "```\n"
        f"{body}\n"
        "```\n\n"
        "This is informational only — no retry is forced. Surface it to "
        "the user when relevant to the current task. Rules:\n"
        "- `spec.status = superseded` iff another spec at `active` declares "
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

    try:
        import validate_frontmatter as vfm
        import validate_body as vbody
        from markdown import extract_preamble
    except ImportError as e:
        sys.stderr.write(
            f"a4_hook.py stop: failed to import validators ({e}) — skipping validation\n"
        )
        return 0

    try:
        wikis = vbody.discover_wiki_pages(a4_dir)
        issues = vbody.discover_issues(a4_dir)
        sparks = vbody.discover_sparks(a4_dir)
    except Exception as e:
        sys.stderr.write(
            f"a4_hook.py stop: body index build failed ({e}) — skipping validation\n"
        )
        return 0

    fm_violations: list = []
    body_violations: list = []

    try:
        for f in edited:
            path = Path(f)
            preamble = extract_preamble(path)
            if preamble.fm is None:
                missing = vfm.check_missing_frontmatter(path, a4_dir)
                if missing is not None:
                    fm_violations.append(missing)
            else:
                fm_violations.extend(vfm.validate_file(path, a4_dir, preamble.fm))
            body_violations.extend(
                vbody.validate_file(path, a4_dir, wikis, issues, sparks)
            )
    except Exception as e:
        sys.stderr.write(
            f"a4_hook.py stop: validator error ({e}) — skipping validation\n"
        )
        return 0

    if not fm_violations and not body_violations:
        _unlink_silent(record_file)
        return 0

    out_lines = ["a4/ validators found issues in files edited this session:"]
    if fm_violations:
        fm_file_count = len({v.path for v in fm_violations})
        out_lines.append("")
        out_lines.append("--- validate_frontmatter.py ---")
        out_lines.append(
            f"{len(fm_violations)} violation(s) across {fm_file_count} file(s):"
        )
        for v in fm_violations:
            loc = v.path + (f" [{v.field}]" if v.field else "")
            out_lines.append(f"  {loc} ({v.rule}): {v.message}")
    if body_violations:
        body_file_count = len({v.path for v in body_violations})
        out_lines.append("")
        out_lines.append("--- validate_body.py ---")
        out_lines.append(
            f"{len(body_violations)} violation(s) across {body_file_count} file(s):"
        )
        for v in body_violations:
            loc = v.path + (f":{v.line}" if v.line is not None else "")
            out_lines.append(f"  {loc} ({v.rule}): {v.message}")
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


def _unlink_silent(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# --------------------------- session-start --------------------------------


def _session_start() -> int:
    """Refresh implemented_by, then report consistency."""
    import os

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    # Order: write (refresh) → read (report).
    refresh_ctx, refresh_sys = _refresh_implemented_by(a4_dir)
    report_ctx = _report_status_consistency_session_start(a4_dir)

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


def _refresh_implemented_by(a4_dir: Path) -> tuple[str, str]:
    """Return (additional_context_md, system_message). Empty strings on clean/fail."""
    try:
        import refresh_implemented_by as rib
    except ImportError:
        return ("", "")

    try:
        report = rib.refresh_all(a4_dir, dry_run=False)
    except Exception:
        return ("", "")

    changes = report.changes
    errors = report.errors
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
            lines.append(f"- `{ch.uc}`: `{ch.previous}` → `{ch.new}`")
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


def _report_status_consistency_session_start(a4_dir: Path) -> str:
    """Return additional_context_md or empty string."""
    try:
        import validate_status_consistency as vsc
    except ImportError:
        return ""

    try:
        mismatches = vsc.collect_workspace_mismatches(a4_dir)
    except Exception:
        return ""

    if not mismatches:
        return ""

    body_lines = [f"{len(mismatches)} status-consistency mismatch(es):"]
    for m in mismatches:
        body_lines.append(f"  {m.path} ({m.rule}): {m.message}")
    body = "\n".join(body_lines)

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
        "- `spec.status = superseded` iff another spec at `active` declares "
        "`supersedes: [<this>]`.\n"
        "- `idea.status = promoted` iff own `promoted:` list is non-empty.\n"
        "- `spark/*.brainstorm.md` `status = promoted` iff own `promoted:` "
        "is non-empty.\n\n"
        "See `plugins/a4/references/frontmatter-schema.md` for the "
        "underlying schema."
    )


# -------------------------- user-prompt (UserPromptSubmit) ----------------


_MAX_IDS = 20
_LOOKUP_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "review",
    "spec",
    "idea",
)
# Folders that hold kind-scoped subfolders (e.g. `task/feature/`) — the
# `#<id>` resolver must rglob into them to find the actual file.
_NESTED_LOOKUP_FOLDERS: frozenset[str] = frozenset({"task"})


def _user_prompt() -> int:
    """Resolve `#<id>` references in the prompt to a4/ file paths.

    Dedupes within a session via a record file at
    `.claude/tmp/a4-edited/a4-resolved-ids-<sid>.txt`: an id whose path
    was already injected this session is skipped on subsequent prompts.
    Cleanup is handled by the same SessionEnd / SessionStart-sweep hooks
    that manage `a4-edited-<sid>.txt`.
    """
    import json
    import os
    import re

    raw = sys.stdin.read()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    prompt = payload.get("prompt") or ""
    session_id = payload.get("session_id") or ""
    if not prompt or not session_id:
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    # `#<id>`. Negative lookbehind `(?<![\w#])` rejects markdown headings
    # (`##h`, `#####`) and word-attached `#` (`abc#42`). `\b` after `\d+`
    # rejects `#42x`. `re` is imported here (not at module scope) so the
    # post-edit fast path stays slim.
    id_pattern = re.compile(r"(?<![\w#])#(\d+)\b")

    # Dedupe in first-occurrence order; cap to bound work.
    seen: set[str] = set()
    ids: list[str] = []
    for m in id_pattern.finditer(prompt):
        token = m.group(1)
        if token in seen:
            continue
        seen.add(token)
        ids.append(token)
        if len(ids) >= _MAX_IDS:
            break
    if not ids:
        return 0

    already = _read_resolved_ids(project_dir, session_id)
    fresh = [t for t in ids if t not in already]
    if not fresh:
        return 0

    project_prefix = project_dir + os.sep
    resolved: list[tuple[str, list[str]]] = []
    for token in fresh:
        matches: list[str] = []
        for folder in _LOOKUP_FOLDERS:
            sub = a4_dir / folder
            if not sub.is_dir():
                continue
            pattern = f"{token}-*.md"
            iter_paths = (
                sub.rglob(pattern)
                if folder in _NESTED_LOOKUP_FOLDERS
                else sub.glob(pattern)
            )
            matches.extend(str(p) for p in sorted(iter_paths))
        archive = a4_dir / "archive"
        if archive.is_dir():
            matches.extend(
                str(p) for p in sorted(archive.rglob(f"{token}-*.md"))
            )
        if matches:
            display = [
                p[len(project_prefix):] if p.startswith(project_prefix) else p
                for p in matches
            ]
            resolved.append((token, display))

    if not resolved:
        return 0

    _record_resolved_ids(project_dir, session_id, [t for t, _ in resolved])

    # Terse on purpose — only the path is actionable. No header / footer:
    # `#<id> → path` is self-explanatory in context, and meta-explanation
    # (folder=type, dedupe behavior) is not re-injected on every prompt.
    lines = []
    for token, paths in resolved:
        joined = ", ".join(paths)
        lines.append(f"- #{token} → {joined}")
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(lines),
            }
        }
    )
    return 0


def _resolved_ids_path(project_dir: str, session_id: str) -> Path:
    return (
        Path(project_dir)
        / ".claude"
        / "tmp"
        / "a4-edited"
        / f"a4-resolved-ids-{session_id}.txt"
    )


def _read_resolved_ids(project_dir: str, session_id: str) -> set[str]:
    path = _resolved_ids_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        return {line.strip() for line in path.read_text().splitlines() if line.strip()}
    except OSError:
        return set()


def _record_resolved_ids(
    project_dir: str, session_id: str, tokens: list[str]
) -> None:
    if not tokens:
        return
    path = _resolved_ids_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with path.open("a") as f:
            for t in tokens:
                f.write(t + "\n")
    except OSError:
        return


# -------------------------- shared helpers --------------------------------


def _emit(payload: dict) -> None:
    import json

    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
