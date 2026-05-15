#!/usr/bin/env python3
"""Shared workflow hook logic.

The executable entry points are runtime-specific:

- ``hook_claude.py`` adapts Claude Code hook payloads and environment values.
- ``hook_codex.py`` adapts Codex hook payloads and environment values.

This module contains only host-neutral workflow behavior such as workflow
policy text, issue-cache injection, local projection guards, and session-state
coordination. Runtime-specific entry scripts parse their payloads, resolve
runtime values, and call the plain functions here with concrete arguments.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from authoring_guard import evaluate_authoring_guard  # noqa: E402
from authoring_ledger import LedgerError, record_reads  # noqa: E402
from authoring_resolver import ResolverError  # noqa: E402
from workflow_artifact_metadata import infer_artifact_metadata  # noqa: E402
from workflow_command import CommandRunner  # noqa: E402
from workflow_edit_target import EditTarget  # noqa: E402
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_github import GitHubRepository, GitHubRepositoryError, normalize_issue_number  # noqa: E402
from workflow_github import resolve_github_repository  # noqa: E402
from workflow_issue_cache import cache_issue_references  # noqa: E402
from workflow_issue_cache import extract_issue_numbers, format_issue_cache_context  # noqa: E402
from workflow_session_state import (  # noqa: E402
    read_session_issues,
    record_session_issues,
    remove_session_issues,
)
from util import emit_json, is_markdown_path, is_under, is_under_any  # noqa: E402

STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"

# =============================================================================
# Common hook operations
# =============================================================================


def resolve_state_dir(override: Path | None = None) -> Path | None:
    """Resolve the optional workflow ledger state directory."""

    if override is not None:
        return override.resolve()
    explicit = os.environ.get(STATE_DIR_ENV_VAR)
    if explicit:
        return Path(explicit).expanduser().resolve()
    return None


def workflow_config_for_project(project_dir: Path | None) -> WorkflowConfig | None:
    """Resolve the active workflow config, silent on missing project or load errors."""

    if project_dir is None:
        return None
    try:
        return load_workflow_config(project_dir)
    except WorkflowConfigError:
        return None


def record_authoring_read(
    *,
    project_dir: Path | None,
    plugin_root: Path,
    session_id: str,
    read_target: Path | None,
    state_dir: Path | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Record a read of a bundled workflow authoring file."""

    if not session_id:
        return 0
    config = workflow_config_for_project(project_dir)
    if config is None or read_target is None:
        return 0

    authoring_file = workflow_authoring_file(read_target, plugin_root)
    if authoring_file is None:
        return 0

    try:
        record_reads(
            [authoring_file],
            project=config.root,
            session_id=session_id,
            state_dir=resolve_state_dir(state_dir),
            require_config=True,
        )
    except LedgerError:
        return 0

    # `stdout` is accepted for a uniform test signature. Successful read
    # recording intentionally emits no hook context.
    _ = stdout
    return 0


def block_unread_authoring_write(
    *,
    project_dir: Path | None,
    session_id: str,
    edit_targets: tuple[EditTarget, ...],
    state_dir: Path | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Block local projection writes lacking required authoring reads."""

    if not session_id:
        return 0
    config = workflow_config_for_project(project_dir)
    if config is None:
        return 0

    roots = local_workflow_roots(config)
    if not roots:
        return 0

    targets = [
        target
        for target in edit_targets
        if is_markdown_path(target.path) and is_under_any(target.path, roots)
    ]
    if not targets:
        return 0

    for target in targets:
        block_reason = local_projection_guard_reason(
            target,
            config=config,
            session_id=session_id,
            state_dir=resolve_state_dir(state_dir),
        )
        if block_reason:
            emit_json({"decision": "block", "reason": block_reason}, stdout=stdout)
            return 0
    return 0


def inject_prompt_issue_context(
    *,
    project_dir: Path | None,
    session_id: str,
    prompt_text: str,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Cache issue refs from a prompt and inject concise context."""

    config = workflow_config_for_project(project_dir)
    if config is None or config.issues.kind != "github":
        return 0

    repo = github_repo_for_config(config, runner=runner)
    if repo is None:
        return 0

    prompt_numbers = extract_issue_numbers(
        prompt_text,
        repo=repo,
        issue_id_format=config.issue_id_format,
    )
    pending_numbers = sorted(read_session_issues(config.root, session_id, "pending"), key=int)
    issue_numbers = _ordered_issue_union(pending_numbers, prompt_numbers)
    if not issue_numbers:
        return 0

    record_session_issues(config.root, session_id, issue_numbers, "mentioned")

    already_announced = read_session_issues(config.root, session_id, "announced")
    contexts = cache_issue_references(config, issue_numbers, repo=repo, runner=runner)
    fresh_contexts = [context for context in contexts if context.number not in already_announced]
    if pending_numbers and contexts:
        remove_session_issues(
            config.root,
            session_id,
            [context.number for context in contexts],
            "pending",
        )
    if not fresh_contexts:
        return 0

    record_session_issues(
        config.root,
        session_id,
        [context.number for context in fresh_contexts],
        "announced",
    )
    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_issue_cache_context(
                    fresh_contexts,
                    include_details=False,
                ),
            }
        },
        stdout=stdout,
    )
    return 0


def record_stop_issue_references(
    *,
    project_dir: Path | None,
    session_id: str,
    scan_text: str,
    stop_hook_active: bool = False,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Record issue refs known to this session as pending."""

    if stop_hook_active:
        return 0
    # Stop hook JSON output is reserved for block decisions. Context injection
    # happens in UserPromptSubmit so Stop can never fail host output validation.
    _ = stdout

    config = workflow_config_for_project(project_dir)
    if config is None or config.issues.kind != "github":
        return 0

    repo = github_repo_for_config(config, runner=runner)
    if repo is None:
        return 0

    issue_numbers = sorted(read_session_issues(config.root, session_id, "mentioned"), key=int)
    for number in extract_issue_numbers(
        scan_text,
        repo=repo,
        issue_id_format=config.issue_id_format,
    ):
        if number not in issue_numbers:
            issue_numbers.append(number)
    if not issue_numbers:
        return 0

    record_session_issues(config.root, session_id, issue_numbers, "mentioned")
    already_announced = read_session_issues(config.root, session_id, "announced")
    pending_numbers = [number for number in issue_numbers if number not in already_announced]
    record_session_issues(config.root, session_id, pending_numbers, "pending")
    return 0


# =============================================================================
# Module-level helpers used by the handlers
# =============================================================================


def build_session_start_context(config: WorkflowConfig, plugin_root: Path) -> str:
    """Build the context block injected for configured workflow projects."""

    _ = plugin_root  # plugin_root reserved for future template extensions
    return (
        "## workflow authoring policy\n\n"
        f"This project is configured for the workflow plugin (issue provider: `{config.issues.kind}`). "
        "Delegate workflow operations — provider/cache reads, write-back, comment "
        "append, authoring path discovery, guarded writes — to the "
        "`workflow-operator` agent. Pass workflow intent, issue refs, artifact "
        "type, and operation-specific inputs. The operator returns "
        "provider/cache metadata, issue relationship metadata, and paths.\n\n"
        "The operator does not interpret content. Read and summarize issue, "
        "comment, knowledge, or authoring file content directly from the paths "
        "it returns.\n\n"
        f"{build_issue_operation_policy(config)}"
    )


def build_issue_operation_policy(config: WorkflowConfig) -> str:
    """Build SessionStart operation guidance for the configured issue provider."""

    if config.issues.kind == "github":
        return (
            "Workflow issues live in GitHub. The main assistant should not run "
            "raw `gh` for workflow operations — the operator handles GitHub via "
            "workflow scripts with raw `gh` as its own fallback. If the operator "
            "cannot complete a request, report that limitation instead of "
            "running `gh` directly. For cached issue body edits, edit `issue.md` "
            "in the cache projection first, then delegate write-back; use direct "
            "provider edits only when explicitly requested."
        )

    if config.issues.kind == "filesystem":
        return (
            "Workflow issues are filesystem-backed local Markdown artifacts. "
            "Edit them directly at the paths the operator returns after "
            "required authoring contracts are read. Provider cache, write-back, "
            "and comment-append delegation does not apply."
        )

    return (
        f"Workflow issues use the `{config.issues.kind}` provider, not GitHub. "
        "If the operator cannot complete a provider operation, report that "
        "limitation rather than reaching for provider-specific tools directly."
    )


def github_repo_for_config(
    config: WorkflowConfig,
    *,
    runner: CommandRunner | None = None,
) -> GitHubRepository | None:
    """Resolve the configured GitHub issue repository without failing hooks."""

    if config.issues.kind != "github":
        return None
    try:
        return resolve_github_repository(config.root, runner=runner)
    except (GitHubRepositoryError, OSError, subprocess.SubprocessError):
        return None


def local_projection_guard_reason(
    target: EditTarget,
    *,
    config: WorkflowConfig,
    session_id: str,
    state_dir: Path | None = None,
) -> str | None:
    """Return a block reason for a local workflow write, or ``None`` to allow."""

    metadata = infer_artifact_metadata(target)
    if metadata is None:
        return (
            "workflow authoring guard blocked a local projection write because "
            f"the artifact type could not be determined: {target.path}\n\n"
            "Add workflow metadata such as `type: task` and, for `usecase` or "
            "`research`, `role: issue` or `role: knowledge` before writing."
        )

    try:
        result = evaluate_authoring_guard(
            metadata.artifact_type,
            project=config.root,
            session_id=session_id,
            role=metadata.role,
            provider=metadata.provider,
            state_dir=state_dir,
            require_config=True,
        )
    except (ResolverError, LedgerError) as exc:
        return (
            "workflow authoring guard blocked a local projection write because "
            f"authoring requirements could not be resolved for {target.path}.\n\n"
            f"Reason: {exc}"
        )

    if result["ok"]:
        return None

    missing = "\n".join(f"- {path}" for path in result["missing_authoring_files"])
    return (
        "workflow authoring guard blocked a local projection write because "
        "required authoring files have not been read in this session.\n\n"
        f"Target: {target.path}\n"
        f"Artifact type: {metadata.artifact_type}\n"
        f"Role: {result['artifact']['role']}\n"
        f"Provider: {result['artifact']['provider']}\n\n"
        "Read these absolute authoring file paths, then retry the write:\n"
        f"{missing}"
    )


def workflow_authoring_file(path: Path, plugin_root: Path) -> Path | None:
    target = path.expanduser().resolve(strict=False)
    authoring_root = (plugin_root / "authoring").resolve(strict=False)
    if not is_under(target, authoring_root):
        return None
    if target.suffix != ".md" or not target.is_file():
        return None
    return target


def local_workflow_roots(config: WorkflowConfig) -> tuple[Path, ...]:
    roots: list[Path] = []

    if config.local_projection.mode != "none" and config.local_projection.path:
        roots.append((config.root / config.local_projection.path).resolve(strict=False))

    for provider in (config.issues, config.knowledge):
        path = provider.settings.get("path")
        if provider.kind == "filesystem" and isinstance(path, str) and path:
            roots.append((config.root / path).resolve(strict=False))

    return tuple(dict.fromkeys(roots))


def _ordered_issue_union(*groups: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for issue in group:
            try:
                normalized = normalize_issue_number(issue)
            except Exception:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return ordered
