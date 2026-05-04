"""PreToolUse subcommand: pre-status snapshot + authoring-contract injection.

Two responsibilities on the same a4/*.md gate:

1. Stash the on-disk ``status:`` of the file the tool is about to write.
   Consumed by ``post-edit`` to detect ``status:`` transitions precisely
   (pre vs post on disk, instead of HEAD vs working tree).
2. Inject the type-specific authoring-contract pointers as
   ``additionalContext`` once per type per session, for both existing-file
   edits and new-file Writes (issue creation), when the runtime supports
   PreToolUse context injection. Sole mechanism for surfacing authoring
   contracts at edit time in Claude Code.

Authoring-contract injection notes:

- Lazy, edit-intent-only — fires from PreToolUse so a pure read of an
  `a4/*.md` file does NOT pull in the contract; only an imminent
  Write/Edit/MultiEdit does. Codex apply_patch payloads still record
  pre-edit state, but suppress this context because Codex PreToolUse does
  not inject `additionalContext` into the model.
- Type resolution is by path (`common.WIKI_TYPES` / `common.ISSUE_FOLDERS`),
  not by frontmatter parse — the a4 layout pins type by location, so an
  extra file IO is unnecessary. Archive files are skipped.
- Deduped per type per session — once the LLM has seen the umbrella/task/...
  contract this session, editing another file of the same type re-emits
  nothing.
- Session-scoped state at `.claude/tmp/a4-edited/a4-injected-<sid>.txt`,
  one `<type>` per line. Cleaned up by the same SessionEnd / SessionStart-sweep
  paths that handle the other a4-edited family files.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    AUTHORING_DIR,
    display_rel,
    emit,
    project_dir_from_payload,
    read_injected,
    read_prestatus,
    read_status_from_disk,
    record_injected,
    record_newfile,
    resolve_type_from_path,
    trace,
    write_prestatus,
)
from a4_hook._runtime import select_hook_strategy


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
        "ci",
        "context",
        "domain",
        "nfr",
    }
)


def pre_edit() -> int:
    """PreToolUse entry point. Always exits 0."""
    import json
    import os

    raw = sys.stdin.read()
    if not raw:
        trace(project_dir_from_payload({}), None, "pre-edit", "abort", reason="no_payload")
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        trace(project_dir_from_payload({}), None, "pre-edit", "abort", reason="bad_json")
        return 0

    session_id = payload.get("session_id") or ""
    if not session_id:
        trace(
            project_dir_from_payload(payload),
            None,
            "pre-edit",
            "abort",
            reason="no_session_id",
            tool_name=payload.get("tool_name"),
        )
        return 0

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        trace(None, session_id, "pre-edit", "abort", reason="no_project_dir")
        return 0
    a4_dir = Path(project_dir) / "a4"
    a4_prefix = str(a4_dir) + os.sep

    strategy = select_hook_strategy(payload)
    targets = strategy.edit_targets(payload, project_dir)
    if not targets:
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "abort",
            reason="no_targets",
            runtime=strategy.name,
            tool_name=payload.get("tool_name"),
        )
        return 0

    # Codex currently parses PreToolUse `additionalContext` but does not inject
    # it into the model. Emitting the Claude-style authoring-contract context
    # from a Codex PreToolUse hook would therefore become invalid hook output.
    # Keep the stateful pre-edit work, but suppress context for Codex payloads.
    suppress_context = strategy.suppress_pretooluse_context
    trace(
        project_dir,
        session_id,
        "pre-edit",
        "targets",
        runtime=strategy.name,
        suppress_context=suppress_context,
        count=len(targets),
        paths=[t.path for t in targets],
    )

    for target in targets:
        _pre_edit_one(
            payload,
            target.path,
            a4_dir,
            a4_prefix,
            project_dir,
            session_id,
            target.is_new_file_intent,
            suppress_context,
        )
    return 0


def _pre_edit_one(
    payload: dict,
    file_path: str,
    a4_dir: Path,
    a4_prefix: str,
    project_dir: str,
    session_id: str,
    is_new_file_intent: bool,
    suppress_context: bool,
) -> None:
    if not file_path.startswith(a4_prefix):
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip",
            reason="outside_a4",
            file_path=file_path,
            a4_dir=str(a4_dir),
        )
        return

    abs_path = Path(file_path)

    # Responsibility 1 — pre-status snapshot for cascade detection.
    # Only meaningful when the file already exists; new-file Writes have
    # no prior `status:` and post-edit treats absence as "no transition".
    if abs_path.is_file():
        pre = read_status_from_disk(abs_path)
        if pre is not None:
            data = read_prestatus(project_dir, session_id)
            data[file_path] = pre
            write_prestatus(project_dir, session_id, data)
            trace(
                project_dir,
                session_id,
                "pre-edit",
                "record_prestatus",
                file_path=file_path,
                status=pre,
            )
        else:
            trace(
                project_dir,
                session_id,
                "pre-edit",
                "skip_prestatus",
                reason="no_status",
                file_path=file_path,
            )
    else:
        # File doesn't exist yet — record so post-edit can stamp
        # `created:` after the Write lands (overwriting any value the
        # LLM pre-populated; `created:` is hook-owned). Only Write can
        # create files in Claude Code's tool model; Edit/MultiEdit
        # require a prior Read of an existing file.
        if is_new_file_intent or payload.get("tool_name") == "Write":
            record_newfile(project_dir, session_id, file_path)
            trace(
                project_dir,
                session_id,
                "pre-edit",
                "record_newfile",
                file_path=file_path,
            )
        else:
            trace(
                project_dir,
                session_id,
                "pre-edit",
                "skip_newfile",
                reason="not_create_intent",
                file_path=file_path,
            )

    # Responsibility 2 — authoring-contract injection (one-shot per
    # (file, type) per session). Fires for both edits and new-file
    # Writes — type is resolved from path (`a4/<folder>/...`), which
    # works without on-disk frontmatter, so issue creation gets the
    # binding contract before authoring. Dedupe still suppresses repeat
    # injections on subsequent edits to the same file.
    if not suppress_context:
        _maybe_inject_authoring_contract(
            abs_path, file_path, a4_dir, project_dir, session_id
        )
    else:
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip_contract_context",
            reason="runtime_suppresses_pretooluse_context",
            file_path=file_path,
        )


def _maybe_inject_authoring_contract(
    abs_path: Path,
    file_path: str,
    a4_dir: Path,
    project_dir: str,
    session_id: str,
) -> None:
    """Inject pointer-style authoring-contract context once per type
    per session. Silent when the type cannot be resolved from path
    (archive files, unrecognized layout).
    """
    type_value = resolve_type_from_path(abs_path, a4_dir)
    if not type_value:
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip_contract_context",
            reason="unknown_type",
            file_path=file_path,
        )
        return

    type_doc = AUTHORING_DIR / f"{type_value}-authoring.md"
    if not type_doc.is_file():
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip_contract_context",
            reason="missing_type_doc",
            file_path=file_path,
            type=type_value,
        )
        return

    already = read_injected(project_dir, session_id)
    if type_value in already:
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip_contract_context",
            reason="already_injected",
            file_path=file_path,
            type=type_value,
        )
        return
    record_injected(project_dir, session_id, type_value)
    trace(
        project_dir,
        session_id,
        "pre-edit",
        "inject_contract_context",
        file_path=file_path,
        type=type_value,
    )

    rel = display_rel(file_path, project_dir)

    pointers = [
        f"- `{AUTHORING_DIR}/frontmatter-common.md` — cross-cutting "
        "frontmatter rules (`type:`, path references, empty collections, "
        "unknown fields, `created` / `updated`).",
    ]
    if type_value in _ISSUE_BODY_TYPES:
        pointers.append(
            f"- `{AUTHORING_DIR}/frontmatter-issue.md` — issue-side "
            "rules (`id`, title placeholders, relationships, status "
            "changes and cascades, structural relationship fields)."
        )
    else:
        pointers.append(
            f"- `{AUTHORING_DIR}/frontmatter-wiki.md` — wiki minimal "
            "frontmatter contract."
        )
    pointers.extend([
        f"- `{AUTHORING_DIR}/{type_value}-authoring.md` — per-type "
        "field table, lifecycle, body shape, common mistakes.",
        f"- `{AUTHORING_DIR}/body-conventions.md` — cross-cutting "
        "body conventions (heading form, link form).",
    ])
    if type_value in _ISSUE_BODY_TYPES:
        pointers.append(
            f"- `{AUTHORING_DIR}/issue-body.md` — `## Resume` "
            "(current-state snapshot) and `## Log` (narrative-worthy "
            "events) for issue files."
        )
    if type_value in _WIKI_BODY_TYPES:
        pointers.append(
            f"- `{AUTHORING_DIR}/wiki-body.md` — `## Change Logs` "
            "audit trail and Wiki Update Protocol."
        )
    if type_value in _TASK_FAMILY_TYPES:
        pointers.insert(
            2,
            f"- `{AUTHORING_DIR}/issue-family-lifecycle.md` — "
            "issue-family lifecycle (status enum, transitions, writer "
            "rules).",
        )

    body = "\n".join(pointers)
    context = (
        f"## a4 authoring contract — `type: {type_value}`\n\n"
        f"About to edit `{rel}`. Read these contracts before "
        "writing — they are the binding schema/body contract for this "
        "type, not optional.\n\n"
        f"{body}\n\n"
        f"Injected once per `type: {type_value}` per session — subsequent "
        "edits to any file of this type will not re-emit this notice."
    )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }
    )
