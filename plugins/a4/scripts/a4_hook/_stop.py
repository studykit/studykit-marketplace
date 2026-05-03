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
    AUTHORING_DIR,
    project_dir_from_payload,
    record_dir,
    unlink_silent,
)


def stop() -> int:
    """Stop entry point. Always exits 0; uses JSON-on-stdout to block."""
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

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0
    record_file = record_dir(project_dir) / f"a4-edited-{session_id}.txt"
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
        unlink_silent(record_file)
        return 0

    try:
        from markdown_validator import frontmatter as vfm
        from markdown_validator import transitions as vtr
        from markdown import extract_preamble
    except ImportError as e:
        sys.stderr.write(
            f"a4_hook stop: failed to import validators ({e}) — skipping validation\n"
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
            f"a4_hook stop: validator error ({e}) — skipping validation\n"
        )
        return 0

    if not fm_violations and not tr_violations:
        unlink_silent(record_file)
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
        f"`{AUTHORING_DIR}/frontmatter-common.md` (universal "
        "contract) and the matching "
        f"`{AUTHORING_DIR}/<type>-authoring.md` (per-type field "
        "table and lifecycle) for the binding shape."
    )
    sys.stdout.write(
        json.dumps({"decision": "block", "reason": "\n".join(out_lines)})
    )
    return 0
