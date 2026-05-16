#!/usr/bin/env python3
"""Shared workflow hook logic.

The executable entry points are runtime-specific:

- ``hook_claude.py`` adapts Claude Code hook payloads and environment values.
- ``hook_codex.py`` adapts Codex hook payloads and environment values.

This module contains only host-neutral workflow behavior such as workflow
policy text, issue-cache injection, provider cache projection checks, and
session-state coordination. Runtime-specific entry scripts parse their payloads, resolve
runtime values, and call the plain functions here with concrete arguments.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_command import CommandRunner  # noqa: E402
from workflow_edit_target import EditTarget  # noqa: E402
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_github import GitHubRepository, GitHubRepositoryError, normalize_issue_number  # noqa: E402
from workflow_github import resolve_github_repository  # noqa: E402
from workflow_issue_cache import cache_issue_references  # noqa: E402
from workflow_issue_cache import extract_issue_numbers, format_issue_cache_context  # noqa: E402
from workflow_jira import normalize_jira_issue_key  # noqa: E402
from workflow_session_state import (  # noqa: E402
    commit_prefix_was_announced,
    read_session_issues,
    record_commit_prefix_announced,
    record_session_issues,
)
from util import emit_json  # noqa: E402

COMMIT_PROMPT_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z])(?:commit|commits|committed|committing)(?![A-Za-z])|커밋"
)

# =============================================================================
# Common hook operations
# =============================================================================


def workflow_config_for_project(project_dir: Path | None) -> WorkflowConfig | None:
    """Resolve the active workflow config, silent on missing project or load errors."""

    if project_dir is None:
        return None
    try:
        return load_workflow_config(project_dir)
    except WorkflowConfigError:
        return None


def block_provider_cache_body_write(
    *,
    project_dir: Path | None,
    edit_targets: tuple[EditTarget, ...],
    stdout: TextIO | None = None,
) -> int:
    """Block unsafe provider cache issue body projection writes."""

    config = workflow_config_for_project(project_dir)
    if config is None:
        return 0

    for target in edit_targets:
        block_reason = provider_cache_body_write_reason(target, config)
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
    if config is None or config.issues.kind not in {"github", "jira"}:
        return 0

    context_parts: list[str] = []
    commit_context = build_prompt_commit_context(config, prompt_text)
    if commit_context and commit_prefix_was_announced(config.root, session_id):
        commit_context = ""

    repo = None
    if config.issues.kind == "github":
        repo = github_repo_for_config(config, runner=runner)
        if repo is None:
            if commit_context:
                record_commit_prefix_announced(config.root, session_id)
                emit_user_prompt_context([commit_context], stdout=stdout)
            return 0

    prompt_numbers = extract_issue_numbers(
        prompt_text,
        repo=repo,
        issue_id_format=config.issue_id_format,
    )
    issue_numbers = _ordered_issue_union(prompt_numbers, issue_id_format=config.issue_id_format)
    if not issue_numbers:
        if commit_context:
            record_commit_prefix_announced(config.root, session_id)
            emit_user_prompt_context([commit_context], stdout=stdout)
        return 0

    already_announced = read_session_issues(config.root, session_id, "announced")
    contexts = cache_issue_references(config, issue_numbers, repo=repo, runner=runner)
    fresh_contexts = [context for context in contexts if context.number not in already_announced]
    if fresh_contexts:
        record_session_issues(
            config.root,
            session_id,
            [context.number for context in fresh_contexts],
            "announced",
        )
        context_parts.append(format_issue_cache_context(fresh_contexts, include_details=False))
    if commit_context:
        context_parts.append(commit_context)
    if context_parts:
        if commit_context:
            record_commit_prefix_announced(config.root, session_id)
        emit_user_prompt_context(context_parts, stdout=stdout)
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
    """Keep Stop silent and avoid carrying issue refs into the next prompt."""

    # Stop hook JSON output is reserved for block decisions. Provider/cache
    # context injection is prompt-local only.
    _ = project_dir, session_id, scan_text, stop_hook_active, stdout, runner
    return 0


# =============================================================================
# Module-level helpers used by the handlers
# =============================================================================


def build_session_start_context(config: WorkflowConfig, plugin_root: Path) -> str:
    """Build the context block injected for configured workflow projects."""

    _ = plugin_root  # plugin_root reserved for future template extensions
    lines = [
        "## workflow policy",
        "",
        "Before editing a workflow issue or knowledge document, ask `workflow-operator` "
        "for the required authoring paths, then read those files locally before drafting "
        "or editing content.",
        "For workflow issues, draft or edit title/body/labels locally. After local "
        "draft/edit content is complete, tell `workflow-operator`; it will publish "
        "and verify provider updates.",
        "For new workflow issues, stop at the pending draft until the user explicitly "
        "approves provider issue creation.",
    ]
    if config.knowledge.kind == "github":
        lines.append(
            "For GitHub-backed knowledge documents, choose a target Markdown file under "
            "`wiki/`, ask `workflow-operator` for authoring paths with the document type "
            "and `knowledge` role, then edit the file directly in the working tree."
        )
    return "\n".join(lines)


def build_prompt_commit_context(config: WorkflowConfig, prompt_text: str) -> str:
    """Build terse commit guidance when a user prompt asks about commits."""

    if not config.commit_refs.enabled:
        return ""
    if not COMMIT_PROMPT_PATTERN.search(prompt_text):
        return ""
    if config.issues.kind not in {"github", "jira"}:
        return ""
    return "\n".join(
        [
            "## Workflow commit",
            "",
            "Handle staging, commit message authoring, and commit execution in the main assistant.",
            "Prefix the subject with the related issue ref.",
        ]
    )


def emit_user_prompt_context(context_parts: list[str], *, stdout: TextIO | None = None) -> None:
    """Emit a single UserPromptSubmit additionalContext payload."""

    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(part for part in context_parts if part),
            }
        },
        stdout=stdout,
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


def is_provider_issue_cache_body(path: Path, config: WorkflowConfig) -> bool:
    """Return whether ``path`` is a provider issue body cache projection."""

    if config.issues.kind not in {"github", "jira"} or path.name != "issue.md":
        return False
    try:
        parts = path.expanduser().resolve(strict=False).relative_to(
            config.root / ".workflow-cache"
        ).parts
    except ValueError:
        return False

    if config.issues.kind == "github" and len(parts) == 3:
        return parts[0] in {"issues", "issues-pending"}
    if config.issues.kind == "github" and len(parts) == 6:
        return parts[3] in {"issues", "issues-pending"}
    if config.issues.kind == "jira" and len(parts) == 5:
        return parts[0] == "jira" and parts[2] == "issues-pending"
    return False


def provider_cache_body_write_reason(target: EditTarget, config: WorkflowConfig) -> str | None:
    """Block provider cache body writes that create or alter provider metadata."""

    if not is_provider_issue_cache_body(target.path, config):
        return None

    if not target.path.is_file():
        return (
            "workflow cache protection blocked a provider cache issue body write "
            "because the projection has not been prepared yet.\n\n"
            f"Target: {target.path}\n\n"
            "Ask `workflow-operator` to prepare or refresh the cache projection, "
            "then edit only the Markdown body below the existing YAML frontmatter."
        )

    if target.content is None:
        return None

    try:
        current_content = target.path.read_text(encoding="utf-8")
    except OSError as exc:
        return (
            "workflow cache protection blocked a provider cache issue body write "
            "because the existing projection could not be read.\n\n"
            f"Target: {target.path}\n"
            f"Reason: {exc}"
        )

    current_frontmatter = leading_frontmatter_block(current_content)
    proposed_frontmatter = leading_frontmatter_block(target.content)
    if current_frontmatter is None:
        return (
            "workflow cache protection blocked a provider cache issue body write "
            "because the existing projection is missing provider frontmatter.\n\n"
            f"Target: {target.path}\n\n"
            "Ask `workflow-operator` to refresh the cache projection before editing."
        )
    if proposed_frontmatter != current_frontmatter:
        return (
            "workflow cache protection blocked a provider cache issue body write "
            "because provider frontmatter is projection-owned.\n\n"
            f"Target: {target.path}\n\n"
            "Keep the existing YAML frontmatter byte-for-byte and edit only the "
            "Markdown body below it. Ask `workflow-operator` to prepare or refresh "
            "the projection when provider metadata needs to change."
        )

    return None


def leading_frontmatter_block(content: str) -> str | None:
    """Return the leading YAML frontmatter block, including delimiters."""

    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            return "".join(lines[: index + 1])
    return None


def _ordered_issue_union(*groups: list[str], issue_id_format: str = "github") -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for issue in group:
            normalized = _normalize_issue_token(issue, issue_id_format=issue_id_format)
            if normalized is None:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def _normalize_issue_token(issue: str, *, issue_id_format: str) -> str | None:
    try:
        if issue_id_format == "jira":
            return normalize_jira_issue_key(issue)
        return normalize_issue_number(issue)
    except Exception:
        return None
