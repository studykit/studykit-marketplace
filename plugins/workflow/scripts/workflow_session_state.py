#!/usr/bin/env python3
"""File-backed session state for workflow hooks.

Tracks per-(project, session) ledgers under ``.workflow-cache/hook-state/``:

- announced/mentioned/pending issue lists, used by ``UserPromptSubmit`` and
  ``Stop`` to dedupe issue cache injection and carry pending refs across
  turns.
- a per-(runtime, session) marker file used by ``SessionStart`` to inject the
  workflow policy at most once per session unless ``source == clear``
  triggers a re-injection.

Helpers stay narrow: every function takes ``project``/``session_id`` plus
the minimum extras it needs and is silent on filesystem errors so hook
execution never breaks on disk hiccups.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_github import normalize_issue_number  # noqa: E402

HOOK_STATE_DIR_NAME = "hook-state"

_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX_SESSION_SLUG_LEN = 120


def workflow_hook_state_dir(project: Path) -> Path:
    return GitHubIssueCache.for_project(project).root / HOOK_STATE_DIR_NAME


def issue_state_path(project: Path, session_id: str, kind: str) -> Path | None:
    safe_session = _safe_token(session_id)
    if not safe_session:
        return None
    return workflow_hook_state_dir(project) / f"workflow-{kind}-issues-{safe_session}.txt"


def session_policy_state_path(project: Path, runtime: str, session_id: str) -> Path | None:
    safe_session = _safe_token(session_id)
    if not safe_session:
        return None
    safe_runtime = _safe_token(runtime) or "unknown"
    return workflow_hook_state_dir(project) / (
        f"workflow-session-policy-{safe_runtime}-{safe_session}.txt"
    )


def session_policy_was_announced(project: Path, runtime: str, session_id: str) -> bool:
    path = session_policy_state_path(project, runtime, session_id)
    return bool(path is not None and path.is_file())


def record_session_policy_announced(project: Path, runtime: str, session_id: str) -> None:
    path = session_policy_state_path(project, runtime, session_id)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("announced\n", encoding="utf-8")
    except OSError:
        return


def read_session_issues(project: Path, session_id: str, kind: str) -> set[str]:
    path = issue_state_path(project, session_id, kind)
    if path is None or not path.is_file():
        return set()
    try:
        return {
            normalize_issue_number(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except Exception:
        return set()


def record_session_issues(
    project: Path,
    session_id: str,
    issues: list[str],
    kind: str,
) -> None:
    path = issue_state_path(project, session_id, kind)
    if path is None or not issues:
        return
    existing = read_session_issues(project, session_id, kind)
    for issue in issues:
        try:
            existing.add(normalize_issue_number(issue))
        except Exception:
            continue
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(existing, key=lambda value: int(value))
        path.write_text("\n".join(ordered) + ("\n" if ordered else ""), encoding="utf-8")
    except OSError:
        return


def remove_session_issues(
    project: Path,
    session_id: str,
    issues: list[str],
    kind: str,
) -> None:
    path = issue_state_path(project, session_id, kind)
    if path is None or not path.exists():
        return
    remove: set[str] = set()
    for issue in issues:
        try:
            remove.add(normalize_issue_number(issue))
        except Exception:
            continue
    remaining = read_session_issues(project, session_id, kind) - remove
    try:
        if not remaining:
            path.unlink()
            return
        ordered = sorted(remaining, key=lambda value: int(value))
        path.write_text("\n".join(ordered) + "\n", encoding="utf-8")
    except OSError:
        return


def _safe_token(value: str) -> str:
    if not value:
        return ""
    sanitized = _SAFE_TOKEN_RE.sub("_", value).strip("._-")
    return sanitized[:_MAX_SESSION_SLUG_LEN]
