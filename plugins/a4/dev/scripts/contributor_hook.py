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
    intent_label = "Reading" if intent == "read" else "About to write"
    layer_notes = _LAYER_NOTES.get(layer, _LAYER_NOTES["other"])
    file_body = (
        f"## a4 contributor — `{display_rel}`\n\n"
        f"{intent_label} this file. Layer: **{layer}**.\n\n"
        f"{layer_notes}\n\n"
        f"Injected once per file per session — will not re-emit on "
        f"subsequent Read/Edit of `{display_rel}`."
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
    "## a4 plugin contributor — audience routing (lazy-loaded on first "
    "`plugins/a4/` touch)\n\n"
    "You just touched a file under `plugins/a4/` — this plugin's own "
    "source. Every directory has a fixed audience and a binding "
    "citation contract; do not mix them. This map is injected once per "
    "session at the first matching Read/Edit; subsequent file-specific "
    "notes will only name the layer and its key rules.\n\n"
    "**Layer map (path purity is binding):**\n\n"
    "- **`plugins/a4/authoring/`** — workspace authoring contract. "
    "Audience: workspace authors editing `<project-root>/a4/**/*.md` "
    "and LLMs editing those files on the user's behalf. Cite `./` "
    "siblings and `../scripts/<script>.py` (script *usage* in prose) "
    "only. NO `../workflows/`, `../skills/`, `../dev/`. Use relative "
    "paths in shell snippets too — `${CLAUDE_PLUGIN_ROOT}` is not "
    "expanded here. Two scope exceptions: "
    "`commit-message-convention.md` extends to anyone authoring "
    "commits derived from a4 artifacts; `usecase-abstraction-guard.md` "
    "narrows to `<project-root>/a4/usecase/*.md`.\n"
    "- **`plugins/a4/workflows/`** — skill orchestration contract. "
    "Audience: skill runtimes. Cite `./` siblings and `../authoring/` "
    "only. NO `../scripts/`, `../dev/`. Relative paths.\n"
    "- **`plugins/a4/dev/`** — plugin internals. Audience: plugin "
    "contributors only. May cite anywhere; skills, agents, authoring, "
    "and workflows MUST NOT cite back into this directory.\n"
    "- **`plugins/a4/skills/<name>/**`** and **`plugins/a4/agents/*.md`** "
    "— skill / agent definitions. Cite `${CLAUDE_PLUGIN_ROOT}/authoring/` "
    "and `${CLAUDE_PLUGIN_ROOT}/workflows/`. NEVER cite "
    "`${CLAUDE_PLUGIN_ROOT}/dev/`. `${CLAUDE_PLUGIN_ROOT}` is the "
    "binding form for both markdown and shell.\n"
    "- **`plugins/a4/scripts/`** — workspace-side runtime code "
    "(validators, hook dispatcher, cascade primitives). Distinct from "
    "`plugins/a4/dev/scripts/`, which is contributor-only tooling.\n"
    "- **`plugins/a4/dev/scripts/`** — contributor-only tooling (this "
    "hook, cleanup/sweep wrappers). Registered in repo "
    "`.claude/settings.json`, not in any plugin manifest.\n"
    "- **`plugins/a4/hooks/`** — workspace hook manifests + small bash "
    "wrappers for tmp-file lifecycle.\n\n"
    "**Audience drift signal:** if you find a skill or agent citing "
    "`../dev/`, or `authoring/` citing `workflows/`, that is a bug — "
    "promote or relocate the content to the correct layer rather than "
    "inverting the dependency.\n\n"
    "Per-directory `CLAUDE.md` files carry the binding rules."
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
        "**Audience:** workspace authors editing "
        "`<project-root>/a4/**/*.md` (and LLMs on their behalf). This is "
        "a binding contract for end-user workspace files — precise and "
        "conservative tone, state *what* is valid, not *how* it is "
        "checked. Cite only `./` siblings and `../scripts/<script>.py` "
        "(script *usage* in prose). NO `../workflows/`, `../skills/`, "
        "`../dev/`. Use relative paths in shell snippets — "
        "`${CLAUDE_PLUGIN_ROOT}` is not expanded here. New `type:` value "
        "→ add `<type>-authoring.md`; workspace-wide rule → extend "
        "`frontmatter-universals.md` or `body-conventions.md`."
    ),
    "workflows": (
        "**Audience:** skill runtimes. Cross-skill orchestration only — "
        "skill modes, pipeline shapes, iterate mechanics, "
        "wiki-authorship policy. Cite `./` siblings and `../authoring/` "
        "for the frontmatter contract. NO `../scripts/`, `../dev/`. "
        "Relative paths. A single skill's procedure does NOT belong "
        "here — it belongs in `../skills/<name>/references/`."
    ),
    "dev": (
        "**Audience:** plugin contributors only. The only layer that "
        "may cite anywhere — `../scripts/`, `../authoring/`, "
        "`../workflows/`, `../hooks/`, `../skills/`. Skills, agents, "
        "authoring, workflows MUST NOT cite back into this directory. "
        "Lead each entry with the file path; reserve prose for design "
        "rationale that fits nowhere else."
    ),
    "dev-scripts": (
        "**Audience:** plugin contributors only — contributor-side "
        "tooling (this hook, cleanup/sweep wrappers, future "
        "contributor-facing scripts). Distinct from `../../scripts/` "
        "which is workspace runtime code. Registered via repo "
        "`.claude/settings.json`, not via any plugin manifest, so "
        "end-user installs of the a4 plugin never run these. "
        "Type hints required on Python; invoke via `uv run`."
    ),
    "skills": (
        "**Audience:** skill runtime. `SKILL.md` is orchestration only "
        "(preflight + step list + non-goals). Procedures live in "
        "`references/*.md`. Cite "
        "`${CLAUDE_PLUGIN_ROOT}/authoring/` and "
        "`${CLAUDE_PLUGIN_ROOT}/workflows/`. NEVER cite "
        "`${CLAUDE_PLUGIN_ROOT}/dev/`. Use `${CLAUDE_PLUGIN_ROOT}` for "
        "both markdown citations and shell snippets — env var expands "
        "at skill-invocation time."
    ),
    "agents": (
        "**Audience:** skill runtime (subagent definitions: reviewers, "
        "composers, implementers, workspace-assistant). Same path-form "
        "rules as `skills/`: `${CLAUDE_PLUGIN_ROOT}/...` for citations "
        "and shell, never `../dev/`."
    ),
    "scripts": (
        "**Audience:** workspace runtime (validators, hook dispatcher, "
        "cascade primitives). Imports happen in-process from the hook "
        "dispatcher — keep top-level imports light. Type hints required "
        "on anything beyond a one-off script. Invoke with `uv run`, not "
        "`python` directly."
    ),
    "hooks": (
        "**Audience:** workspace hook runtime. `hooks.json` manifest + "
        "small bash wrappers for trivial tmp-file lifecycle. "
        "Substantive hook logic lives in `../scripts/a4_hook.py` (or, "
        "for contributor-only flows, `../dev/scripts/`). Always exit 0 "
        "in lifecycle wrappers — never block session boundaries."
    ),
    "other": (
        "This file is not in one of the canonical layers "
        "(`authoring/`, `workflows/`, `dev/`, `skills/`, `agents/`, "
        "`scripts/`, `hooks/`). Confirm it belongs in `plugins/a4/` at "
        "all before editing — most contributor-relevant content lives "
        "in those seven directories."
    ),
}


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    sys.exit(main())
