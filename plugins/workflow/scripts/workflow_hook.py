#!/usr/bin/env python3
"""Workflow hook dispatcher.

SessionStart injects a concise workflow routing policy only for main sessions
when the active project has a valid ``.workflow/config.yml``. The policy is
intentionally narrow: it announces that the project is workflow-configured,
names the issue provider, and tells the main assistant to delegate workflow
operations to the ``workflow-operator`` agent. Detailed authoring resolver,
ledger, guard, and script command syntax live in the operator's own prompt.

For ``workflow-operator`` subagent invocations, the dispatcher emits the parent
session id as ``additionalContext`` so the operator binds its ledger and guard
lookups to the main session's read history. In Claude that injection rides on
``SubagentStart`` (matcher ``workflow-operator``); Codex has no SubagentStart
event, so the equivalent path lives inside ``SessionStart`` and extracts the
parent thread id from the subagent transcript when the operator session starts.

The hook never starts workflow skills and never blocks session startup.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from authoring_guard import evaluate_authoring_guard  # noqa: E402
from authoring_ledger import LedgerError, record_reads  # noqa: E402
from authoring_resolver import ALL_TYPES, DUAL_TYPES, ResolverError  # noqa: E402
from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_command import CommandRunner  # noqa: E402
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_github import GitHubRepository, GitHubRepositoryError, normalize_issue_number  # noqa: E402
from workflow_github import resolve_github_repository  # noqa: E402
from workflow_hook_context import EditTarget, HookContext  # noqa: E402
from workflow_issue_cache import cache_issue_references  # noqa: E402
from workflow_issue_cache import extract_issue_numbers, format_issue_cache_context  # noqa: E402
from workflow_operator_context import (  # noqa: E402
    agent_name_matches_operator,
    build_operator_subagent_context,
)

HOOK_STATE_DIR_NAME = "hook-state"


@dataclass(frozen=True)
class ArtifactMetadata:
    """Workflow artifact metadata inferred from local projection content."""

    artifact_type: str
    role: str | None = None
    provider: str | None = None


def session_start(payload: dict[str, Any] | None = None, *, stdout: TextIO | None = None) -> int:
    """SessionStart entry point. Always exits 0."""

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    output = stdout or sys.stdout
    if ctx.is_agent_session():
        return _emit_codex_operator_session(ctx, output)

    project_dir = ctx.project_dir()
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0

    if config is None:
        return 0

    session_id = ctx.session_id()
    if ctx.should_skip_session_start_policy():
        return 0
    if not ctx.should_reinject_session_policy() and session_policy_was_announced(
        config.root,
        ctx.runtime,
        session_id,
    ):
        return 0

    plugin_root = ctx.plugin_root()
    context = build_session_start_context(config, plugin_root)
    ctx.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
    record_session_policy_announced(config.root, ctx.runtime, session_id)
    return 0


def post_read(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Record reads of plugin-bundled workflow authoring files.

    The hook is silent on success and on non-workflow projects.
    """

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    project_dir = ctx.project_dir()
    session_id = ctx.session_id()
    if project_dir is None or not session_id:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    target = ctx.read_target()
    if target is None:
        return 0

    plugin_root = ctx.plugin_root()
    authoring_file = workflow_authoring_file(target, plugin_root)
    if authoring_file is None:
        return 0

    try:
        record_reads(
            [authoring_file],
            project=config.root,
            session_id=session_id,
            state_dir=ctx.state_dir(state_dir),
            require_config=True,
        )
    except LedgerError:
        return 0

    # `stdout` is accepted for a uniform test signature. Successful read
    # recording intentionally emits no hook context.
    _ = stdout
    return 0


def user_prompt_submit(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Cache issue references from a user prompt and inject concise context."""

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    output = stdout or sys.stdout

    project_dir = ctx.project_dir()
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None or config.issues.kind != "github":
        return 0

    repo = github_repo_for_config(config, runner=runner)
    if repo is None:
        return 0

    session_id = ctx.session_id()
    prompt_numbers = extract_issue_numbers(
        prompt_from_payload(ctx.payload),
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
        remove_session_issues(config.root, session_id, [context.number for context in contexts], "pending")
    if not fresh_contexts:
        return 0

    record_session_issues(config.root, session_id, [context.number for context in fresh_contexts], "announced")
    ctx.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_issue_cache_context(fresh_contexts, include_details=False),
            }
        },
        stdout=output,
    )
    return 0


def stop(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Record issue references known to the session before stopping."""

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    if ctx.payload.get("stop_hook_active") is True:
        return 0
    # Stop hook JSON output is reserved for block decisions. Context injection
    # happens in UserPromptSubmit so Stop can never fail host output validation.
    _ = stdout

    project_dir = ctx.project_dir()
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None or config.issues.kind != "github":
        return 0

    repo = github_repo_for_config(config, runner=runner)
    if repo is None:
        return 0

    session_id = ctx.session_id()
    issue_numbers = sorted(read_session_issues(config.root, session_id, "mentioned"), key=int)
    for number in extract_issue_numbers(
        text_from_payload(ctx.payload),
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


def pre_write(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Block local projection writes until required authoring files were read."""

    ctx = HookContext.from_payload(payload) if payload is not None else HookContext.from_stdin()
    output = stdout or sys.stdout

    project_dir = ctx.project_dir()
    session_id = ctx.session_id()
    if project_dir is None or not session_id:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    roots = local_workflow_roots(config)
    if not roots:
        return 0

    targets = [
        target
        for target in ctx.edit_targets()
        if is_markdown_path(target.path) and is_under_any(target.path, roots)
    ]
    if not targets:
        return 0

    for target in targets:
        block_reason = local_projection_guard_reason(
            target,
            config=config,
            session_id=session_id,
            state_dir=ctx.state_dir(state_dir),
        )
        if block_reason:
            ctx.emit({"decision": "block", "reason": block_reason}, stdout=output)
            return 0

    return 0


def _emit_codex_operator_session(ctx: HookContext, output: TextIO) -> int:
    """Emit operator subagent context when a codex subagent SessionStart is for workflow-operator.

    Claude SubagentStart already covers the operator path natively (see
    ``workflow_subagent_hook.py``), so this helper restricts injection to
    codex. Non-operator subagents stay silent.
    """

    if ctx.runtime != "codex":
        return 0

    parent_thread_id, agent_name = ctx.subagent_metadata()
    if not parent_thread_id:
        return 0
    if not agent_name_matches_operator(agent_name):
        return 0

    project_dir = ctx.project_dir()
    if project_dir is None:
        return 0
    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    context = build_operator_subagent_context(parent_thread_id, config.root)
    ctx.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
    return 0


def build_session_start_context(config: WorkflowConfig, plugin_root: Path) -> str:
    """Build the context block injected for configured workflow projects."""

    return (
        "## workflow authoring policy\n\n"
        f"This project is configured for the workflow plugin (issue provider: `{config.issues.kind}`). "
        "Delegate workflow operations — provider/cache reads, write-back, comment "
        "append, authoring path discovery, guarded writes — to the "
        "`workflow-operator` agent. Pass workflow intent, issue refs, and "
        "artifact type; the operator picks up the parent session id from its "
        "own start hook and returns provider/cache metadata, issue relationship "
        "metadata, and paths.\n\n"
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
            "running `gh` directly."
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


def prompt_from_payload(payload: dict[str, Any]) -> str:
    for key in ("prompt", "user_prompt", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def text_from_payload(payload: dict[str, Any]) -> str:
    """Collect bounded string content from hook payloads for issue ref scans."""

    chunks: list[str] = []

    def visit(value: Any, *, depth: int = 0) -> None:
        if len(chunks) >= 40 or depth > 5:
            return
        if isinstance(value, str):
            if value:
                chunks.append(value[:4000])
            return
        if isinstance(value, Mapping):
            for item in value.values():
                visit(item, depth=depth + 1)
            return
        if isinstance(value, (list, tuple)):
            for item in value[:40]:
                visit(item, depth=depth + 1)

    visit(payload)
    return "\n".join(chunks)


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


def workflow_hook_state_dir(project: Path) -> Path:
    return GitHubIssueCache.for_project(project).root / HOOK_STATE_DIR_NAME


def issue_state_path(project: Path, session_id: str, kind: str) -> Path | None:
    if not session_id:
        return None
    safe_session = re.sub(r"[^A-Za-z0-9_.-]+", "_", session_id).strip("._-")
    if not safe_session:
        return None
    return workflow_hook_state_dir(project) / f"workflow-{kind}-issues-{safe_session[:120]}.txt"


def session_policy_state_path(project: Path, runtime: str, session_id: str) -> Path | None:
    if not session_id:
        return None
    safe_runtime = re.sub(r"[^A-Za-z0-9_.-]+", "_", runtime).strip("._-") or "unknown"
    safe_session = re.sub(r"[^A-Za-z0-9_.-]+", "_", session_id).strip("._-")
    if not safe_session:
        return None
    return workflow_hook_state_dir(project) / (
        f"workflow-session-policy-{safe_runtime}-{safe_session[:120]}.txt"
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


def record_session_issues(project: Path, session_id: str, issues: list[str], kind: str) -> None:
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


def remove_session_issues(project: Path, session_id: str, issues: list[str], kind: str) -> None:
    path = issue_state_path(project, session_id, kind)
    if path is None or not path.exists():
        return
    remove = set()
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


def is_markdown_path(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".markdown"}


def is_under_any(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve(strict=False)
    return any(is_under(resolved, root) for root in roots)


def is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def infer_artifact_metadata(target: EditTarget) -> ArtifactMetadata | None:
    content = target.content
    if content is None:
        try:
            content = target.path.read_text(encoding="utf-8")
        except OSError:
            content = ""

    values = extract_metadata_values(content)
    artifact_type = values.get("type")
    if artifact_type is None:
        return None

    normalized_type = artifact_type.strip().lower().replace("_", "-")
    if normalized_type == "use-case":
        normalized_type = "usecase"
    if normalized_type not in ALL_TYPES:
        return None

    role = values.get("role")
    provider = values.get("provider")
    if normalized_type in DUAL_TYPES and not role:
        return None

    return ArtifactMetadata(
        artifact_type=normalized_type,
        role=role.strip().lower().replace("_", "-") if role else None,
        provider=provider.strip().lower().replace("_", "-") if provider else None,
    )


def extract_metadata_values(content: str) -> dict[str, str]:
    """Extract simple scalar workflow metadata from Markdown content."""

    lines = content.splitlines()
    metadata_lines: list[str] = []
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            metadata_lines.append(line)
    else:
        for line in lines[:80]:
            stripped = line.strip()
            if stripped.startswith("#"):
                break
            metadata_lines.append(line)

    values: dict[str, str] = {}
    for line in metadata_lines:
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip().lower().replace("-", "_")
        if key not in {"type", "role", "provider"}:
            continue
        value = raw_value.strip().strip("\"'")
        if value:
            values[key] = value
    return values


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        return 0
    if args[0] == "session-start":
        return session_start()
    if args[0] == "post-read":
        return post_read()
    if args[0] == "pre-write":
        return pre_write()
    if args[0] in {"user-prompt", "user-prompt-submit"}:
        return user_prompt_submit()
    if args[0] == "stop":
        return stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
