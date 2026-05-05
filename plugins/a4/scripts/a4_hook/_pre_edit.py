"""PreToolUse subcommand: pre-status snapshot.

Stashes the on-disk ``status:`` of the a4 file the tool is about to
write. ``post-edit`` consumes this snapshot to detect ``status:``
transitions precisely (pre vs post on disk, instead of HEAD vs working
tree) and run any required cascade.

Authoring entrypoints are intentionally emitted by ``session-start`` for
all runtimes. ``pre-edit`` no longer emits authoring guidance; it remains
focused on status-transition bookkeeping.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    project_dir_from_payload,
    read_prestatus,
    read_status_from_disk,
    trace,
    write_prestatus,
)
from a4_hook._runtime import select_hook_strategy


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

    trace(
        project_dir,
        session_id,
        "pre-edit",
        "targets",
        runtime=strategy.name,
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

    # Pre-status snapshot for cascade detection.
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
    elif not (is_new_file_intent or payload.get("tool_name") == "Write"):
        trace(
            project_dir,
            session_id,
            "pre-edit",
            "skip_newfile",
            reason="not_create_intent",
            file_path=file_path,
        )
