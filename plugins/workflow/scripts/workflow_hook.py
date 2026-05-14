#!/usr/bin/env python3
"""Workflow hook runtime (library module).

Defines the runtime-bound hook hierarchy (``Hook`` -> ``ClaudeHook`` /
``CodexHook`` / ``UnknownHook``). Each subclass owns the payload/environment
extraction for its host and exposes ``handle_*`` methods that implement the
SessionStart, PostToolUse Read, PreToolUse Write, UserPromptSubmit, Stop, and
SubagentStart events.

Runtime-divergent behavior lives on the concrete subclass:

- ``ClaudeHook.handle_subagent_start`` emits the operator subagent context
  on Claude's dedicated ``SubagentStart`` event.
- ``CodexHook.handle_session_start`` recognizes Codex's combined
  SessionStart-for-subagent path and emits the same operator context when
  the spawned agent is ``workflow-operator``.

Everything runtime-agnostic (workflow policy text, issue-cache injection,
local projection guards, session-state coordination) lives on the ``Hook``
base so both runtimes share one implementation. Module-level
``session_start``/``post_read``/``pre_write``/``user_prompt_submit``/``stop``
functions are thin shims kept for test imports and the runtime entry
scripts (``hook_claude.py`` and ``hook_codex.py``).

This module is import-only; the executable entry points are
``hook_claude.py`` (Claude hook manifest + SubagentStart) and
``hook_codex.py`` (Codex hook manifest).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

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
    record_session_policy_announced,
    remove_session_issues,
    session_policy_was_announced,
)

RUNTIME_ENV_VAR = "WORKFLOW_HOOK_RUNTIME"
STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"
CLAUDE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
CODEX_SESSION_START_SOURCES = {"startup", "resume", "clear"}
CLAUDE_SESSION_START_SOURCES = {"startup", "resume", "clear", "compact"}
_SCAN_TEXT_MAX_CHUNKS = 40
_SCAN_TEXT_MAX_DEPTH = 5
_SCAN_TEXT_CHUNK_LIMIT = 4000
_PAYLOAD_AGENT_BOOL_KEYS = ("is_agent", "is_subagent", "agent_session")
_PAYLOAD_AGENT_STRING_KEYS = (
    "agent_id",
    "agent_name",
    "agent_path",
    "subagent_id",
    "subagent_type",
    "parent_agent_id",
    "parent_session_id",
    "parent_thread_id",
    "parent_conversation_id",
)
_PAYLOAD_AGENT_SOURCE_KEYS = (
    "source",
    "session_type",
    "session_kind",
    "conversation_type",
    "invocation",
    "origin",
)
_AGENT_MARKER_VALUES = {"agent", "subagent", "sub_agent", "child_agent", "spawned_agent"}
_TRANSCRIPT_AGENT_KEYS = {
    "agent",
    "agent_id",
    "agent_name",
    "agent_nickname",
    "agent_path",
    "agent_role",
    "parent_thread_id",
    "subagent",
    "thread_spawn",
}


# =============================================================================
# Hook hierarchy
# =============================================================================


class Hook(ABC):
    """Runtime-bound hook executor.

    A ``Hook`` owns one hook invocation: the payload, the runtime-specific
    payload/env extraction, and the handler methods for every supported
    event. Concrete subclasses (``ClaudeHook``, ``CodexHook``,
    ``UnknownHook``) implement only what diverges between runtimes; the
    workflow business logic lives in the base.
    """

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload: dict[str, Any] = dict(payload)

    # ----- runtime identity -----

    @property
    @abstractmethod
    def runtime(self) -> str:
        ...

    # ----- runtime-aware extraction -----

    @abstractmethod
    def project_dir(self) -> Path | None:
        ...

    @abstractmethod
    def plugin_root(self) -> Path:
        ...

    @abstractmethod
    def session_id(self) -> str:
        ...

    @abstractmethod
    def is_agent_session(self) -> bool:
        ...

    @abstractmethod
    def edit_targets(self) -> tuple[EditTarget, ...]:
        ...

    @abstractmethod
    def read_target(self) -> Path | None:
        ...

    @abstractmethod
    def session_start_source(self) -> str:
        ...

    # ----- shared utilities -----

    def should_reinject_session_policy(self) -> bool:
        return self.session_start_source() == "clear"

    def should_skip_session_start_policy(self) -> bool:
        if self.session_start_source() != "compact":
            return False
        return self.runtime in {"claude", "unknown"}

    def resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path.resolve(strict=False)

        cwd = self.payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            base = Path(cwd).expanduser()
        else:
            project = self.project_dir()
            base = project if project is not None else Path.cwd()
        return (base / path).resolve(strict=False)

    def state_dir(self, override: Path | None = None) -> Path | None:
        if override is not None:
            return override.resolve()
        explicit = os.environ.get(STATE_DIR_ENV_VAR)
        if explicit:
            return Path(explicit).expanduser().resolve()
        return None

    def emit(self, payload: dict[str, Any], *, stdout: TextIO | None = None) -> None:
        output = stdout or sys.stdout
        json.dump(payload, output, ensure_ascii=False)
        output.write("\n")

    def workflow_config(self) -> WorkflowConfig | None:
        """Resolve the active workflow config, silent on missing project or load errors."""

        project_dir = self.project_dir()
        if project_dir is None:
            return None
        try:
            return load_workflow_config(project_dir)
        except WorkflowConfigError:
            return None

    def user_prompt_text(self) -> str:
        """Return the first non-empty user-prompt-shaped string in the payload."""

        for key in ("prompt", "user_prompt", "message"):
            value = _string(self.payload, key)
            if value:
                return value
        return ""

    def scan_text(self) -> str:
        """Collect bounded string content from the payload for issue-ref scans."""

        chunks: list[str] = []

        def visit(value: Any, *, depth: int = 0) -> None:
            if len(chunks) >= _SCAN_TEXT_MAX_CHUNKS or depth > _SCAN_TEXT_MAX_DEPTH:
                return
            if isinstance(value, str):
                if value:
                    chunks.append(value[:_SCAN_TEXT_CHUNK_LIMIT])
                return
            if isinstance(value, Mapping):
                for item in value.values():
                    visit(item, depth=depth + 1)
                return
            if isinstance(value, (list, tuple)):
                for item in value[:_SCAN_TEXT_MAX_CHUNKS]:
                    visit(item, depth=depth + 1)

        visit(self.payload)
        return "\n".join(chunks)

    def subagent_metadata(self) -> tuple[str, str | None]:
        """Return (parent_thread_id, agent_name) from a subagent transcript.

        Only ``CodexHook`` populates this — Codex is the runtime that surfaces
        subagent metadata through ``transcript_path``.
        """

        return "", None

    # ----- factories -----

    @classmethod
    def from_stdin(cls) -> "Hook":
        return _hook_for_payload(_read_stdin_json())

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "Hook":
        return _hook_for_payload(payload)

    @classmethod
    def from_payload_or_stdin(cls, payload: Mapping[str, Any] | None) -> "Hook":
        if payload is None:
            return cls.from_stdin()
        return cls.from_payload(payload)

    # ----- event handlers -----

    def handle_session_start(self, *, stdout: TextIO | None = None) -> int:
        """SessionStart event: dispatch subagent path or inject workflow policy."""

        output = stdout or sys.stdout
        if self.is_agent_session():
            return self._handle_agent_session_start(stdout=output)

        config = self.workflow_config()
        if config is None:
            return 0

        session_id = self.session_id()
        if self.should_skip_session_start_policy():
            return 0
        if not self.should_reinject_session_policy() and session_policy_was_announced(
            config.root,
            self.runtime,
            session_id,
        ):
            return 0

        plugin_root = self.plugin_root()
        context = build_session_start_context(config, plugin_root)
        self.emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            },
            stdout=output,
        )
        record_session_policy_announced(config.root, self.runtime, session_id)
        return 0

    def _handle_agent_session_start(self, *, stdout: TextIO | None = None) -> int:
        """Subagent SessionStart no-op default.

        Claude does not fire SessionStart for subagents, so this never runs in
        real Claude usage; tests that exercise the path still expect silence.
        ``CodexHook`` overrides to emit operator context when the spawned
        agent is ``workflow-operator``.
        """

        _ = stdout
        return 0

    def handle_post_read(
        self,
        *,
        stdout: TextIO | None = None,
        state_dir: Path | None = None,
    ) -> int:
        """PostToolUse Read event: record reads of bundled authoring files."""

        session_id = self.session_id()
        if not session_id:
            return 0
        config = self.workflow_config()
        if config is None:
            return 0

        target = self.read_target()
        if target is None:
            return 0

        authoring_file = workflow_authoring_file(target, self.plugin_root())
        if authoring_file is None:
            return 0

        try:
            record_reads(
                [authoring_file],
                project=config.root,
                session_id=session_id,
                state_dir=self.state_dir(state_dir),
                require_config=True,
            )
        except LedgerError:
            return 0

        # `stdout` is accepted for a uniform test signature. Successful read
        # recording intentionally emits no hook context.
        _ = stdout
        return 0

    def handle_pre_write(
        self,
        *,
        stdout: TextIO | None = None,
        state_dir: Path | None = None,
    ) -> int:
        """PreToolUse Write/Edit event: block local projection writes lacking authoring reads."""

        output = stdout or sys.stdout
        session_id = self.session_id()
        if not session_id:
            return 0
        config = self.workflow_config()
        if config is None:
            return 0

        roots = local_workflow_roots(config)
        if not roots:
            return 0

        targets = [
            target
            for target in self.edit_targets()
            if is_markdown_path(target.path) and is_under_any(target.path, roots)
        ]
        if not targets:
            return 0

        for target in targets:
            block_reason = local_projection_guard_reason(
                target,
                config=config,
                session_id=session_id,
                state_dir=self.state_dir(state_dir),
            )
            if block_reason:
                self.emit({"decision": "block", "reason": block_reason}, stdout=output)
                return 0
        return 0

    def handle_user_prompt_submit(
        self,
        *,
        stdout: TextIO | None = None,
        runner: CommandRunner | None = None,
    ) -> int:
        """UserPromptSubmit event: cache issue refs and inject concise context."""

        output = stdout or sys.stdout
        config = self.workflow_config()
        if config is None or config.issues.kind != "github":
            return 0

        repo = github_repo_for_config(config, runner=runner)
        if repo is None:
            return 0

        session_id = self.session_id()
        prompt_numbers = extract_issue_numbers(
            self.user_prompt_text(),
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
        self.emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": format_issue_cache_context(
                        fresh_contexts, include_details=False
                    ),
                }
            },
            stdout=output,
        )
        return 0

    def handle_stop(
        self,
        *,
        stdout: TextIO | None = None,
        runner: CommandRunner | None = None,
    ) -> int:
        """Stop event: record issue refs known to this session as pending."""

        if self.payload.get("stop_hook_active") is True:
            return 0
        # Stop hook JSON output is reserved for block decisions. Context injection
        # happens in UserPromptSubmit so Stop can never fail host output validation.
        _ = stdout

        config = self.workflow_config()
        if config is None or config.issues.kind != "github":
            return 0

        repo = github_repo_for_config(config, runner=runner)
        if repo is None:
            return 0

        session_id = self.session_id()
        issue_numbers = sorted(read_session_issues(config.root, session_id, "mentioned"), key=int)
        for number in extract_issue_numbers(
            self.scan_text(),
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

    def handle_subagent_start(self, *, stdout: TextIO | None = None) -> int:
        """SubagentStart event: no-op on runtimes that do not fire it."""

        _ = stdout
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


# =============================================================================
# Hook factory + payload/env extraction helpers
# =============================================================================


def _hook_for_payload(payload: Mapping[str, Any]) -> Hook:
    runtime = _detect_runtime(payload)
    # Subclasses are imported at the bottom of this module to keep the
    # ``Hook`` ABC and module-level helpers loadable without runtime-specific
    # implementations on top of them.
    if runtime == "codex":
        return CodexHook(payload)
    if runtime == "claude":
        return ClaudeHook(payload)
    return UnknownHook(payload)


def _detect_runtime(payload: Mapping[str, Any]) -> str:
    runtime = os.environ.get(RUNTIME_ENV_VAR, "").strip().lower()
    if runtime in {"claude", "codex"}:
        return runtime
    if payload.get("turn_id"):
        return "codex"
    return "unknown"


def _resolve_project_from_cwd(cwd: Any) -> Path | None:
    if not isinstance(cwd, str) or not cwd:
        cwd = os.getcwd()
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


def _default_plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _string(mapping: Mapping[str, Any], key: str) -> str:
    """Return the stripped string value at ``key`` or ``""`` when absent/blank."""

    value = mapping.get(key)
    if not isinstance(value, str):
        return ""
    stripped = value.strip()
    return stripped if stripped else ""


def _payload_marks_agent(payload: Mapping[str, Any]) -> bool:
    for key in _PAYLOAD_AGENT_BOOL_KEYS:
        if payload.get(key) is True:
            return True

    for key in _PAYLOAD_AGENT_STRING_KEYS:
        if _string(payload, key):
            return True

    agent_value = payload.get("agent")
    if isinstance(agent_value, Mapping) and agent_value:
        return True

    for key in _PAYLOAD_AGENT_SOURCE_KEYS:
        value = payload.get(key)
        if not isinstance(value, str):
            continue
        if value.strip().lower().replace("-", "_") in _AGENT_MARKER_VALUES:
            return True

    return False


def _session_start_source_value(payload: Mapping[str, Any], allowed: set[str]) -> str:
    value = payload.get("source")
    if not isinstance(value, str):
        return ""
    source = value.strip().lower()
    return source if source in allowed else ""


def _claude_edit_target(payload: Mapping[str, Any], resolve_path: Any) -> tuple[EditTarget, ...]:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict) or tool_name not in CLAUDE_EDIT_TOOLS:
        return ()
    file_path = _string(tool_input, "file_path")
    if not file_path:
        return ()
    path = resolve_path(file_path)
    content = tool_input.get("content") if tool_name == "Write" else None
    if not isinstance(content, str):
        content = None
    return (EditTarget(path=path, content=content),)


def _read_target_default(payload: Mapping[str, Any], resolve_path: Any) -> Path | None:
    if payload.get("tool_name") != "Read":
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    file_path = _string(tool_input, "file_path") or _string(tool_input, "path")
    if not file_path:
        return None
    return resolve_path(file_path)


def _read_stdin_json() -> dict[str, Any]:
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


def _session_metadata_indicates_agent(metadata: Any) -> bool:
    if not isinstance(metadata, Mapping):
        return False

    thread_source = metadata.get("thread_source")
    if isinstance(thread_source, str):
        normalized = thread_source.strip().lower().replace("-", "_")
        if normalized in _AGENT_MARKER_VALUES:
            return True

    source = metadata.get("source")
    if isinstance(source, Mapping) and _mapping_has_agent_marker(source):
        return True

    for key in ("agent_role", "agent_nickname", "agent_path"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return True

    return False


def _mapping_has_agent_marker(value: Mapping[str, Any]) -> bool:
    for key, item in value.items():
        if isinstance(key, str) and key in _TRANSCRIPT_AGENT_KEYS:
            return True
        if isinstance(item, Mapping) and _mapping_has_agent_marker(item):
            return True
    return False


def _parent_thread_id_from_metadata(metadata: Mapping[str, Any]) -> str:
    direct = _string(metadata, "parent_thread_id")
    if direct:
        return direct
    spawn = _nested_mapping(metadata, "source", "subagent", "thread_spawn")
    if spawn is not None:
        return _string(spawn, "parent_thread_id")
    return ""


def _agent_name_from_metadata(metadata: Mapping[str, Any]) -> str | None:
    for key in ("agent_name", "agent_role", "agent_nickname", "agent_path"):
        value = _string(metadata, key)
        if value:
            return value
    subagent = _nested_mapping(metadata, "source", "subagent")
    if subagent is not None:
        for key in ("agent_name", "agent_role", "agent_nickname"):
            value = _string(subagent, key)
            if value:
                return value
        spawn = subagent.get("thread_spawn")
        if isinstance(spawn, Mapping):
            for key in ("agent_name", "agent_role"):
                value = _string(spawn, key)
                if value:
                    return value
    return None


def _nested_mapping(root: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    current: Any = root
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current if isinstance(current, Mapping) else None


# =============================================================================
# Backward-compat shims and CLI dispatcher
# =============================================================================


def session_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    return Hook.from_payload_or_stdin(payload).handle_session_start(stdout=stdout)


def post_read(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    return Hook.from_payload_or_stdin(payload).handle_post_read(
        stdout=stdout, state_dir=state_dir
    )


def pre_write(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    return Hook.from_payload_or_stdin(payload).handle_pre_write(
        stdout=stdout, state_dir=state_dir
    )


def user_prompt_submit(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    return Hook.from_payload_or_stdin(payload).handle_user_prompt_submit(
        stdout=stdout, runner=runner
    )


def stop(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    return Hook.from_payload_or_stdin(payload).handle_stop(stdout=stdout, runner=runner)


# Concrete subclasses are imported at module-load time so the ``_hook_for_payload``
# factory above can resolve them. The bottom-of-file placement matters: each
# subclass module imports the ``Hook`` ABC and module-level helpers defined
# earlier in this file, so the abstract base must be fully defined before the
# subclass modules load. ``workflow_hook`` itself is library-only; the
# executable entry points live in ``hook_claude.py`` and ``hook_codex.py``.
from hook_claude import ClaudeHook, UnknownHook  # noqa: E402, F401
from hook_codex import CodexHook  # noqa: E402, F401
