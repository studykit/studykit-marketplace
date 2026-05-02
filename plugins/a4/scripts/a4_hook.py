# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""a4 hook dispatcher.

Subcommands:
  pre-edit       PreToolUse on Write|Edit|MultiEdit. Two responsibilities
                 on the same a4/*.md gate:
                 (1) Stash the on-disk ``status:`` into a session-scoped
                 JSON map. Consumed by ``post-edit`` to detect ``status:``
                 transitions precisely (pre vs post on disk, instead of
                 HEAD vs working tree).
                 (2) Inject the type-specific authoring-contract pointers
                 as ``additionalContext`` once per type per session.
                 Silent on subsequent edits to any file of the same type.
  post-edit      PostToolUse on Write|Edit|MultiEdit. Record the edited
                 a4/*.md path (session-scoped), report cross-file
                 status-consistency mismatches within the edited file's
                 connected component, and — if ``status:`` changed
                 legally — run the cascade (supersedes / discarded /
                 revising) on related files and refresh ``updated:`` on
                 the primary. Cascade results surface as
                 additionalContext + systemMessage.
  stop           Stop. Validate all a4/*.md edited in this session against
                 (1) the frontmatter schema and (2) status-transition
                 legality (HEAD vs working tree, via git). rc=2 on
                 violations (forces Claude retry); rc=0 on clean or any
                 internal failure.
  user-prompt    UserPromptSubmit. Scan the prompt for `#<id>` references
                 and inject resolved `a4/<type>/<id>-<slug>.md` paths as
                 `additionalContext` so Claude reads the file directly
                 instead of searching for it.
  session-start  SessionStart. Inject the canonical type → file-location
                 map for the `<project-root>/a4/` workspace plus the
                 runnable `allocate_id.py` command as
                 `additionalContext`, so the LLM places new files in
                 the right folder and allocates a workspace-global
                 monotonic id before any PreToolUse fires. The map is
                 built dynamically from `common.WIKI_TYPES` and
                 `common.ISSUE_FOLDERS` — adding a new type updates the
                 injection automatically. Silent when the project has
                 no `a4/` directory.

SessionStart does not run workspace-wide status-consistency reporting —
that sweep is manual via `/a4:validate` (or `validate.py`).

Conventions (state classification, lifecycle symmetry, language/invocation,
in-event ordering, non-blocking policy, output channel usage) live in
`plugins/a4/dev/hook-conventions.md`.

Invoked from `plugins/a4/hooks/hooks.json` as
`uv run "${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py" <subcommand>`.

The `markdown_validator` package next to this file is imported in-process
rather than shelled out via `uv run`, so per-invocation interpreter
startup is paid once — not once per validator call.

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
    if sub == "pre-edit":
        return _pre_edit()
    if sub == "post-edit":
        return _post_edit()
    if sub == "stop":
        return _stop()
    if sub == "user-prompt":
        return _user_prompt()
    if sub == "session-start":
        return _session_start()
    return 0


# ------------------------- prestatus stash IO -----------------------------
#
# Session-scoped state under `.claude/tmp/a4-edited/a4-prestatus-<sid>.json`:
# a `{abs_path: pre_status}` map populated by `pre-edit` (PreToolUse) and
# consumed by `post-edit` (PostToolUse) to detect `status:` transitions.
# Per `dev/hook-conventions.md` §2 Rule A, paired cleanup runs at
# SessionEnd (`hooks/cleanup-edited-a4.sh`) with a SessionStart safety-net
# sweep (`hooks/sweep-old-edited-a4.sh`) for crashed sessions.


def _prestatus_file(project_dir: str, session_id: str) -> "Path":
    return (
        Path(project_dir) / ".claude" / "tmp" / "a4-edited"
        / f"a4-prestatus-{session_id}.json"
    )


def _read_prestatus(project_dir: str, session_id: str) -> dict:
    import json

    path = _prestatus_file(project_dir, session_id)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_prestatus(project_dir: str, session_id: str, data: dict) -> None:
    import json

    path = _prestatus_file(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        return


def _read_status_from_disk(path: "Path") -> str | None:
    """Return the `status:` scalar from the file's frontmatter, or None if
    absent / unreadable. Used by both pre-edit (snapshot) and post-edit
    (compare) so they see the disk through the same lens.
    """
    try:
        from markdown import extract_preamble
    except ImportError:
        return None
    try:
        preamble = extract_preamble(path)
    except (OSError, ValueError):
        return None
    if preamble.fm is None:
        return None
    s = preamble.fm.get("status")
    return s if isinstance(s, str) else None


# ----------------------- newfiles snapshot IO -----------------------------
#
# Session-scoped state under
# ``.claude/tmp/a4-edited/a4-newfiles-<sid>.txt`` — one absolute path per
# line, populated by ``pre-edit`` when the tool is about to Write a file
# that does not yet exist on disk. Consumed by ``post-edit`` to decide
# whether to stamp ``created:`` on the post-write frontmatter. Cleaned up
# alongside the other session-scoped a4-edited family files.


def _newfiles_path(project_dir: str, session_id: str) -> "Path":
    return (
        Path(project_dir) / ".claude" / "tmp" / "a4-edited"
        / f"a4-newfiles-{session_id}.txt"
    )


def _read_newfiles(project_dir: str, session_id: str) -> set[str]:
    path = _newfiles_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        return {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()


def _record_newfile(
    project_dir: str, session_id: str, file_path: str
) -> None:
    path = _newfiles_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(file_path + "\n")
    except OSError:
        return


def _drop_newfile(
    project_dir: str, session_id: str, file_path: str
) -> None:
    path = _newfiles_path(project_dir, session_id)
    if not path.is_file():
        return
    try:
        lines = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and line.strip() != file_path
        ]
    except OSError:
        return
    try:
        if lines:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            path.unlink()
    except OSError:
        return


# -------------------------- pre-edit (PreToolUse) -------------------------


def _pre_edit() -> int:
    """Two responsibilities on the same a4/*.md gate:
      (1) Stash on-disk `status:` for the a4/*.md the tool is about to
          write. Files outside `a4/`, non-md files, missing `status:`,
          new files (no on-disk frontmatter), and parse failures are
          silent no-ops — the post-edit consumer treats absence as
          "no transition to detect".
      (2) Inject type-specific authoring-contract pointers once per
          type per session, for both existing-file edits and new-file
          Writes (issue creation). Sole mechanism for surfacing
          authoring contracts at edit time.

    Always exits 0.
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

    abs_path = Path(file_path)

    # Responsibility 1 — pre-status snapshot for cascade detection.
    # Only meaningful when the file already exists; new-file Writes have
    # no prior `status:` and post-edit treats absence as "no transition".
    if abs_path.is_file():
        pre = _read_status_from_disk(abs_path)
        if pre is not None:
            data = _read_prestatus(project_dir, session_id)
            data[file_path] = pre
            _write_prestatus(project_dir, session_id, data)
    else:
        # File doesn't exist yet — record so post-edit can stamp
        # `created:` after the Write lands. Only Write can create files
        # in Claude Code's tool model; Edit/MultiEdit require a prior
        # Read of an existing file.
        if payload.get("tool_name") == "Write":
            _record_newfile(project_dir, session_id, file_path)

    # Responsibility 2 — authoring-contract injection (one-shot per
    # (file, type) per session). Fires for both edits and new-file
    # Writes — type is resolved from path (`a4/<folder>/...`), which
    # works without on-disk frontmatter, so issue creation gets the
    # binding contract before authoring. Dedupe still suppresses repeat
    # injections on subsequent edits to the same file.
    _maybe_inject_authoring_contract(
        abs_path, file_path, a4_dir, project_dir, session_id
    )
    return 0


# -------------------- authoring-contract injection ------------------------
#
# Lazy, edit-intent-only surfacing of `authoring/*.md` contracts. Fires
# from PreToolUse so a pure read of an `a4/*.md` file does NOT pull in
# the contract; only an imminent Write/Edit/MultiEdit does. Covers both
# edits to existing files and new-file Writes (issue creation) — type
# is resolved by path, which works without on-disk frontmatter. Deduped
# per type per session — the contract is a per-type binding (the same
# `<type>-authoring.md` applies to every file of that type), so once
# the LLM has seen the umbrella/task/... contract this session, editing
# another file of the same type re-emits nothing.
#
# Type resolution is by path (`common.WIKI_TYPES` / `common.ISSUE_FOLDERS`),
# not by frontmatter parse — the a4 layout pins type by location, so an
# extra file IO is unnecessary. Archive files are skipped.
#
# Session-scoped state at `.claude/tmp/a4-edited/a4-injected-<sid>.txt`,
# one `<type>` per line. Cleaned up by the same SessionEnd / SessionStart-sweep
# paths that handle the other a4-edited family files
# (`hooks/cleanup-edited-a4.sh`, `hooks/sweep-old-edited-a4.sh`).


_TASK_FAMILY_TYPES = frozenset({"task", "bug", "spike", "research"})
_ISSUE_BODY_TYPES = frozenset(
    {
        "task",
        "bug",
        "spike",
        "research",
        "usecase",
        "spec",
        "umbrella",
        "review",
        "idea",
        "brainstorm",
    }
)
_WIKI_BODY_TYPES = frozenset(
    {
        "actors",
        "architecture",
        "bootstrap",
        "context",
        "domain",
        "nfr",
    }
)


def _injected_path(project_dir: str, session_id: str) -> "Path":
    return (
        Path(project_dir) / ".claude" / "tmp" / "a4-edited"
        / f"a4-injected-{session_id}.txt"
    )


def _read_injected(project_dir: str, session_id: str) -> set[str]:
    path = _injected_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        # Strip any pre-existing `<file>\t<type>` lines too — older sessions
        # may still have the (file, type) format on disk; treat the type
        # column as authoritative and ignore the file column.
        return {
            (line.split("\t", 1)[1] if "\t" in line else line).strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()


def _record_injected(
    project_dir: str, session_id: str, type_value: str
) -> None:
    path = _injected_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{type_value}\n")
    except OSError:
        return


def _resolve_type_from_path(abs_path: "Path", a4_dir: "Path") -> str | None:
    """Resolve frontmatter `type:` from the file's location under `a4/`.

    The a4 layout pins `type:` by path: top-level `<wiki>.md` files map
    to `WIKI_TYPES`, and flat `<folder>/<id>-<slug>.md` files map to
    `ISSUE_FOLDERS`. Resolving by path avoids a frontmatter parse on
    every edit (cheaper than reading the file just to read `type:`)
    and matches the canonical layout used by `discover_files` and the
    validators. Path-based resolution also works for new-file Writes
    (issue creation), where on-disk frontmatter does not exist yet.

    Returns None for archived files (`a4/archive/...`) — archived files
    retain their original `type:` but are not active edit targets, so
    contract injection is skipped.
    """
    try:
        rel = abs_path.resolve(strict=False).relative_to(a4_dir.resolve())
    except (OSError, ValueError):
        return None
    parts = rel.parts
    if not parts:
        return None
    if parts[0] == "archive":
        return None
    try:
        from common import ISSUE_FOLDERS, WIKI_TYPES
    except ImportError:
        return None
    if len(parts) == 1 and parts[0].endswith(".md"):
        stem = parts[0][:-3]
        return stem if stem in WIKI_TYPES else None
    if len(parts) >= 2 and parts[0] in ISSUE_FOLDERS:
        return parts[0]
    return None


def _maybe_inject_authoring_contract(
    abs_path: "Path",
    file_path: str,
    a4_dir: "Path",
    project_dir: str,
    session_id: str,
) -> None:
    """Inject pointer-style authoring-contract context once per type
    per session. Silent when the type cannot be resolved from path
    (archive files, unrecognized layout).
    """
    type_value = _resolve_type_from_path(abs_path, a4_dir)
    if not type_value:
        return

    plugin_root = Path(__file__).resolve().parent.parent
    type_doc = plugin_root / "authoring" / f"{type_value}-authoring.md"
    if not type_doc.is_file():
        return

    already = _read_injected(project_dir, session_id)
    if type_value in already:
        return
    _record_injected(project_dir, session_id, type_value)

    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + "/")
        else file_path
    )

    pointers = [
        "- `plugins/a4/authoring/frontmatter-common.md` — cross-cutting "
        "frontmatter rules (`type:`, path references, empty collections, "
        "unknown fields, `created` / `updated`).",
    ]
    if type_value in _ISSUE_BODY_TYPES:
        pointers.append(
            "- `plugins/a4/authoring/frontmatter-issue.md` — issue-side "
            "rules (`id`, title placeholders, relationships, status "
            "changes and cascades, structural relationship fields)."
        )
    else:
        pointers.append(
            "- `plugins/a4/authoring/frontmatter-wiki.md` — wiki minimal "
            "frontmatter contract."
        )
    pointers.extend([
        f"- `plugins/a4/authoring/{type_value}-authoring.md` — per-type "
        "field table, lifecycle, body shape, common mistakes.",
        "- `plugins/a4/authoring/body-conventions.md` — cross-cutting "
        "body conventions (heading form, link form).",
    ])
    if type_value in _ISSUE_BODY_TYPES:
        pointers.append(
            "- `plugins/a4/authoring/issue-body.md` — `## Resume` "
            "(current-state snapshot) and `## Log` (narrative-worthy "
            "events) for issue files."
        )
    if type_value in _WIKI_BODY_TYPES:
        pointers.append(
            "- `plugins/a4/authoring/wiki-body.md` — `## Change Logs` "
            "audit trail and Wiki Update Protocol."
        )
    if type_value in _TASK_FAMILY_TYPES:
        pointers.insert(
            2,
            "- `plugins/a4/authoring/issue-family-lifecycle.md` — "
            "issue-family lifecycle (status enum, transitions, writer "
            "rules).",
        )

    body = "\n".join(pointers)
    context = (
        f"## a4 authoring contract — `type: {type_value}`\n\n"
        f"About to edit `{display_rel}`. Read these contracts before "
        "writing — they are the binding schema/body contract for this "
        "type, not optional.\n\n"
        f"{body}\n\n"
        f"Injected once per `type: {type_value}` per session — subsequent "
        "edits to any file of this type will not re-emit this notice."
    )
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }
    )


# ------------------------- post-edit (PostToolUse) ------------------------


def _post_edit() -> int:
    """Record edited a4/*.md, run status-change cascade if applicable,
    then report cross-file status-consistency.

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
    _record_edited(project_dir, session_id, file_path)

    if not a4_dir.is_dir():
        return 0

    # Step 2 — stamp `created:` if this Write created a new file. Runs
    # before the cascade so a status flip (which also touches `updated:`)
    # sees a frontmatter that already carries `created:`, and `created:`
    # ends up immediately above `updated:` (their canonical order).
    _maybe_stamp_created(a4_dir, file_path, project_dir, session_id)

    # Step 3 — status-change cascade (runs before consistency report).
    _run_status_change_cascade(a4_dir, file_path, project_dir, session_id)

    # Step 4 — status-consistency report on the (now post-cascade) state.
    _report_status_consistency_post(a4_dir, file_path, project_dir)
    return 0


def _maybe_stamp_created(
    a4_dir: Path, file_path: str, project_dir: str, session_id: str
) -> None:
    """Stamp `created:` on a freshly Written a4/*.md whose schema requires it.

    Triggers iff:
      - PreToolUse recorded the path as new (file did not exist on disk).
      - The file now exists.
      - Its `type:` (resolved by path) is in the schema-derived
        ``types_with_created()`` set.
      - Its current frontmatter does not already carry a non-empty
        `created:` value (immutable — never overwrite an author-written
        timestamp).

    Inserts ``created: <now-kst>`` immediately before ``updated:`` if
    that line exists, else appends at the frontmatter end. Failure on
    any step is silent — stamping is a convenience, not a gate.
    """
    new_files = _read_newfiles(project_dir, session_id)
    if file_path not in new_files:
        return

    abs_path = Path(file_path)
    if not abs_path.is_file():
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        type_value = _resolve_type_from_path(abs_path, a4_dir)
    except Exception:
        _drop_newfile(project_dir, session_id, file_path)
        return
    if not type_value:
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        from markdown_validator.frontmatter import types_with_created
    except ImportError:
        _drop_newfile(project_dir, session_id, file_path)
        return
    if type_value not in types_with_created():
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        from common import now_kst
        from markdown import extract_preamble
        from status_cascade import parse_fm, write_file
    except ImportError:
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        preamble = extract_preamble(abs_path)
    except (OSError, ValueError):
        _drop_newfile(project_dir, session_id, file_path)
        return
    if preamble.fm is None:
        _drop_newfile(project_dir, session_id, file_path)
        return

    existing = preamble.fm.get("created")
    if isinstance(existing, str) and existing.strip():
        _drop_newfile(project_dir, session_id, file_path)
        return
    if existing is not None and not isinstance(existing, str):
        # date / datetime / int — already populated by the author. Don't
        # overwrite, even if not a string.
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        _, raw_fm, body = parse_fm(abs_path)
    except (OSError, ValueError):
        _drop_newfile(project_dir, session_id, file_path)
        return

    try:
        new_fm = _insert_created_before_updated(raw_fm, now_kst())
        write_file(abs_path, new_fm, body)
    except (OSError, ValueError):
        pass
    finally:
        _drop_newfile(project_dir, session_id, file_path)


def _insert_created_before_updated(raw_fm: str, value: str) -> str:
    """Insert ``created: <value>`` into a YAML frontmatter block.

    Position rule: immediately before the ``updated:`` line if present,
    else appended at the end. Indentation matches the ``updated:`` line
    when inserting before it (frontmatter is canonically left-aligned,
    but the matching keeps the rule minimal). When ``created:`` already
    exists in the block, this function rewrites the existing line in
    place via ``rewrite_frontmatter_scalar`` semantics — but the caller
    is expected to gate on absence so this branch is dead in practice.
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


def _run_status_change_cascade(
    a4_dir: Path, file_path: str, project_dir: str, session_id: str
) -> None:
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
    """
    pre_map = _read_prestatus(project_dir, session_id)
    pre_status = pre_map.get(file_path)
    if pre_status is None:
        return

    abs_path = Path(file_path)
    post_status = _read_status_from_disk(abs_path)

    # Drop the entry regardless of outcome — the next edit's PreToolUse
    # will repopulate from disk, so we never act on a stale pre.
    pre_map.pop(file_path, None)
    _write_prestatus(project_dir, session_id, pre_map)

    if post_status is None or post_status == pre_status:
        return

    try:
        rel_path = str(abs_path.resolve().relative_to(a4_dir.resolve()))
    except (OSError, ValueError):
        return

    try:
        from common import now_kst

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
            f"a4_hook.py post-edit: failed to import cascade modules ({e}) "
            "— skipping cascade\n"
        )
        return

    family = detect_family(rel_path)
    if family is None or family not in FAMILY_TRANSITIONS:
        return
    if not is_transition_legal(family, pre_status, post_status):
        # Illegal direct edit — Stop hook will surface it. Don't cascade
        # off an illegal transition.
        return

    today = now_kst()
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
    try:
        apply_status_change(
            abs_path, pre_status, post_status, "direct edit",
            dry_run=False, today=today,
        )
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
                f"a4_hook.py post-edit: cascade error ({e})\n"
            )
            return

    if not report.cascades and not report.errors:
        return

    _emit_cascade_context(report, file_path, project_dir)


def _emit_cascade_context(report, file_path: str, project_dir: str) -> None:
    """Surface cascade results as additionalContext + systemMessage.

    Per `dev/hook-conventions.md` §6: "both channels together" when a
    hook affects workspace state the user should be aware of — cascades
    rewrite related files, so a short systemMessage summary plus a
    per-file additionalContext detail is the right shape.
    """
    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + "/")
        else file_path
    )
    n = len(report.cascades)
    summary = (
        f"a4 cascade: {report.primary.from_status} → "
        f"{report.primary.to_status} on {display_rel} "
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
        f"`{display_rel}` transitioned "
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
    _emit(payload)


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
        "- `brainstorm.status = promoted` iff own `promoted:` list is "
        "non-empty."
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
        from markdown_validator import frontmatter as vfm
        from markdown_validator import transitions as vtr
        from markdown import extract_preamble
    except ImportError as e:
        sys.stderr.write(
            f"a4_hook.py stop: failed to import validators ({e}) — skipping validation\n"
        )
        return 0

    fm_violations: list = []
    tr_violations: list = []

    try:
        from markdown_validator.refs import RefIndex

        index = RefIndex(a4_dir)
        edited_rel = {str(Path(f).resolve().relative_to(a4_dir.resolve())) for f in edited}
        for f in edited:
            path = Path(f)
            preamble = extract_preamble(path)
            if preamble.fm is None:
                missing = vfm.check_missing_frontmatter(path, a4_dir)
                if missing is not None:
                    fm_violations.append(missing)
            else:
                fm_violations.extend(vfm.validate_file(path, a4_dir, preamble.fm, index))
        for v in vfm.validate_id_uniqueness(a4_dir):
            if v.path in edited_rel:
                fm_violations.append(v)
        tr_violations = vtr.check_files(a4_dir, [Path(f) for f in edited])
    except Exception as e:
        sys.stderr.write(
            f"a4_hook.py stop: validator error ({e}) — skipping validation\n"
        )
        return 0

    if not fm_violations and not tr_violations:
        _unlink_silent(record_file)
        return 0

    out_lines = ["a4/ validators found issues in files edited this session:"]
    if fm_violations:
        fm_file_count = len({v.path for v in fm_violations})
        out_lines.append("")
        out_lines.append("--- markdown_validator.frontmatter ---")
        out_lines.append(
            f"{len(fm_violations)} violation(s) across {fm_file_count} file(s):"
        )
        for v in fm_violations:
            loc = v.path + (f" [{v.field}]" if v.field else "")
            out_lines.append(f"  {loc} ({v.rule}): {v.message}")
    if tr_violations:
        tr_file_count = len({v.path for v in tr_violations})
        out_lines.append("")
        out_lines.append("--- markdown_validator.transitions ---")
        out_lines.append(
            f"{len(tr_violations)} violation(s) across {tr_file_count} file(s):"
        )
        for v in tr_violations:
            loc = v.path + (f" [{v.field}]" if v.field else "")
            out_lines.append(f"  {loc} ({v.rule}): {v.message}")
        out_lines.append(
            "Edit `status:` directly — the PostToolUse cascade hook handles "
            "related-file flips and `updated:` refresh. Direct edits are "
            "allowed only when the transition is in FAMILY_TRANSITIONS "
            "(status_model.py); illegal jumps land here."
        )
    out_lines.append("")
    out_lines.append(
        "Fix the issues above before stopping. Each violation message "
        "names the file, field, and rule; consult "
        "`plugins/a4/authoring/frontmatter-common.md` (universal "
        "contract) and the matching "
        "`plugins/a4/authoring/<type>-authoring.md` (per-type field "
        "table and lifecycle) for the binding shape."
    )
    sys.stderr.write("\n".join(out_lines) + "\n")
    return 2


def _unlink_silent(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# -------------------------- user-prompt (UserPromptSubmit) ----------------


_MAX_IDS = 20
_LOOKUP_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "bug",
    "spike",
    "research",
    "review",
    "spec",
    "idea",
)


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
            matches.extend(str(p) for p in sorted(sub.glob(pattern)))
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


# ------------------------- session-start (SessionStart) -------------------


def _session_start() -> int:
    """Inject the canonical type → file-location map for `a4/` plus the
    `allocate_id.py` invocation as `additionalContext`.

    Surfaces the layout (issue families as flat `a4/<type>/<id>-<slug>.md`;
    wiki pages as top-level `a4/<type>.md`) so the LLM places new files
    correctly, and the runnable allocator command so it can claim a
    workspace-global monotonic id without searching for it — both before
    the first Write/Edit triggers PreToolUse contract-injection. Built
    from `common.WIKI_TYPES` and `common.ISSUE_FOLDERS` so adding a new
    type does not require touching this function.

    Silent when the project has no `a4/` directory (non-a4 projects get
    no SessionStart noise). Always exits 0.
    """
    import os

    # Drain stdin defensively. Claude Code pipes a JSON payload to
    # SessionStart hooks; we read no fields, but a closed pipe on an
    # unread parent stdin can block.
    try:
        sys.stdin.read()
    except OSError:
        pass

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    try:
        from common import ISSUE_FOLDERS, WIKI_TYPES
    except ImportError:
        return 0

    issue_lines = [
        f"- `{t}` → `a4/{t}/<id>-<slug>.md`" for t in ISSUE_FOLDERS
    ]
    wiki_lines = [f"- `{t}` → `a4/{t}.md`" for t in sorted(WIKI_TYPES)]

    context = (
        "## a4/ workspace — type → file location\n\n"
        "**Issue families** (one file per id, flat folder):\n\n"
        + "\n".join(issue_lines)
        + "\n\n**Wiki pages** (single top-level file per type):\n\n"
        + "\n".join(wiki_lines)
        + "\n\n**Allocate id** (issue files only; never invent or reuse):\n\n"
        "```bash\n"
        'uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" <a4-dir>\n'
        "```"
    )
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
    return 0


# -------------------------- shared helpers --------------------------------


def _emit(payload: dict) -> None:
    import json

    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
