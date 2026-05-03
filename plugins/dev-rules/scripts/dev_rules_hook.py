#!/usr/bin/env python3
"""dev-rules hook dispatcher.

Subcommands
-----------
- pre-edit       PreToolUse on Write|Edit|MultiEdit. Resolves the target file's
                 language from its extension, then injects **pointer paths** to
                 matching ruleset files as `additionalContext` with an
                 imperative directive ("Read these — binding, not optional").
                 The model performs the Read itself, so ruleset bodies enter
                 the transcript as the model's own tool-result rather than as
                 system-injected text — higher attention weight, and the rules
                 stay live across subsequent edits via the cached Read result.
                 Rulesets are organized by category: each subdirectory under
                 `rulesets/` is one category (e.g. `rulesets/logging/`), and
                 within each category the same `general.md` + `<language>.md`
                 pattern is used. Per-session dedup ensures each
                 `<category>:<key>` pointer is emitted at most once per
                 session. `general` is announced on the first code edit of any
                 language; `<language>` on the first edit of a file in that
                 language. All categories that ship a matching file are
                 announced together on the same edit.
- session-end    SessionEnd. Deletes this session's dedup state file under
                 `.claude/tmp/dev-rules/`.
- session-start  SessionStart. Sweeps orphan dedup state files older than 1
                 day (covers crashed sessions where session-end never fired)
                 and truncates the trace log if its mtime is older than 1 day.

Design constraints (mirrors `plugins/a4/dev/hook-conventions.md`):
- Always exits 0; never blocks an edit, session start, or session end.
- Internal failures (missing env, IO errors, malformed JSON) are silent.
- Silent on dedup hit (no heartbeat, no "ran successfully" line).
- Dedup state is session-scoped under `.claude/tmp/dev-rules/`.

Debug tracing
-------------
Every decision point calls `_trace(...)` which, **when tracing is enabled**,
appends a JSON Lines record to `.claude/tmp/dev-rules/trace.log` under the
project root. Tracing is OFF by default and is enabled only when the
environment variable `DEV_RULES_TRACE` is set to a truthy value (`1`, `true`,
`yes`, `on`, case-insensitive). Trace output never goes to stdout / stderr —
it is file-only so it does not consume LLM context.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".jsx": "javascript",
    ".tsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
}

LANGUAGE_DISPLAY: dict[str, str] = {
    "python": "Python",
    "javascript": "JavaScript",
    "java": "Java",
    "kotlin": "Kotlin",
}

STATE_DIR_REL = ".claude/tmp/dev-rules"
STATE_FILE_PREFIX = "injected-"
STATE_FILE_SUFFIX = ".txt"
TRACE_FILE_NAME = "trace.log"
TRACE_ENV_VAR = "DEV_RULES_TRACE"
TRACE_TRUTHY = {"1", "true", "yes", "on"}
ORPHAN_MAX_AGE_SECONDS = 24 * 60 * 60


def _trace_enabled() -> bool:
    value = os.environ.get(TRACE_ENV_VAR, "").strip().lower()
    return value in TRACE_TRUTHY


def _project_dir() -> Path | None:
    value = os.environ.get("CLAUDE_PROJECT_DIR")
    if not value:
        return None
    return Path(value)


def _plugin_root() -> Path | None:
    value = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not value:
        return None
    return Path(value)


def _state_dir(project_dir: Path) -> Path:
    return project_dir / STATE_DIR_REL


def _state_file(project_dir: Path, session_id: str) -> Path:
    return _state_dir(project_dir) / f"{STATE_FILE_PREFIX}{session_id}{STATE_FILE_SUFFIX}"


def _trace_file(project_dir: Path) -> Path:
    return _state_dir(project_dir) / TRACE_FILE_NAME


def _trace(
    project_dir: Path | None,
    session_id: str | None,
    subcommand: str,
    event: str,
    **fields: Any,
) -> None:
    """Append one JSON Lines record to the trace log. File-only; never stdout.

    No-op unless the environment variable named by `TRACE_ENV_VAR` is truthy.
    """
    if not _trace_enabled():
        return
    if project_dir is None:
        return
    try:
        path = _trace_file(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now().isoformat(timespec="microseconds"),
            "sid": session_id,
            "cmd": subcommand,
            "event": event,
        }
        record.update(fields)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _read_injected(state_file: Path) -> set[str]:
    if not state_file.is_file():
        return set()
    try:
        return {
            line.strip()
            for line in state_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()


def _record_injected(state_file: Path, keys: list[str]) -> None:
    if not keys:
        return
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file.open("a", encoding="utf-8") as f:
            for key in keys:
                f.write(f"{key}\n")
    except OSError:
        pass


def _collect_rulesets(plugin_root: Path, key: str) -> list[str]:
    """Scan every category subdirectory under `rulesets/` for `<key>.md`.

    Returns a list of category names (deterministic, sorted) for which a
    matching ruleset file exists. The body is **not** read — pre-edit emits
    pointer paths and lets the model Read the bodies itself.
    """
    rulesets_dir = plugin_root / "rulesets"
    if not rulesets_dir.is_dir():
        return []
    try:
        entries = sorted(rulesets_dir.iterdir(), key=lambda p: p.name)
    except OSError:
        return []
    results: list[str] = []
    for category_dir in entries:
        if not category_dir.is_dir():
            continue
        path = category_dir / f"{key}.md"
        if not path.is_file():
            continue
        results.append(category_dir.name)
    return results


def _read_payload() -> dict | None:
    try:
        raw = sys.stdin.read()
    except OSError:
        return None
    if not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def pre_edit() -> int:
    project_dir = _project_dir()
    payload = _read_payload()
    if payload is None:
        _trace(project_dir, None, "pre-edit", "abort", reason="no_payload")
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    session_id_raw = payload.get("session_id")
    session_id = session_id_raw if isinstance(session_id_raw, str) and session_id_raw else None

    if not isinstance(file_path, str) or not file_path:
        _trace(project_dir, session_id, "pre-edit", "abort", reason="no_file_path")
        return 0

    if session_id is None:
        _trace(project_dir, None, "pre-edit", "abort", reason="no_session_id", file_path=file_path)
        return 0

    plugin_root = _plugin_root()
    if project_dir is None or plugin_root is None:
        _trace(
            project_dir,
            session_id,
            "pre-edit",
            "abort",
            reason="missing_env",
            has_project_dir=project_dir is not None,
            has_plugin_root=plugin_root is not None,
        )
        return 0

    # Empty suffix (e.g., `Makefile`, `Dockerfile`) intentionally falls through:
    # `language` stays None, only `general` is considered for injection.
    extension = Path(file_path).suffix.lower()
    language = EXTENSION_MAP.get(extension)

    state_file = _state_file(project_dir, session_id)
    already = _read_injected(state_file)
    _trace(
        project_dir,
        session_id,
        "pre-edit",
        "resolved",
        file_path=file_path,
        extension=extension,
        language=language,
        already_injected=sorted(already),
    )

    emissions_by_category: dict[str, list[Path]] = {}
    new_keys: list[str] = []
    plugin_root_abs = plugin_root.resolve()

    for category in _collect_rulesets(plugin_root, "general"):
        dedup_key = f"{category}:general"
        if dedup_key in already:
            continue
        abs_path = plugin_root_abs / "rulesets" / category / "general.md"
        emissions_by_category.setdefault(category, []).append(abs_path)
        new_keys.append(dedup_key)

    if language:
        for category in _collect_rulesets(plugin_root, language):
            dedup_key = f"{category}:{language}"
            if dedup_key in already:
                continue
            abs_path = plugin_root_abs / "rulesets" / category / f"{language}.md"
            emissions_by_category.setdefault(category, []).append(abs_path)
            new_keys.append(dedup_key)

    if not emissions_by_category:
        _trace(
            project_dir,
            session_id,
            "pre-edit",
            "silent",
            reason="all_dedup_or_no_match",
            language=language,
        )
        return 0

    _record_injected(state_file, new_keys)

    if language:
        lang_display = LANGUAGE_DISPLAY.get(language, language)
        scope_phrase = f"when editing {lang_display} files"
    else:
        scope_phrase = "on every edit"

    sections: list[str] = []
    for category, paths in emissions_by_category.items():
        cat_display = category.capitalize()
        pointer_block = "\n".join(f"- `{p}`" for p in paths)
        sections.append(
            f"## {cat_display} rules to follow {scope_phrase}\n\n"
            "Read these — binding:\n\n"
            f"{pointer_block}"
        )

    additional_context = "\n\n".join(sections) + "\n"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": additional_context,
        }
    }
    json.dump(output, sys.stdout)
    _trace(
        project_dir,
        session_id,
        "pre-edit",
        "inject",
        file_path=file_path,
        language=language,
        injected_keys=new_keys,
        context_bytes=len(additional_context),
    )
    return 0


def session_end() -> int:
    project_dir = _project_dir()
    payload = _read_payload()
    if payload is None:
        _trace(project_dir, None, "session-end", "abort", reason="no_payload")
        return 0

    session_id_raw = payload.get("session_id")
    session_id = session_id_raw if isinstance(session_id_raw, str) and session_id_raw else None
    if session_id is None:
        _trace(project_dir, None, "session-end", "abort", reason="no_session_id")
        return 0

    if project_dir is None:
        _trace(None, session_id, "session-end", "abort", reason="no_project_dir")
        return 0

    state_file = _state_file(project_dir, session_id)
    existed = state_file.is_file()
    try:
        state_file.unlink(missing_ok=True)
        deleted = existed
        error = None
    except OSError as e:
        deleted = False
        error = str(e)

    _trace(
        project_dir,
        session_id,
        "session-end",
        "cleanup",
        existed=existed,
        deleted=deleted,
        error=error,
    )
    return 0


def session_start() -> int:
    project_dir = _project_dir()
    if project_dir is None:
        _trace(None, None, "session-start", "abort", reason="no_project_dir")
        return 0

    state_dir = _state_dir(project_dir)
    if not state_dir.is_dir():
        _trace(project_dir, None, "session-start", "noop", reason="no_state_dir")
        return 0

    cutoff = time.time() - ORPHAN_MAX_AGE_SECONDS
    swept: list[str] = []
    try:
        entries = list(state_dir.iterdir())
    except OSError as e:
        _trace(project_dir, None, "session-start", "abort", reason="iterdir_failed", error=str(e))
        return 0

    for entry in entries:
        if not entry.is_file():
            continue
        name = entry.name
        if not (name.startswith(STATE_FILE_PREFIX) and name.endswith(STATE_FILE_SUFFIX)):
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            try:
                entry.unlink()
                swept.append(name)
            except OSError:
                pass

    # Trace-log self-rotation: truncate if older than the same orphan cutoff.
    trace_path = _trace_file(project_dir)
    truncated_trace = False
    if trace_path.is_file():
        try:
            if trace_path.stat().st_mtime < cutoff:
                trace_path.write_text("", encoding="utf-8")
                truncated_trace = True
        except OSError:
            pass

    _trace(
        project_dir,
        None,
        "session-start",
        "sweep",
        swept_count=len(swept),
        swept=swept,
        truncated_trace=truncated_trace,
    )
    return 0


SUBCOMMANDS = {
    "pre-edit": pre_edit,
    "session-end": session_end,
    "session-start": session_start,
}


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    handler = SUBCOMMANDS.get(sys.argv[1])
    if handler is None:
        return 0
    try:
        return handler()
    except Exception as e:
        _trace(_project_dir(), None, sys.argv[1], "exception", error=repr(e))
        return 0


if __name__ == "__main__":
    sys.exit(main())
