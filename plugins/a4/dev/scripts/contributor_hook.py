# /// script
# requires-python = ">=3.11"
# ///
"""a4 contributor-side audience-injection hook.

Distinct from the workspace-side `scripts/a4_hook.py` — that hook fires on
`<project-root>/a4/**/*.md` (end-user authoring). This one fires on
`plugins/a4/**/*.md` (plugin contributor work in this repo) and surfaces
the per-layer audience / citation contract.

Subcommands:
  pre-read       PreToolUse on Read. When a contributor first opens a
                 specific `plugins/a4/**/*.md` this session, emit a
                 file-scoped note: which layer the file belongs to and
                 the binding rules for that layer. On the very first
                 match in the session (across read AND edit), the full
                 layer map is prepended once.
  pre-edit       PreToolUse on Write|Edit|MultiEdit. Same shape as
                 pre-read; uses the same per-file dedup so reading then
                 editing a file does not double-emit, and the layer-map
                 prepend uses the same session-wide sentinel so it
                 fires at most once per session regardless of whether
                 the first matching tool was Read or Edit.

The layer map is loaded lazily on first `plugins/a4/` touch rather than
at SessionStart — sessions that never work on a4 do not pay the context
cost.

Session-scoped state under `.claude/tmp/a4-edited/`:
  a4-contributor-files-<sid>.txt   — newline-delimited file paths
                                     already announced this session
                                     (per-file dedup).
  a4-contributor-map-<sid>.flag    — touched once when the layer map
                                     has been prepended this session.
Cleaned up by `cleanup-contributor.sh` (SessionEnd) and swept by
`sweep-contributor.sh` (SessionStart, age-based for crashed sessions).

End-user impact: zero. Pre-tool hooks gate on a `plugins/a4/` path
prefix under `$CLAUDE_PROJECT_DIR`; that prefix exists only when a
contributor edits this plugin's own source.

Conventions (state classification, lifecycle symmetry, blocking policy,
output channel) follow `plugins/a4/dev/hook-conventions.md`.

Registered in repo `.claude/settings.json` (not in plugin manifest) so
it applies only to contributors who clone this repository.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


_PLUGIN_REL = ("plugins", "a4")
_SENTINEL_DIR = (".claude", "tmp", "a4-edited")
_FILES_BASENAME = "a4-contributor-files-{sid}.txt"
_MAP_BASENAME = "a4-contributor-map-{sid}.flag"


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    sub = sys.argv[1]
    if sub == "pre-read":
        return _pre_read()
    if sub == "pre-edit":
        return _pre_edit()
    return 0


# ----------------------------- PreToolUse ---------------------------------


def _pre_read() -> int:
    """PreToolUse(Read). Emit a per-file layer note on first Read of a
    `plugins/a4/**/*.md` file in this session.
    """
    payload = _payload()
    if payload is None:
        return 0
    if payload.get("tool_name") != "Read":
        return 0
    return _inject_per_file(payload, intent="read")


def _pre_edit() -> int:
    """PreToolUse(Write|Edit|MultiEdit). Same shape as _pre_read with
    edit phrasing.
    """
    payload = _payload()
    if payload is None:
        return 0
    if payload.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    return _inject_per_file(payload, intent="edit")


def _payload() -> dict | None:
    raw = sys.stdin.read()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _inject_per_file(payload: dict, intent: str) -> int:
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    session_id = payload.get("session_id") or ""
    if not file_path or not session_id or not file_path.endswith(".md"):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0

    plugin_root = Path(project_dir).joinpath(*_PLUGIN_REL)
    plugin_prefix = str(plugin_root) + os.sep
    if not file_path.startswith(plugin_prefix):
        return 0

    if _already_announced(project_dir, session_id, file_path):
        return 0
    if not _record_announced(project_dir, session_id, file_path):
        return 0

    layer = _resolve_layer(file_path, plugin_root)
    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + os.sep)
        else file_path
    )
    intent_label = "read" if intent == "read" else "edit"
    layer_note = _LAYER_NOTES.get(layer, _LAYER_NOTES["other"])
    file_body = (
        f"**a4 ({intent_label})** `{display_rel}` — layer **{layer}**. "
        f"{layer_note}"
    )

    map_prefix = _layer_map_prefix(project_dir, session_id)
    if map_prefix is not None:
        body = map_prefix + "\n\n---\n\n" + file_body
    else:
        body = file_body

    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": body,
            }
        }
    )
    return 0


# --------------------------- layer-map prepend ----------------------------


def _layer_map_prefix(project_dir: str, session_id: str) -> str | None:
    """Return the full layer-map block on the first call per session,
    None thereafter. Touches the session sentinel atomically — if the
    sentinel cannot be written, we still return None to avoid emitting
    the heavy map repeatedly.
    """
    sentinel = (
        Path(project_dir).joinpath(*_SENTINEL_DIR)
        / _MAP_BASENAME.format(sid=session_id)
    )
    if sentinel.is_file():
        return None
    try:
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.touch(exist_ok=True)
    except OSError:
        return None
    return _LAYER_MAP_BLOCK


_LAYER_MAP_BLOCK = (
    "**a4 plugin layer map** (loaded once on first `plugins/a4/` touch). "
    "Path purity is binding — do not invert citation direction.\n"
    "- `authoring/` — workspace authors. Cite `./*` + `../scripts/*.py`. "
    "No `../workflows/`, `../skills/`, `../dev/`. Relative paths.\n"
    "- `workflows/` — skill runtimes. Cite `./*` + `../authoring/`. "
    "No `../scripts/`, `../dev/`.\n"
    "- `dev/` — contributors only. May cite anywhere; reverse refs "
    "forbidden.\n"
    "- `skills/<name>/**`, `agents/*.md` — skill / agent definitions. "
    "Cite `${CLAUDE_PLUGIN_ROOT}/{authoring,workflows}/`. Never `dev/`.\n"
    "- `scripts/` — workspace runtime. `dev/scripts/` — contributor "
    "tooling (registered via repo `.claude/settings.json`).\n"
    "- `hooks/` — workspace hook manifests + bash wrappers.\n"
    "Binding rules live in each directory's `CLAUDE.md`."
)


# ----------------------------- per-file dedup -----------------------------


def _files_log_path(project_dir: str, session_id: str) -> Path:
    return (
        Path(project_dir)
        .joinpath(*_SENTINEL_DIR)
        / _FILES_BASENAME.format(sid=session_id)
    )


def _already_announced(project_dir: str, session_id: str, file_path: str) -> bool:
    path = _files_log_path(project_dir, session_id)
    if not path.is_file():
        return False
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() == file_path:
                return True
    except OSError:
        return False
    return False


def _record_announced(project_dir: str, session_id: str, file_path: str) -> bool:
    path = _files_log_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(file_path + "\n")
    except OSError:
        return False
    return True


# ----------------------------- layer routing ------------------------------


def _resolve_layer(file_path: str, plugin_root: Path) -> str:
    """Return the layer name for the matched file: authoring | workflows |
    dev | dev-scripts | skills | agents | scripts | hooks | other.
    """
    try:
        rel = Path(file_path).resolve().relative_to(plugin_root.resolve())
    except (OSError, ValueError):
        return "other"
    parts = rel.parts
    if not parts:
        return "other"
    head = parts[0]
    if head == "dev" and len(parts) >= 2 and parts[1] == "scripts":
        return "dev-scripts"
    if head in ("authoring", "workflows", "dev", "skills", "agents", "scripts", "hooks"):
        return head
    return "other"


_LAYER_NOTES: dict[str, str] = {
    "authoring": (
        "End-user workspace contract. Cite `./*` + `../scripts/*.py`. "
        "No workflows/skills/dev. Relative paths only."
    ),
    "workflows": (
        "Skill orchestration. Cite `./*` + `../authoring/`. "
        "No scripts/dev."
    ),
    "dev": (
        "Plugin internals. May cite anywhere; reverse refs forbidden."
    ),
    "dev-scripts": (
        "Contributor tooling (not in plugin manifest). Type hints; "
        "invoke via `uv run`."
    ),
    "skills": (
        "Cite `${CLAUDE_PLUGIN_ROOT}/{authoring,workflows}/`. Never "
        "`dev/`. `SKILL.md` is orchestration; procedures in "
        "`references/`."
    ),
    "agents": (
        "Same as skills: `${CLAUDE_PLUGIN_ROOT}` paths, never `dev/`."
    ),
    "scripts": (
        "Workspace runtime. Type hints; `uv run` (not `python`)."
    ),
    "hooks": (
        "Manifest + bash wrappers; substantive logic in "
        "`../scripts/a4_hook.py`. Always exit 0."
    ),
    "other": (
        "Not in canonical layers — confirm location before editing."
    ),
}


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
