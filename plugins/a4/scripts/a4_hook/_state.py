"""Shared state, helpers, and session-scoped record IO for a4 hook subcommands.

All session-state lives under ``<project>/.claude/tmp/a4-edited/``:

- ``a4-edited-<sid>.txt``        — paths edited this session (PostToolUse → Stop).
- ``a4-prestatus-<sid>.json``    — pre-edit ``status:`` snapshot (Pre → Post).
- ``a4-resolved-ids-<sid>.txt``  — `#<id>` tokens already resolved this session
                                   (UserPromptSubmit dedupe).
- ``trace.log``                  — opt-in JSON Lines trace, written only when
                                   ``A4_HOOK_TRACE`` is truthy.

All cleanup runs at SessionEnd (`hooks/cleanup-edited-a4.sh`) with a
SessionStart safety-net sweep in the Python dispatcher for crashed sessions,
per `dev/hook-conventions.md` §2 Rule A.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._runtime import project_root_from_payload

# Plugin-internal anchor path. Resolved once at import time so subcommands can
# render fully-qualified absolute pointers without recomputing the plugin root.
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent

TRACE_ENV_VAR = "A4_HOOK_TRACE"
TRACE_FILE_NAME = "trace.log"
TRACE_TRUTHY = {"1", "true", "yes", "on"}


# ----------------------------- generic helpers ----------------------------


def record_dir(project_dir: str) -> Path:
    """Session-scoped state directory shared by all a4-edited family files."""
    return Path(project_dir) / ".claude" / "tmp" / "a4-edited"


def trace_enabled() -> bool:
    """Return true when opt-in hook tracing is enabled.

    Tracing is intentionally file-only and off by default. Enable it by
    launching the host with ``A4_HOOK_TRACE=1`` (also accepts
    ``true``/``yes``/``on``, case-insensitive).
    """
    import os

    return os.environ.get(TRACE_ENV_VAR, "").strip().lower() in TRACE_TRUTHY


def trace_file(project_dir: str | Path) -> Path:
    return record_dir(str(project_dir)) / TRACE_FILE_NAME


def trace(
    project_dir: str | Path | None,
    session_id: str | None,
    subcommand: str,
    event: str,
    **fields,
) -> None:
    """Append one JSON Lines trace record.

    This helper never writes stdout/stderr and never raises. It exists to
    diagnose early-return paths such as "payload had no targets", "target was
    outside root ``a4/``", or "project has no ``a4/`` directory" without
    breaking hook JSON output.
    """
    if not trace_enabled() or project_dir is None:
        return
    try:
        import json
        from datetime import datetime

        path = trace_file(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now().isoformat(timespec="microseconds"),
            "sid": session_id,
            "cmd": subcommand,
            "event": event,
        }
        record.update(fields)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except OSError:
        return


def display_rel(file_path: str, project_dir: str) -> str:
    """Render `file_path` as project-dir-relative for human-readable
    `additionalContext` / `systemMessage` output. Falls back to the
    original (absolute) path when the file is outside project_dir.
    """
    prefix = project_dir + "/"
    return file_path[len(prefix):] if file_path.startswith(prefix) else file_path


def project_dir_from_payload(payload: dict) -> str:
    """Resolve the active project directory for Claude Code and Codex hooks.

    Runtime-specific source variables and cwd fallback behavior are declared in
    ``a4_hook._runtime``. The return value is a normalized absolute path string
    or ``""`` when no usable cwd can be found.
    """
    return project_root_from_payload(payload)


def emit(payload: dict) -> None:
    import json

    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def unlink_silent(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def read_status_from_disk(path: Path) -> str | None:
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


# ----------------------------- prestatus IO -------------------------------


def prestatus_file(project_dir: str, session_id: str) -> Path:
    return record_dir(project_dir) / f"a4-prestatus-{session_id}.json"


def read_prestatus(project_dir: str, session_id: str) -> dict:
    import json

    path = prestatus_file(project_dir, session_id)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_prestatus(project_dir: str, session_id: str, data: dict) -> None:
    import json

    path = prestatus_file(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        return


# ----------------------------- resolved-ids IO ----------------------------


def resolved_ids_path(project_dir: str, session_id: str) -> Path:
    return record_dir(project_dir) / f"a4-resolved-ids-{session_id}.txt"


def read_resolved_ids(project_dir: str, session_id: str) -> set[str]:
    path = resolved_ids_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        return {line.strip() for line in path.read_text().splitlines() if line.strip()}
    except OSError:
        return set()


def record_resolved_ids(
    project_dir: str, session_id: str, tokens: list[str]
) -> None:
    if not tokens:
        return
    path = resolved_ids_path(project_dir, session_id)
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


# ----------------------------- edited IO ----------------------------------


def record_edited(project_dir: str, session_id: str, file_path: str) -> None:
    rd = record_dir(project_dir)
    try:
        rd.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    record_file = rd / f"a4-edited-{session_id}.txt"
    try:
        with record_file.open("a") as f:
            f.write(file_path + "\n")
    except OSError:
        return
