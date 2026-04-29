"""Status transition legality check (library).

Compares each issue file's working-tree ``status:`` against its HEAD
counterpart and flags transitions that are not allowed by the family
table in ``status_model.FAMILY_TRANSITIONS``.

Acts as a stop-time **safety net**:
``scripts/transition_status.py`` validates legality before writing on
every authored flip, but if the LLM hand-edits ``status:`` directly
(bypassing the writer), this validator surfaces illegal jumps before
the agent stops.

Scope rules:

  - Files newly added in the working tree (no HEAD copy) are skipped
    here — initial-status validation belongs to the static frontmatter
    check.
  - The ``idea`` / ``spark`` families have no mechanical writer and are
    intentionally absent from ``FAMILY_TRANSITIONS``; they are skipped.
  - Wiki pages and any other non-issue file are skipped.
  - When ``old_status == new_status`` there is no transition.
  - When ``status:`` is missing or non-string in either side, the file
    is skipped (other validators report the type error).

Pure library — no stdout / stderr / exit. The unified CLI
``scripts/validate.py`` adapts ``run_*`` output to ``Issue`` via
``markdown_validator.registry`` and owns presentation / exit codes. The
hook dispatcher ``scripts/a4_hook.py`` calls ``check_files`` directly
on the session's edited file list.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from common import ISSUE_FOLDERS, discover_files
from markdown import extract_preamble, extract_preamble_from_text
from status_model import (
    FAMILY_TRANSITIONS,
    is_transition_legal,
    legal_targets_from,
)


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str
    field: str
    message: str


def check_files(
    a4_dir: Path,
    files: list[Path],
    repo_root: Path | None = None,
) -> list[Violation]:
    """Return illegal status transitions among ``files``.

    ``files`` is the caller-supplied set (typically session-edited
    paths). Files outside ``a4_dir``, outside the issue folders, or
    without a HEAD copy are silently skipped. ``repo_root`` is resolved
    via ``git rev-parse --show-toplevel`` if not supplied; if there is
    no git repo, returns ``[]``.
    """
    if not files:
        return []
    if repo_root is None:
        repo_root = _find_repo_root(a4_dir)
    if repo_root is None:
        return []
    a4_resolved = a4_dir.resolve()
    repo_resolved = repo_root.resolve()
    violations: list[Violation] = []
    for path in files:
        v = _check_one(a4_resolved, repo_resolved, path)
        if v is not None:
            violations.append(v)
    return violations


def run_workspace(a4_dir: Path) -> list[Violation]:
    """Workspace sweep — diff every working-tree issue file against HEAD."""
    return check_files(a4_dir, discover_files(a4_dir))


def run_file(a4_dir: Path, file: Path) -> list[Violation]:
    """Single-file scope — same logic, single path."""
    return check_files(a4_dir, [file])


def _check_one(
    a4_resolved: Path,
    repo_resolved: Path,
    path: Path,
) -> Violation | None:
    try:
        path_resolved = path.resolve()
        rel_to_a4 = path_resolved.relative_to(a4_resolved)
    except (OSError, ValueError):
        return None

    if not rel_to_a4.parts:
        return None
    folder = rel_to_a4.parts[0]
    if folder not in ISSUE_FOLDERS:
        return None
    # idea has no mechanical writer / no transition table.
    if folder not in FAMILY_TRANSITIONS:
        return None

    try:
        rel_to_repo = path_resolved.relative_to(repo_resolved)
    except ValueError:
        return None

    old_text = _git_show_head(repo_resolved, str(rel_to_repo))
    if old_text is None:
        # New file in working tree — no transition baseline.
        return None

    old_pre = extract_preamble_from_text(old_text)
    if old_pre.fm is None:
        return None
    new_pre = extract_preamble(path)
    if new_pre.fm is None:
        return None

    old_status = old_pre.fm.get("status")
    new_status = new_pre.fm.get("status")
    if not isinstance(old_status, str) or not isinstance(new_status, str):
        return None
    if old_status == new_status:
        return None

    rel_str = str(rel_to_a4)
    if is_transition_legal(folder, old_status, new_status):
        return None

    allowed = legal_targets_from(folder, old_status)
    if not allowed:
        return Violation(
            path=rel_str,
            rule="illegal-transition",
            field="status",
            message=(
                f"transition {old_status!r} → {new_status!r} not allowed "
                f"({folder}: {old_status!r} has no outgoing transitions)"
            ),
        )
    return Violation(
        path=rel_str,
        rule="illegal-transition",
        field="status",
        message=(
            f"transition {old_status!r} → {new_status!r} not allowed "
            f"({folder}: from {old_status!r}, allowed targets are "
            f"{sorted(allowed)})"
        ),
    )


def _git_show_head(repo_root: Path, rel: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True,
            cwd=repo_root,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _find_repo_root(start: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            cwd=start,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    line = result.stdout.strip()
    if not line:
        return None
    return Path(line)
