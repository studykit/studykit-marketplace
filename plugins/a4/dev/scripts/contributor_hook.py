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
    `CLAUDE.md`. `CLAUDE.md` and `AGENTS.md` files themselves are
    special-cased — their audience is plugin contributors regardless of
    layer (the per-layer audience in `_LAYER_INFO` describes the
    directory's *other* files).

The two are deliberately distinct: the layer map gives the routing big
picture once; the per-file note disambiguates which slot the current
file occupies. Detailed citation/body rules live in each directory's
`CLAUDE.md` — this hook does not duplicate them.

Subcommands:
  pre-read       Claude PreToolUse on Read. Emit per-file note (with
                 layer-map prepended on first session match).
  pre-edit       Claude PreToolUse on Write|Edit|MultiEdit. Same shape as
                 pre-read; shares the per-file dedup AND the layer-map
                 sentinel so a Read followed by an Edit of the same
                 file does not double-emit either layer. Codex PreToolUse
                 is intentionally silent because Codex currently does not
                 inject PreToolUse `additionalContext` into the model.
  post-edit      Codex PostToolUse on apply_patch. Emit one aggregated
                 PostToolUse JSON object with per-file notes for touched
                 `plugins/a4/**/*.md` files.
  session-start  Sweep orphan contributor-hook sentinels older than 1 day.
                 This is the Codex replacement for SessionEnd cleanup,
                 because Codex does not currently support SessionEnd.

Session-scoped state under `.claude/tmp/a4-edited/`:
  a4-contributor-files-<sid>.txt        — newline-delimited file paths
                                          already announced this session.
  a4-contributor-map-<sid>.flag         — touched once when the layer map
                                          has been prepended this session.
  a4-contributor-hooks-time-<sid>.flag  — touched once when the KST
                                          timestamp block has been
                                          injected on the first edit
                                          under `plugins/a4/hooks/`.
Cleaned up by `cleanup-contributor.sh` (Claude SessionEnd) and swept by
`sweep-contributor.sh` / `session-start` (age-based for crashed sessions
and Codex sessions).

End-user impact: zero. Tool hooks gate on a `plugins/a4/` path prefix
under the active project root; that prefix exists only when a contributor
edits this plugin's own source.

Conventions (state classification, lifecycle symmetry, blocking policy,
output channel) follow `plugins/a4/dev/hook-conventions.md`.

Registered in repo `.claude/settings.json` and `.codex/hooks.json` (not in
the plugin manifest) so it applies only to contributors who clone this
repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


_PLUGIN_REL = ("plugins", "a4")
_HOOKS_REL = ("plugins", "a4", "hooks")
_SENTINEL_DIR = (".claude", "tmp", "a4-edited")
_FILES_BASENAME = "a4-contributor-files-{sid}.txt"
_MAP_BASENAME = "a4-contributor-map-{sid}.flag"
_HOOKS_TIME_BASENAME = "a4-contributor-hooks-time-{sid}.flag"
_RUNTIME_ENV_VAR = "A4_HOOK_RUNTIME"
_CLAUDE_EDIT_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
_GUARDRAIL_FILENAMES = frozenset({"CLAUDE.md", "AGENTS.md"})
_STALE_SENTINEL_SECONDS = 24 * 60 * 60


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    sub = sys.argv[1]
    if sub == "pre-read":
        return _pre_read()
    if sub == "pre-edit":
        return _pre_edit()
    if sub == "post-edit":
        return _post_edit()
    if sub == "session-start":
        return _session_start()
    return 0


# ----------------------------- Hook events --------------------------------


def _pre_read() -> int:
    payload = _payload()
    if payload is None:
        return 0
    if payload.get("tool_name") != "Read":
        return 0
    # Codex does not expose a built-in Read hook shape equivalent to Claude's
    # file Read event. This path is intentionally Claude-only.
    if _runtime_name(payload) == "codex":
        return 0
    return _emit_payload_targets(payload, intent="read", hook_event="PreToolUse")


def _pre_edit() -> int:
    payload = _payload()
    if payload is None:
        return 0

    runtime = _runtime_name(payload)
    if runtime == "codex":
        # Codex parses but does not currently inject PreToolUse
        # `additionalContext`; emitting the Claude-shaped context here would be
        # noisy at best and invalid for some clients. Codex receives the same
        # contributor guidance through PostToolUse, where additionalContext is
        # supported.
        return 0

    if payload.get("tool_name") not in _CLAUDE_EDIT_TOOLS:
        return 0
    return _emit_payload_targets(payload, intent="edit", hook_event="PreToolUse")


def _post_edit() -> int:
    payload = _payload()
    if payload is None:
        return 0

    runtime = _runtime_name(payload)
    if runtime != "codex" and payload.get("tool_name") != "apply_patch":
        return 0

    session_id = _session_id(payload)
    if not session_id:
        return 0
    project_dir = _project_dir(payload)
    if not project_dir:
        return 0

    contexts: list[str] = []
    for file_path in _edit_targets(payload, project_dir):
        context = _context_for_file(project_dir, session_id, file_path, "edit")
        if context:
            contexts.append(context)

    if contexts:
        _emit_context("PostToolUse", "\n\n---\n\n".join(contexts))
    return 0


def _session_start() -> int:
    payload = _payload() or {}
    project_dir = _project_dir(payload)
    if project_dir:
        _sweep_stale_sentinels(project_dir)
    return 0


# ----------------------------- Payload IO ---------------------------------


def _payload() -> dict | None:
    raw = sys.stdin.read()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _emit_context(hook_event: str, body: str) -> None:
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": hook_event,
                "additionalContext": body,
            }
        }
    )


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


# ----------------------------- Runtime ------------------------------------


def _runtime_name(payload: dict) -> str:
    runtime = os.environ.get(_RUNTIME_ENV_VAR, "").strip().lower()
    if runtime in {"claude", "codex"}:
        return runtime

    tool_name = payload.get("tool_name")
    if tool_name == "apply_patch" or payload.get("turn_id"):
        return "codex"
    if tool_name == "Read" or tool_name in _CLAUDE_EDIT_TOOLS:
        return "claude"
    return "unknown"


def _session_id(payload: dict) -> str:
    session_id = payload.get("session_id") or payload.get("turn_id") or ""
    return session_id if isinstance(session_id, str) else ""


def _project_dir(payload: dict) -> str:
    """Return the active repository root for Claude and Codex hooks."""

    runtime = _runtime_name(payload)
    if runtime != "codex":
        explicit = os.environ.get("CLAUDE_PROJECT_DIR")
        if explicit:
            return str(Path(explicit).expanduser().resolve())

    cwd = payload.get("cwd") or os.getcwd()
    if not isinstance(cwd, str) or not cwd:
        return ""
    cwd_path = Path(cwd).expanduser().resolve()

    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd_path), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        root = proc.stdout.strip()
        if root:
            return str(Path(root).resolve())
    except (OSError, subprocess.CalledProcessError):
        pass

    return str(cwd_path)


# ----------------------------- Target parsing -----------------------------


def _emit_payload_targets(payload: dict, intent: str, hook_event: str) -> int:
    session_id = _session_id(payload)
    if not session_id:
        return 0

    project_dir = _project_dir(payload)
    if not project_dir:
        return 0

    targets = (
        _read_targets(payload, project_dir)
        if intent == "read"
        else _edit_targets(payload, project_dir)
    )
    for file_path in targets:
        context = _context_for_file(project_dir, session_id, file_path, intent)
        if context:
            _emit_context(hook_event, context)
    return 0


def _read_targets(payload: dict, project_dir: str) -> list[str]:
    if payload.get("tool_name") != "Read":
        return []
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []
    file_path = tool_input.get("file_path") or ""
    if not isinstance(file_path, str) or not file_path:
        return []
    return [_resolve_path(file_path, payload, project_dir)]


def _edit_targets(payload: dict, project_dir: str) -> list[str]:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []

    if tool_name in _CLAUDE_EDIT_TOOLS:
        file_path = tool_input.get("file_path") or ""
        if not isinstance(file_path, str) or not file_path:
            return []
        return [_resolve_path(file_path, payload, project_dir)]

    if tool_name == "apply_patch":
        command = tool_input.get("command") or ""
        if not isinstance(command, str) or not command:
            return []
        seen: set[str] = set()
        out: list[str] = []
        for raw_path in _apply_patch_paths(command):
            path = _resolve_path(raw_path, payload, project_dir)
            if path in seen:
                continue
            seen.add(path)
            out.append(path)
        return out

    return []


def _resolve_path(raw_path: str, payload: dict, project_dir: str) -> str:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        cwd = payload.get("cwd") or project_dir
        base = (
            Path(cwd).expanduser()
            if isinstance(cwd, str) and cwd
            else Path(project_dir)
        )
        path = base / path
    return str(path.resolve(strict=False))


def _apply_patch_paths(patch_text: str) -> list[str]:
    """Extract file paths from Codex `apply_patch` text."""

    out: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("*** Add File: "):
            out.append(line.removeprefix("*** Add File: ").strip())
        elif line.startswith("*** Update File: "):
            out.append(line.removeprefix("*** Update File: ").strip())
        elif line.startswith("*** Delete File: "):
            out.append(line.removeprefix("*** Delete File: ").strip())
        elif line.startswith("*** Move to: "):
            out.append(line.removeprefix("*** Move to: ").strip())
    return out


# ----------------------------- Context building ---------------------------


def _context_for_file(
    project_dir: str,
    session_id: str,
    file_path: str,
    intent: str,
) -> str | None:
    plugin_root = Path(project_dir).joinpath(*_PLUGIN_REL).resolve(strict=False)
    plugin_prefix = str(plugin_root) + os.sep
    if not file_path.startswith(plugin_prefix):
        return None

    parts: list[str] = []
    if intent == "edit":
        time_prefix = _hooks_time_prefix(project_dir, session_id, file_path)
        if time_prefix is not None:
            parts.append(time_prefix)

    if file_path.endswith(".md"):
        file_note = _file_note(project_dir, plugin_root, session_id, file_path, intent)
        if file_note:
            map_prefix = _layer_map_prefix(project_dir, session_id)
            if map_prefix is not None:
                parts.append(map_prefix)
            parts.append(file_note)

    if not parts:
        return None
    return "\n\n---\n\n".join(parts)


def _file_note(
    project_dir: str,
    plugin_root: Path,
    session_id: str,
    file_path: str,
    intent: str,
) -> str | None:
    if _already_announced(project_dir, session_id, file_path):
        return None
    if not _record_announced(project_dir, session_id, file_path):
        return None

    if Path(file_path).name in _GUARDRAIL_FILENAMES:
        # `CLAUDE.md` and `AGENTS.md` are the directory's contributor
        # guardrails themselves — their audience is plugin contributors
        # regardless of which layer they sit in. The audience listed in
        # `_LAYER_INFO` describes the *other* files in that directory.
        audience = "plugin contributors editing this directory's guardrails"
        claude_md = "plugins/a4/CLAUDE.md"
    else:
        layer = _resolve_layer(file_path, plugin_root)
        audience, claude_md = _LAYER_INFO.get(layer, _LAYER_INFO["other"])

    display_rel = (
        file_path[len(project_dir) + 1 :]
        if file_path.startswith(project_dir + os.sep)
        else file_path
    )
    intent_label = "read" if intent == "read" else "edit"
    return (
        f"**a4 ({intent_label})** `{display_rel}` — audience: {audience}. "
        f"See `{claude_md}` for binding rules."
    )


# --------------------- hooks/ first-edit time prefix ----------------------


def _hooks_time_prefix(
    project_dir: str, session_id: str, file_path: str
) -> str | None:
    """Return a one-shot KST timestamp block on the first edit under
    `plugins/a4/hooks/` per session, None thereafter or when the path is
    outside that directory. Touches the session sentinel atomically — if
    the sentinel cannot be written, we still return None to avoid
    re-emitting on subsequent edits.
    """
    hooks_root = Path(project_dir).joinpath(*_HOOKS_REL).resolve(strict=False)
    hooks_prefix = str(hooks_root) + os.sep
    if not file_path.startswith(hooks_prefix):
        return None

    sentinel = (
        Path(project_dir).joinpath(*_SENTINEL_DIR)
        / _HOOKS_TIME_BASENAME.format(sid=session_id)
    )
    if sentinel.is_file():
        return None
    try:
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.touch(exist_ok=True)
    except OSError:
        return None

    from datetime import datetime, timedelta, timezone

    kst = timezone(timedelta(hours=9))
    stamp = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
    return f"current time (KST): {stamp}"


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
    "- `authoring/` — workspace authors and skill runtime, editing or "
    "reading `<project-root>/a4/**/*.md` contracts. Cite `./*` + "
    "`../scripts/*.py`. No `../skills/`, `../dev/`. Relative paths.\n"
    "- `dev/` — plugin contributors. May cite anywhere; skills must NOT "
    "cite this directory at runtime.\n"
    "- `dev/scripts/` — plugin contributors (contributor tooling, "
    "registered via repo `.claude/settings.json` and `.codex/hooks.json`, "
    "not in the plugin manifest).\n"
    "- `skills/<name>/**`, `agents/*.md` — skill / agent runtime. Cite "
    "`${CLAUDE_PLUGIN_ROOT}/authoring/`. Never `dev/`. Each skill is an "
    "independent entry point — there is no shared orchestration layer.\n"
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


# ----------------------------- Session sweep ------------------------------


def _sweep_stale_sentinels(project_dir: str) -> None:
    record_dir = Path(project_dir).joinpath(*_SENTINEL_DIR)
    if not record_dir.is_dir():
        return

    cutoff = time.time() - _STALE_SENTINEL_SECONDS
    patterns = (
        "a4-contributor-files-*.txt",
        "a4-contributor-map-*.flag",
        "a4-contributor-hooks-time-*.flag",
    )
    for pattern in patterns:
        for path in record_dir.glob(pattern):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue


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
    if head in ("authoring", "dev", "skills", "agents", "scripts", "hooks"):
        return head
    return "other"


# (audience, CLAUDE.md path) per layer. Detailed citation / body rules
# live in each CLAUDE.md — this hook only points contributors at it.
_LAYER_INFO: dict[str, tuple[str, str]] = {
    "authoring": (
        "workspace authors and skill runtime reading `<project-root>/a4/**/*.md` contracts",
        "plugins/a4/authoring/CLAUDE.md",
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


if __name__ == "__main__":
    sys.exit(main())
