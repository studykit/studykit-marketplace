"""Shared state, helpers, and session-scoped record IO for a4 hook subcommands.

All session-state lives under ``<project>/.claude/tmp/a4-edited/``:

- ``a4-edited-<sid>.txt``        — paths edited this session (PostToolUse → Stop).
- ``a4-prestatus-<sid>.json``    — pre-edit ``status:`` snapshot (Pre → Post).
- ``a4-newfiles-<sid>.txt``      — paths the LLM is about to Write that did not
                                   exist on disk yet (Pre → Post).
- ``a4-injected-<sid>.txt``      — types whose authoring contract was already
                                   injected this session (Pre dedupe).
- ``a4-resolved-ids-<sid>.txt``  — `#<id>` tokens already resolved this session
                                   (UserPromptSubmit dedupe).

All cleanup runs at SessionEnd (`hooks/cleanup-edited-a4.sh`) with a
SessionStart safety-net sweep (`hooks/sweep-old-edited-a4.sh`) for crashed
sessions, per `dev/hook-conventions.md` §2 Rule A.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Plugin-internal anchor paths. Resolved once at import time so every
# subcommand can render fully-qualified absolute pointers to authoring
# contracts without redoing `Path(__file__).resolve().parent.parent.parent`.
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
AUTHORING_DIR = PLUGIN_ROOT / "authoring"


# ----------------------------- generic helpers ----------------------------


def record_dir(project_dir: str) -> Path:
    """Session-scoped state directory shared by all a4-edited family files."""
    return Path(project_dir) / ".claude" / "tmp" / "a4-edited"


def display_rel(file_path: str, project_dir: str) -> str:
    """Render `file_path` as project-dir-relative for human-readable
    `additionalContext` / `systemMessage` output. Falls back to the
    original (absolute) path when the file is outside project_dir.
    """
    prefix = project_dir + "/"
    return file_path[len(prefix):] if file_path.startswith(prefix) else file_path


def project_dir_from_payload(payload: dict) -> str:
    """Resolve the active project directory for Claude Code and Codex hooks.

    Claude Code provides ``CLAUDE_PROJECT_DIR``. Codex hook stdin provides
    ``cwd`` but not that Claude-specific environment variable, so for Codex we
    derive the git root from ``cwd`` and fall back to ``cwd`` itself. The return
    value is a normalized absolute path string or ``""`` when no usable cwd can
    be found.
    """
    import os
    import subprocess

    explicit = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PROJECT_DIR")
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


def resolve_type_from_path(abs_path: Path, a4_dir: Path) -> str | None:
    """Resolve frontmatter `type:` from the file's location under `a4/`.

    The a4 layout pins `type:` by path: top-level `<wiki>.md` files map
    to `WIKI_TYPES`, and flat `<folder>/<id>-<slug>.md` files map to
    `ISSUE_FOLDERS`. Resolving by path avoids a frontmatter parse on
    every edit (cheaper than reading the file just to read `type:`)
    and matches the canonical layout used by `discover_files` and the
    validators. Path-based resolution also works for new-file Writes
    (issue creation), where on-disk frontmatter does not exist yet.

    Returns None for archived files (`a4/archive/...`) — archived files
    retain their original `type:` but are not active edit targets, so
    contract injection is skipped.
    """
    try:
        rel = abs_path.resolve(strict=False).relative_to(a4_dir.resolve())
    except (OSError, ValueError):
        return None
    parts = rel.parts
    if not parts:
        return None
    if parts[0] == "archive":
        return None
    try:
        from common import ISSUE_FOLDERS, WIKI_TYPES
    except ImportError:
        return None
    if len(parts) == 1 and parts[0].endswith(".md"):
        stem = parts[0][:-3]
        return stem if stem in WIKI_TYPES else None
    if len(parts) >= 2 and parts[0] in ISSUE_FOLDERS:
        return parts[0]
    return None


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


# ----------------------------- newfiles IO --------------------------------


def newfiles_path(project_dir: str, session_id: str) -> Path:
    return record_dir(project_dir) / f"a4-newfiles-{session_id}.txt"


def read_newfiles(project_dir: str, session_id: str) -> set[str]:
    path = newfiles_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        return {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()


def record_newfile(project_dir: str, session_id: str, file_path: str) -> None:
    path = newfiles_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(file_path + "\n")
    except OSError:
        return


def drop_newfile(project_dir: str, session_id: str, file_path: str) -> None:
    path = newfiles_path(project_dir, session_id)
    if not path.is_file():
        return
    try:
        lines = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and line.strip() != file_path
        ]
    except OSError:
        return
    try:
        if lines:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            path.unlink()
    except OSError:
        return


# ----------------------------- injected IO --------------------------------


def injected_path(project_dir: str, session_id: str) -> Path:
    return record_dir(project_dir) / f"a4-injected-{session_id}.txt"


def read_injected(project_dir: str, session_id: str) -> set[str]:
    path = injected_path(project_dir, session_id)
    if not path.is_file():
        return set()
    try:
        # Strip any pre-existing `<file>\t<type>` lines too — older sessions
        # may still have the (file, type) format on disk; treat the type
        # column as authoritative and ignore the file column.
        return {
            (line.split("\t", 1)[1] if "\t" in line else line).strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()


def record_injected(project_dir: str, session_id: str, type_value: str) -> None:
    path = injected_path(project_dir, session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{type_value}\n")
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
