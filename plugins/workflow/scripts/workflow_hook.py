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
import re
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
from workflow_artifact_metadata import ArtifactMetadata, infer_artifact_metadata  # noqa: E402
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
from util import emit_json, is_markdown_path, is_under, is_under_any  # noqa: E402

STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"
COMMIT_PROMPT_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z])(?:commit|commits|committed|committing)(?![A-Za-z])|커밋"
)

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
    targets = [
        target
        for target in edit_targets
        if is_markdown_path(target.path) and is_local_workflow_write_target(target.path, config, roots)
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
    return (
        "## workflow policy\n\n"
        "Delegate workflow provider/cache/relationship/write-back/comment/authoring-path operations "
        "to `workflow-operator`.\n"
        "For issue create/update flows, ask `workflow-operator` for required authoring paths, "
        "read those docs locally, draft title/body/labels locally, then ask `workflow-operator` "
        "to perform the provider write and refresh/verify cache.\n"
        "Do not run raw provider CLIs directly when the operator can handle the operation."
    )


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


def local_projection_guard_reason(
    target: EditTarget,
    *,
    config: WorkflowConfig,
    session_id: str,
    state_dir: Path | None = None,
) -> str | None:
    """Return a block reason for a local workflow write, or ``None`` to allow."""

    provider_cache_reason = provider_cache_body_write_reason(target, config)
    if provider_cache_reason:
        return provider_cache_reason

    metadata = infer_artifact_metadata(target)
    metadata = enrich_provider_cache_metadata(metadata, target.path, config)
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


def is_local_workflow_write_target(
    path: Path,
    config: WorkflowConfig,
    roots: tuple[Path, ...] | None = None,
) -> bool:
    """Return whether ``path`` is a local workflow artifact body target."""

    if is_under_any(path, roots if roots is not None else local_workflow_roots(config)):
        return True
    return is_provider_issue_cache_body(path, config)


def enrich_provider_cache_metadata(
    metadata: ArtifactMetadata | None,
    path: Path,
    config: WorkflowConfig,
) -> ArtifactMetadata | None:
    """Fill issue role/provider for provider cache body projections."""

    if metadata is None or not is_provider_issue_cache_body(path, config):
        return metadata
    return ArtifactMetadata(
        artifact_type=metadata.artifact_type,
        role=metadata.role or "issue",
        provider=metadata.provider or config.issues.kind,
    )


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
            "workflow authoring guard blocked a provider cache issue body write "
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
            "workflow authoring guard blocked a provider cache issue body write "
            "because the existing projection could not be read.\n\n"
            f"Target: {target.path}\n"
            f"Reason: {exc}"
        )

    current_frontmatter = leading_frontmatter_block(current_content)
    proposed_frontmatter = leading_frontmatter_block(target.content)
    if current_frontmatter is None:
        return (
            "workflow authoring guard blocked a provider cache issue body write "
            "because the existing projection is missing provider frontmatter.\n\n"
            f"Target: {target.path}\n\n"
            "Ask `workflow-operator` to refresh the cache projection before editing."
        )
    if proposed_frontmatter != current_frontmatter:
        return (
            "workflow authoring guard blocked a provider cache issue body write "
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


def local_workflow_roots(config: WorkflowConfig) -> tuple[Path, ...]:
    roots: list[Path] = []

    if config.local_projection.mode != "none" and config.local_projection.path:
        roots.append((config.root / config.local_projection.path).resolve(strict=False))

    for provider in (config.issues, config.knowledge):
        path = provider.settings.get("path")
        if provider.kind == "filesystem" and isinstance(path, str) and path:
            roots.append((config.root / path).resolve(strict=False))

    return tuple(dict.fromkeys(roots))


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
