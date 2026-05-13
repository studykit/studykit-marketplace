#!/usr/bin/env python3
"""Workflow hook dispatcher.

SessionStart injects a concise workflow authoring policy only when the active
project has a valid ``workflow.config.yml``. The hook never starts workflow
skills and never blocks session startup.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from authoring_guard import evaluate_authoring_guard  # noqa: E402
from authoring_ledger import LedgerError, record_reads  # noqa: E402
from authoring_resolver import ALL_TYPES, DUAL_TYPES, ResolverError  # noqa: E402
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config  # noqa: E402

RUNTIME_ENV_VAR = "WORKFLOW_HOOK_RUNTIME"
STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"
CLAUDE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}


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

    resolver = plugin_root / "scripts" / "authoring_resolver.py"
    ledger = plugin_root / "scripts" / "authoring_ledger.py"
    guard = plugin_root / "scripts" / "authoring_guard.py"

    commit_ref = "disabled"
    if config.commit_refs.enabled:
        commit_ref = config.commit_refs.style

    return (
        "## workflow authoring policy\n\n"
        f"Configured workflow project: `{config.root}`\n"
        f"Config file: `{config.path}`\n"
        f"Issue provider: `{config.issues.kind}`\n"
        f"Knowledge provider: `{config.knowledge.kind}`\n"
        f"Local projection: `{config.local_projection.mode}`\n"
        f"Commit references: `{commit_ref}`\n\n"
        "Before creating or editing any workflow issue, knowledge artifact, "
        "or local projection, resolve and read the required authoring contracts.\n\n"
        "Resolver command:\n\n"
        "```bash\n"
        f'python3 "{resolver}" --project "{config.root}" --type <artifact-type> '
        "[--role issue|knowledge] --json\n"
        "```\n\n"
        "Use `--role issue` or `--role knowledge` for dual artifacts such as "
        "`usecase` and `research`.\n\n"
        "The resolver JSON contains `required_authoring_files`, and every path "
        "in that list is absolute. Read every listed file before writing.\n\n"
        "When a wrapper or hook requires ledger enforcement, record reads with:\n\n"
        "```bash\n"
        f'python3 "{ledger}" --project "{config.root}" --session <session-id> '
        "record --json <absolute-authoring-file>...\n"
        "```\n\n"
        "Check write readiness with:\n\n"
        "```bash\n"
        f'python3 "{guard}" --project "{config.root}" --session <session-id> '
        "--type <artifact-type> [--role issue|knowledge] --json\n"
        "```\n\n"
        "SessionStart only injects this policy. It does not auto-trigger "
        "workflow skills."
    )


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
