#!/usr/bin/env python3
"""Workflow hook dispatcher.

SessionStart injects a concise workflow authoring policy only when the active
project has a valid ``.workflow/config.yml``. The hook never starts workflow
skills and never blocks session startup.
"""

from __future__ import annotations

import json
import os
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
from workflow_cache import CACHE_ROOT_NAME, GitHubIssueCache  # noqa: E402
from workflow_command import CommandRunner  # noqa: E402
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_github import GitHubRepository, GitHubRepositoryError, normalize_issue_number  # noqa: E402
from workflow_github import resolve_github_repository  # noqa: E402
from workflow_providers import CACHE_POLICY_DEFAULT, ProviderDispatcher, default_provider_registry  # noqa: E402
from workflow_providers import request_from_config  # noqa: E402

RUNTIME_ENV_VAR = "WORKFLOW_HOOK_RUNTIME"
STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"
CLAUDE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
MAX_ISSUE_REFS = 20
HOOK_STATE_DIR_NAME = "hook-state"

ISSUE_HASH_RE = re.compile(r"(?<![\w#])#([1-9]\d*)\b")
ISSUE_REPO_RE = re.compile(
    r"(?<![\w/.-])(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)#(?P<num>[1-9]\d*)\b",
    re.IGNORECASE,
)
ISSUE_URL_RE = re.compile(
    r"https?://(?P<host>[^/\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/(?P<num>[1-9]\d*)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EditTarget:
    """Potential local workflow write target."""

    path: Path
    content: str | None = None


@dataclass(frozen=True)
class ArtifactMetadata:
    """Workflow artifact metadata inferred from local projection content."""

    artifact_type: str
    role: str | None = None
    provider: str | None = None


@dataclass(frozen=True)
class IssueCacheContext:
    """Concise hook context for one cache-aware GitHub issue read."""

    number: str
    relative_issue_dir: str
    title: str
    state: str
    cache_hit: bool | None = None


def session_start(payload: dict[str, Any] | None = None, *, stdout: TextIO | None = None) -> int:
    """SessionStart entry point. Always exits 0."""

    if payload is None:
        payload = _read_payload()
    output = stdout or sys.stdout

    project_dir = project_dir_from_payload(payload)
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0

    if config is None:
        return 0

    plugin_root = plugin_root_from_payload(payload)
    context = build_session_start_context(config, plugin_root)
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
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

    if payload is None:
        payload = _read_payload()
    project_dir = project_dir_from_payload(payload)
    session_id = session_id_from_payload(payload)
    if project_dir is None or not session_id:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    target = read_target_from_payload(payload)
    if target is None:
        return 0

    plugin_root = plugin_root_from_payload(payload)
    authoring_file = workflow_authoring_file(target, plugin_root)
    if authoring_file is None:
        return 0

    try:
        record_reads(
            [authoring_file],
            project=config.root,
            session_id=session_id,
            state_dir=state_dir_from_env(state_dir),
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

    if payload is None:
        payload = _read_payload()
    output = stdout or sys.stdout

    project_dir = project_dir_from_payload(payload)
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

    session_id = session_id_from_payload(payload)
    pending_numbers = sorted(read_session_issues(config.root, session_id, "pending"), key=int)
    issue_numbers = _ordered_issue_union(
        pending_numbers,
        extract_issue_numbers(
            prompt_from_payload(payload),
            repo=repo,
            issue_id_format=config.issue_id_format,
        ),
    )
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
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_issue_cache_context(fresh_contexts),
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

    if payload is None:
        payload = _read_payload()
    if payload.get("stop_hook_active") is True:
        return 0
    # Stop hook JSON output is reserved for block decisions. Context injection
    # happens in UserPromptSubmit so Stop can never fail host output validation.
    _ = stdout

    project_dir = project_dir_from_payload(payload)
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

    session_id = session_id_from_payload(payload)
    issue_numbers = sorted(read_session_issues(config.root, session_id, "mentioned"), key=int)
    for number in extract_issue_numbers(
        text_from_payload(payload),
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

    if payload is None:
        payload = _read_payload()
    output = stdout or sys.stdout

    project_dir = project_dir_from_payload(payload)
    session_id = session_id_from_payload(payload)
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
        for target in edit_targets_from_payload(payload)
        if is_markdown_path(target.path) and is_under_any(target.path, roots)
    ]
    if not targets:
        return 0

    for target in targets:
        block_reason = local_projection_guard_reason(
            target,
            config=config,
            session_id=session_id,
            state_dir=state_dir_from_env(state_dir),
        )
        if block_reason:
            emit({"decision": "block", "reason": block_reason}, stdout=output)
            return 0

    return 0


def build_session_start_context(config: WorkflowConfig, plugin_root: Path) -> str:
    """Build the context block injected for configured workflow projects."""

    resolver = "scripts/authoring_resolver.py"
    ledger = "scripts/authoring_ledger.py"
    guard = "scripts/authoring_guard.py"

    commit_ref = "disabled"
    if config.commit_refs.enabled:
        commit_ref = config.commit_refs.style

    cache_context = build_cache_session_context(config)

    return (
        "## workflow authoring policy\n\n"
        f"Configured workflow project: `{config.root}`\n"
        f"Config file: `{config.path}`\n"
        f"Workflow plugin root: `{plugin_root}`\n"
        f"Issue provider: `{config.issues.kind}`\n"
        f"Issue ID format: `{config.issue_id_format}`\n"
        f"Knowledge provider: `{config.knowledge.kind}`\n"
        f"Local projection: `{config.local_projection.mode}`\n"
        f"Commit references: `{commit_ref}`\n\n"
        "Before creating or editing any workflow issue, knowledge artifact, "
        "or local projection, resolve and read the required authoring contracts.\n\n"
        "Resolver command:\n\n"
        "```bash\n"
        f'WORKFLOW_PLUGIN_ROOT="{plugin_root}"\n'
        f'python3 "$WORKFLOW_PLUGIN_ROOT/{resolver}" --project "{config.root}" --type <artifact-type> '
        "[--role issue|knowledge] --json\n"
        "```\n\n"
        "Use `--role issue` or `--role knowledge` for dual artifacts such as "
        "`usecase` and `research`.\n\n"
        "The resolver JSON contains `required_authoring_files`, and every path "
        "in that list is absolute. Read every listed file before writing.\n\n"
        "When a wrapper or hook requires ledger enforcement, record reads with:\n\n"
        "```bash\n"
        f'WORKFLOW_PLUGIN_ROOT="{plugin_root}"\n'
        f'python3 "$WORKFLOW_PLUGIN_ROOT/{ledger}" --project "{config.root}" --session <session-id> '
        "record --json <absolute-authoring-file>...\n"
        "```\n\n"
        "Check write readiness with:\n\n"
        "```bash\n"
        f'WORKFLOW_PLUGIN_ROOT="{plugin_root}"\n'
        f'python3 "$WORKFLOW_PLUGIN_ROOT/{guard}" --project "{config.root}" --session <session-id> '
        "--type <artifact-type> [--role issue|knowledge] --json\n"
        "```\n\n"
        "SessionStart only injects this policy and cache context. It does not "
        "auto-trigger workflow skills."
        f"{cache_context}"
    )


def build_cache_session_context(config: WorkflowConfig) -> str:
    """Build SessionStart guidance for workflow provider read caches."""

    cache_root = GitHubIssueCache.for_project(config.root).root
    cache_root_display = display_project_path(cache_root, config.root, trailing_slash=True)
    lines = [
        "",
        "",
        "## workflow provider cache context",
        "",
        f"Workflow cache root: `{cache_root_display}`",
    ]

    repo = github_repo_for_config(config)
    if repo is not None:
        issue_base = github_issue_cache_base(config, repo)
        issue_base_display = display_project_path(issue_base, config.root, trailing_slash=True)
        lines.extend(
            [
                f"GitHub issue cache base: `{issue_base_display}`",
                "",
                "Hook-reported issue cache paths are relative to the GitHub issue "
                "cache base unless another base is explicitly stated.",
            ]
        )
    else:
        lines.append("")

    lines.extend(
        [
            "UserPromptSubmit may pre-read mentioned issue references through "
            "cache-aware provider reads and inject concise additionalContext.",
            "Stop may record session-mentioned issue references as pending; "
            "the next UserPromptSubmit performs provider reads and cache-path "
            "context injection.",
            "Use hook-provided issue context before ad hoc reads.",
            f"Do not inspect `{CACHE_ROOT_NAME}` directly unless the user explicitly "
            "asks to debug cache contents, layout, or invalidation.",
        ]
    )
    return "\n".join(lines)


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


def github_issue_cache_base(config: WorkflowConfig, repo: GitHubRepository) -> Path:
    """Return the issue-number parent directory for the configured repo cache."""

    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    return cache.issue_dir(repo, "1").parent


def cache_issue_references(
    config: WorkflowConfig,
    issue_numbers: list[str],
    *,
    repo: GitHubRepository,
    runner: CommandRunner | None = None,
) -> list[IssueCacheContext]:
    """Read issues through the provider cache path and return hook context."""

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    issue_base = github_issue_cache_base(config, repo)
    contexts: list[IssueCacheContext] = []

    for number in issue_numbers:
        try:
            normalized = normalize_issue_number(number)
            request = request_from_config(
                config,
                role="issue",
                operation="get",
                artifact_type="task",
                payload={
                    "issue": normalized,
                    "include_body": False,
                    "include_comments": False,
                    "include_relationships": False,
                },
                cache_policy=CACHE_POLICY_DEFAULT,
            )
            response = dispatcher.dispatch(request)
            issue_dir = cache.issue_dir(repo, normalized)
            relative_issue_dir = issue_dir.relative_to(issue_base).as_posix() + "/"
            contexts.append(
                IssueCacheContext(
                    number=normalized,
                    relative_issue_dir=relative_issue_dir,
                    title=str(response.payload.get("title") or ""),
                    state=str(response.payload.get("state") or ""),
                    cache_hit=cache_hit_from_payload(response.payload),
                )
            )
        except Exception:
            continue

    return contexts


def cache_hit_from_payload(payload: Mapping[str, Any]) -> bool | None:
    cache_data = payload.get("cache")
    if isinstance(cache_data, Mapping):
        hit = cache_data.get("hit")
        if isinstance(hit, bool):
            return hit
    return None


def format_issue_cache_context(contexts: list[IssueCacheContext]) -> str:
    """Render issue cache context using issue-cache-base-relative paths."""

    lines = ["Workflow issue cache:"]
    for context in contexts:
        details: list[str] = []
        state = context.state.strip()
        if state:
            details.append(state.lower())
        title = compact_title(context.title)
        if title:
            details.append(title)
        suffix = f" — {' — '.join(details)}" if details else ""
        lines.append(f"- #{context.number} → `{context.relative_issue_dir}`{suffix}")
    return "\n".join(lines)


def compact_title(value: str, *, limit: int = 96) -> str:
    title = " ".join(value.split())
    if len(title) <= limit:
        return title
    return title[: limit - 1].rstrip() + "…"


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


def extract_issue_numbers(
    text: str,
    *,
    repo: GitHubRepository | None = None,
    issue_id_format: str = "github",
) -> list[str]:
    """Extract same-repository issue references in first-seen order."""

    if issue_id_format != "github":
        return []

    numbers: list[str] = []
    seen: set[str] = set()
    candidates: list[tuple[int, str]] = []

    def add(raw: str) -> None:
        if len(numbers) >= MAX_ISSUE_REFS:
            return
        try:
            normalized = normalize_issue_number(raw)
        except Exception:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        numbers.append(normalized)

    for match in ISSUE_URL_RE.finditer(text):
        if repo is not None and not _same_github_repo(
            repo,
            host=match.group("host"),
            owner=match.group("owner"),
            repo_name=match.group("repo"),
        ):
            continue
        candidates.append((match.start(), match.group("num")))

    for match in ISSUE_REPO_RE.finditer(text):
        if repo is not None and not _same_github_repo(
            repo,
            host=repo.host,
            owner=match.group("owner"),
            repo_name=match.group("repo"),
        ):
            continue
        candidates.append((match.start(), match.group("num")))

    for match in ISSUE_HASH_RE.finditer(text):
        candidates.append((match.start(), match.group(1)))

    for _, raw in sorted(candidates, key=lambda item: item[0]):
        add(raw)

    return numbers


def _same_github_repo(
    repo: GitHubRepository,
    *,
    host: str,
    owner: str,
    repo_name: str,
) -> bool:
    return (
        host.lower(),
        owner.lower(),
        repo_name.removesuffix(".git").lower(),
    ) == (
        repo.host.lower(),
        repo.owner.lower(),
        repo.name.lower(),
    )


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


def display_project_path(path: Path, project: Path, *, trailing_slash: bool = False) -> str:
    resolved = path.expanduser().resolve(strict=False)
    try:
        display = resolved.relative_to(project.expanduser().resolve(strict=False)).as_posix()
    except ValueError:
        display = str(resolved)
    if trailing_slash and not display.endswith("/"):
        display += "/"
    return display


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


def project_dir_from_payload(payload: dict[str, Any]) -> Path | None:
    """Resolve the active project directory from host-specific hook inputs."""

    runtime = hook_runtime(payload)
    if runtime == "claude":
        project_env = os.environ.get("CLAUDE_PROJECT_DIR")
        if project_env:
            return Path(project_env).expanduser().resolve()

    cwd = payload.get("cwd") or os.getcwd()
    if not isinstance(cwd, str) or not cwd:
        return None

    cwd_path = Path(cwd).expanduser().resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd_path), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return cwd_path

    root = proc.stdout.strip()
    if not root:
        return cwd_path
    return Path(root).expanduser().resolve()


def plugin_root_from_payload(payload: dict[str, Any]) -> Path:
    """Resolve the workflow plugin root from host-specific adapter inputs."""

    runtime = hook_runtime(payload)
    env_names = ("CLAUDE_PLUGIN_ROOT",) if runtime == "claude" else ("PLUGIN_ROOT",)
    for env_name in env_names:
        explicit = os.environ.get(env_name)
        if explicit:
            return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def session_id_from_payload(payload: dict[str, Any]) -> str:
    for key in ("session_id", "turn_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def hook_runtime(payload: dict[str, Any]) -> str:
    runtime = os.environ.get(RUNTIME_ENV_VAR, "").strip().lower()
    if runtime in {"claude", "codex"}:
        return runtime
    if payload.get("turn_id"):
        return "codex"
    return "unknown"


def read_target_from_payload(payload: dict[str, Any]) -> Path | None:
    if payload.get("tool_name") != "Read":
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not isinstance(file_path, str) or not file_path:
        return None
    project_dir = project_dir_from_payload(payload)
    return resolve_payload_path(file_path, payload, project_dir)


def edit_targets_from_payload(payload: dict[str, Any]) -> tuple[EditTarget, ...]:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ()

    if tool_name in CLAUDE_EDIT_TOOLS:
        file_path = tool_input.get("file_path") or ""
        if not isinstance(file_path, str) or not file_path:
            return ()
        path = resolve_payload_path(file_path, payload, project_dir_from_payload(payload))
        content = tool_input.get("content") if tool_name == "Write" else None
        if not isinstance(content, str):
            content = None
        return (EditTarget(path=path, content=content),)

    if tool_name == "apply_patch":
        command = tool_input.get("command") or ""
        if not isinstance(command, str) or not command:
            return ()
        return apply_patch_targets(command, payload)

    return ()


def apply_patch_targets(command: str, payload: dict[str, Any]) -> tuple[EditTarget, ...]:
    project_dir = project_dir_from_payload(payload)
    out: list[EditTarget] = []
    seen: set[Path] = set()
    current_path: Path | None = None
    current_added: list[str] | None = None

    def flush_add() -> None:
        nonlocal current_path, current_added
        if current_path is None or current_added is None:
            return
        if current_path not in seen:
            seen.add(current_path)
            out.append(EditTarget(path=current_path, content="\n".join(current_added) + "\n"))
        current_path = None
        current_added = None

    for line in command.splitlines():
        if line.startswith("*** Add File: "):
            flush_add()
            raw_path = line.removeprefix("*** Add File: ").strip()
            current_path = resolve_payload_path(raw_path, payload, project_dir)
            current_added = []
            continue

        if line.startswith("*** Update File: ") or line.startswith("*** Delete File: "):
            flush_add()
            raw_path = line.split(": ", 1)[1].strip()
            path = resolve_payload_path(raw_path, payload, project_dir)
            if path not in seen:
                seen.add(path)
                out.append(EditTarget(path=path))
            continue

        if line.startswith("*** Move to: "):
            raw_path = line.removeprefix("*** Move to: ").strip()
            path = resolve_payload_path(raw_path, payload, project_dir)
            if path not in seen:
                seen.add(path)
                out.append(EditTarget(path=path))
            continue

        if line.startswith("*** ") and current_added is not None:
            flush_add()
            continue

        if current_added is not None and line.startswith("+"):
            current_added.append(line[1:])

    flush_add()
    return tuple(out)


def resolve_payload_path(
    raw_path: str,
    payload: dict[str, Any],
    project_dir: Path | None,
) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve(strict=False)

    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        base = Path(cwd).expanduser()
    elif project_dir is not None:
        base = project_dir
    else:
        base = Path.cwd()
    return (base / path).resolve(strict=False)


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


def state_dir_from_env(state_dir: Path | None) -> Path | None:
    if state_dir is not None:
        return state_dir.resolve()
    explicit = os.environ.get(STATE_DIR_ENV_VAR)
    if explicit:
        return Path(explicit).expanduser().resolve()
    return None


def emit(payload: dict[str, Any], *, stdout: TextIO | None = None) -> None:
    output = stdout or sys.stdout
    json.dump(payload, output, ensure_ascii=False)
    output.write("\n")


def _read_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


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
