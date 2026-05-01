# /// script
# requires-python = ">=3.11"
# ///
"""a4 contributor-side audience-injection hook.

Distinct from the workspace-side `scripts/a4_hook.py` — that hook fires on
`<project-root>/a4/**/*.md` (end-user authoring). This one fires on
`plugins/a4/**/*.md` (plugin contributor work in this repo) and surfaces
two things:
  - On the first matching Read/Edit per session: the global layer map
    (which directory has which audience + citation summary).
  - On every file's first Read or Edit: a one-line note naming that
    specific file's audience and pointing to the directory's binding
    `CLAUDE.md`.

The two are deliberately distinct: the layer map gives the routing big
picture once; the per-file note disambiguates which slot the current
file occupies. Detailed citation/body rules live in each directory's
`CLAUDE.md` — this hook does not duplicate them.

Subcommands:
  pre-read       PreToolUse on Read. Emit per-file note (with layer-map
                 prepended on first session match).
  pre-edit       PreToolUse on Write|Edit|MultiEdit. Same shape as
                 pre-read; shares the per-file dedup AND the layer-map
                 sentinel so a Read followed by an Edit of the same
                 file does not double-emit either layer.

Session-scoped state under `.claude/tmp/a4-edited/`:
  a4-contributor-files-<sid>.txt   — newline-delimited file paths
                                     already announced this session.
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
    payload = _payload()
    if payload is None:
        return 0
    if payload.get("tool_name") != "Read":
        return 0
    return _inject_per_file(payload, intent="read")


def _pre_edit() -> int:
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
    audience, claude_md = _LAYER_INFO.get(layer, _LAYER_INFO["other"])
    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + os.sep)
        else file_path
    )
    intent_label = "read" if intent == "read" else "edit"
    file_note = (
        f"**a4 ({intent_label})** `{display_rel}` — audience: {audience}. "
        f"See `{claude_md}` for binding rules."
    )

    map_prefix = _layer_map_prefix(project_dir, session_id)
    body = file_note if map_prefix is None else (
        map_prefix + "\n\n---\n\n" + file_note
    )
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
    """Return the layer-map block on the first call per session, None
    thereafter. Touches the session sentinel atomically — if the
    sentinel cannot be written, we still return None to avoid emitting
    the map repeatedly.
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
    "Each directory has a fixed audience and citation contract — do not "
    "invert the citation direction.\n"
    "- `authoring/` — workspace authors editing "
    "`<project-root>/a4/**/*.md`. Cite `./*` + `../scripts/*.py`. No "
    "`../workflows/`, `../skills/`, `../dev/`. Relative paths.\n"
    "- `workflows/` — skill runtimes. Cite `./*` + `../authoring/`. No "
    "`../scripts/`, `../dev/`.\n"
    "- `dev/` — plugin contributors. May cite anywhere; reverse refs "
    "forbidden.\n"
    "- `dev/scripts/` — plugin contributors (contributor tooling, "
    "registered via repo `.claude/settings.json`, not in the plugin "
    "manifest).\n"
    "- `skills/<name>/**`, `agents/*.md` — skill / agent runtime. Cite "
    "`${CLAUDE_PLUGIN_ROOT}/{authoring,workflows}/`. Never `dev/`.\n"
    "- `scripts/` — workspace runtime (validators, hook dispatcher, "
    "cascade primitives).\n"
    "- `hooks/` — workspace hook manifests + bash wrappers; substantive "
    "logic lives in `scripts/a4_hook.py`.\n"
    "Detailed binding rules live in each directory's `CLAUDE.md` — the "
    "per-file note will point you at the right one."
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
    """Return the layer name: authoring | workflows | dev | dev-scripts |
    skills | agents | scripts | hooks | other.
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


# (audience, CLAUDE.md path) per layer. Detailed citation / body rules
# live in each CLAUDE.md — this hook only points contributors at it.
_LAYER_INFO: dict[str, tuple[str, str]] = {
    "authoring": (
        "workspace authors editing `<project-root>/a4/**/*.md`",
        "plugins/a4/authoring/CLAUDE.md",
    ),
    "workflows": (
        "skill runtimes",
        "plugins/a4/workflows/CLAUDE.md",
    ),
    "dev": (
        "plugin contributors",
        "plugins/a4/dev/CLAUDE.md",
    ),
    "dev-scripts": (
        "plugin contributors (contributor-side tooling)",
        "plugins/a4/dev/CLAUDE.md",
    ),
    "skills": (
        "skill runtime",
        "plugins/a4/CLAUDE.md",
    ),
    "agents": (
        "skill runtime (subagent definitions)",
        "plugins/a4/CLAUDE.md",
    ),
    "scripts": (
        "workspace runtime",
        "plugins/a4/CLAUDE.md",
    ),
    "hooks": (
        "workspace hook runtime",
        "plugins/a4/CLAUDE.md",
    ),
    "other": (
        "unknown (file is outside canonical layers)",
        "plugins/a4/CLAUDE.md",
    ),
}


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
