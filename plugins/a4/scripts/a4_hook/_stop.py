"""Stop subcommand: validate session-edited a4/*.md files.

Runs the frontmatter schema check + the transition-legality safety net
(HEAD-vs-working-tree git diff against `FAMILY_TRANSITIONS`) on every
file recorded in this session. On violations, emits a JSON
``{"decision": "block", "reason": ...}`` payload on stdout (rc=0) so
Claude Code surfaces the message without the ``[command]: `` harness
prefix that wraps stderr-on-rc=2 output, and forces Claude retry.
rc=0 on clean or any internal failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    project_dir_from_payload,
    record_dir,
    trace,
    unlink_silent,
)


def stop() -> int:
    """Stop entry point. Always exits 0; uses JSON-on-stdout to block."""
    import json
    import os

    raw = sys.stdin.read()
    if not raw:
        trace(project_dir_from_payload({}), None, "stop", "abort", reason="no_payload")
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        trace(project_dir_from_payload({}), None, "stop", "abort", reason="bad_json")
        return 0

    session_id = payload.get("session_id") or ""
    if not session_id or payload.get("stop_hook_active") is True:
        trace(
            project_dir_from_payload(payload),
            session_id or None,
            "stop",
            "abort",
            reason=(
                "stop_hook_active"
                if payload.get("stop_hook_active") is True
                else "no_session_id"
            ),
        )
        return 0

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        trace(None, session_id, "stop", "abort", reason="no_project_dir")
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        trace(project_dir, session_id, "stop", "abort", reason="no_a4_dir")
        return 0
    record_file = record_dir(project_dir) / f"a4-edited-{session_id}.txt"
    if not record_file.is_file():
        trace(
            project_dir,
            session_id,
            "stop",
            "noop",
            reason="no_record_file",
            record_file=str(record_file),
        )
        return 0

    try:
        raw_paths = record_file.read_text().splitlines()
    except OSError:
        trace(
            project_dir,
            session_id,
            "stop",
            "abort",
            reason="record_read_failed",
            record_file=str(record_file),
        )
        return 0

    a4_prefix = str(a4_dir) + os.sep
    edited = sorted(
        {p for p in raw_paths if p and p.startswith(a4_prefix) and Path(p).is_file()}
    )
    if not edited:
        unlink_silent(record_file)
        trace(
            project_dir,
            session_id,
            "stop",
            "noop",
            reason="no_existing_a4_edits",
            raw_count=len(raw_paths),
        )
        return 0

    try:
        from markdown_validator import frontmatter as vfm
        from markdown_validator import transitions as vtr
        from markdown import extract_preamble
    except ImportError as e:
        sys.stderr.write(
            f"a4_hook stop: failed to import validators ({e}) — skipping validation\n"
        )
        trace(
            project_dir,
            session_id,
            "stop",
            "abort",
            reason="import_validators_failed",
            error=str(e),
        )
        return 0

    fm_violations: list = []
    tr_violations: list = []
    fm_by_rel: dict[str, dict | None] = {}

    try:
        from markdown_validator.refs import RefIndex

        index = RefIndex(a4_dir)
        edited_rel = {str(Path(f).resolve().relative_to(a4_dir.resolve())) for f in edited}
        for f in edited:
            path = Path(f)
            preamble = extract_preamble(path)
            rel_str = str(path.resolve().relative_to(a4_dir.resolve()))
            fm_by_rel[rel_str] = preamble.fm
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
            f"a4_hook stop: validator error ({e}) — skipping validation\n"
        )
        trace(
            project_dir,
            session_id,
            "stop",
            "abort",
            reason="validator_error",
            error=str(e),
        )
        return 0

    if not fm_violations and not tr_violations:
        unlink_silent(record_file)
        trace(project_dir, session_id, "stop", "clean", edited=edited)
        return 0

    sys.stdout.write(
        json.dumps(
            {
                "decision": "block",
                "reason": _format_block_reason(
                    fm_violations, tr_violations, fm_by_rel, vfm
                ),
            }
        )
    )
    trace(
        project_dir,
        session_id,
        "stop",
        "block",
        edited=edited,
        frontmatter_violations=len(fm_violations),
        transition_violations=len(tr_violations),
    )
    return 0


_STATUS_VALUE_ORDER: dict[str, tuple[str, ...]] = {
    "usecase": (
        "draft",
        "ready",
        "implementing",
        "revising",
        "shipped",
        "superseded",
        "discarded",
        "blocked",
    ),
    "task": ("open", "queued", "progress", "holding", "done", "failing", "discarded"),
    "bug": ("open", "queued", "progress", "holding", "done", "failing", "discarded"),
    "spike": ("open", "queued", "progress", "holding", "done", "failing", "discarded"),
    "research": (
        "open",
        "queued",
        "progress",
        "holding",
        "done",
        "failing",
        "discarded",
    ),
    "review": ("open", "in-progress", "resolved", "discarded"),
    "spec": ("draft", "active", "deprecated", "superseded"),
    "idea": ("open", "promoted", "discarded"),
    "brainstorm": ("open", "promoted", "discarded"),
    "epic": ("open", "done", "discarded"),
}

_FIELD_VALUE_ORDER: dict[str, tuple[str, ...]] = {
    "mode": ("comparative", "single"),
    "priority": ("high", "medium", "low"),
    "kind": ("finding", "gap", "question"),
}


def _format_block_reason(
    fm_violations: list,
    tr_violations: list,
    fm_by_rel: dict[str, dict | None],
    vfm_module,
) -> str:
    """Render a concise, fix-oriented Stop block reason.

    The stop hook is the agent's retry prompt. Keep it short enough to read,
    but list every violation so the agent can fix all edited files in one pass.
    """

    lines = ["a4 validation failed.", ""]
    for v in fm_violations:
        lines.append(
            f"  - {_format_location(v.path, v.field)}: "
            f"{_compact_frontmatter_message(v, fm_by_rel, vfm_module)}"
        )
    for v in tr_violations:
        lines.append(
            f"  - {_format_location(v.path, v.field)}: "
            f"{_compact_transition_message(v)}"
        )
    return "\n".join(lines)


def _format_location(path: str, field: str | None) -> str:
    return path + (f" [{field}]" if field else "")


def _compact_frontmatter_message(v, fm_by_rel: dict[str, dict | None], vfm_module) -> str:
    if v.rule == "enum-violation" and v.field:
        value = _frontmatter_value(v.path, v.field, fm_by_rel)
        allowed = _allowed_enum_values(v, fm_by_rel, vfm_module)
        if allowed:
            return f"invalid {_format_value(value)}. Valid: {_format_values(allowed)}"

    if v.rule == "type-filename-mismatch" and v.field == "type":
        value = _frontmatter_value(v.path, v.field, fm_by_rel)
        return f"invalid {_format_value(value)}. Valid: {Path(v.path).stem}"

    if v.rule == "missing-required":
        return "missing or empty"

    if v.rule == "missing-frontmatter":
        return "missing frontmatter"

    return _strip_field_prefix(v.message, v.field)


def _compact_transition_message(v) -> str:
    import re

    from status_model import legal_targets_from

    match = re.search(r"transition '([^']+)' → '([^']+)' not allowed", v.message)
    if not match:
        return _strip_field_prefix(v.message, v.field)

    old_status, new_status = match.groups()
    family = Path(v.path).parts[0] if Path(v.path).parts else ""
    allowed = legal_targets_from(family, old_status)
    if allowed:
        return (
            f"illegal transition '{old_status}' → '{new_status}'. "
            f"Valid from '{old_status}': "
            f"{_format_values(_ordered_values(allowed, field='status', family=family))}"
        )
    return (
        f"illegal transition '{old_status}' → '{new_status}'. "
        f"'{old_status}' has no valid next statuses."
    )


_MISSING = object()


def _frontmatter_value(path: str, field: str, fm_by_rel: dict[str, dict | None]):
    fm = fm_by_rel.get(path)
    if isinstance(fm, dict):
        return fm.get(field, _MISSING)
    return _MISSING


def _allowed_enum_values(
    v,
    fm_by_rel: dict[str, dict | None],
    vfm_module,
) -> tuple[str, ...]:
    fm = fm_by_rel.get(v.path)
    ftype = None
    if isinstance(fm, dict):
        ftype = vfm_module.detect_type(Path(v.path), fm)
    if ftype is None:
        parts = Path(v.path).parts
        if len(parts) >= 2 and parts[0] in vfm_module.SCHEMAS:
            ftype = parts[0]
        elif Path(v.path).stem in getattr(vfm_module, "WIKI_TYPES", frozenset()):
            ftype = "wiki"
    if ftype is None:
        return ()

    schema = vfm_module.SCHEMAS.get(ftype)
    if schema is None or v.field not in schema.enums:
        return ()
    return _ordered_values(schema.enums[v.field], field=v.field, family=ftype)


def _ordered_values(
    values,
    *,
    field: str | None = None,
    family: str | None = None,
) -> tuple[str, ...]:
    value_set = set(values)
    if field == "status" and family in _STATUS_VALUE_ORDER:
        return tuple(v for v in _STATUS_VALUE_ORDER[family] if v in value_set)
    if field in _FIELD_VALUE_ORDER:
        return tuple(v for v in _FIELD_VALUE_ORDER[field] if v in value_set)
    return tuple(sorted(value_set))


def _format_values(values) -> str:
    return ", ".join(values)


def _format_value(value) -> str:
    if value is _MISSING:
        return "<missing>"
    if isinstance(value, str):
        return f"'{value}'"
    return repr(value)


def _strip_field_prefix(message: str, field: str | None) -> str:
    if not field:
        return message
    for prefix in (f"`{field}` ", f"{field}: ", f"`{field}:` "):
        if message.startswith(prefix):
            return message.removeprefix(prefix)
    return message
