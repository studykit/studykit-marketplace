#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Agent-facing workflow pending relationship stage/apply entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from workflow_cache import GitHubIssueCache, SCHEMA_VERSION, _atomic_write_text, _dump_yaml
from workflow_command import CommandRunner
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_issue_cache import issue_numbers_from_references
from workflow_providers import ProviderDispatcher, ProviderRequest, default_provider_registry
from workflow_providers import authoring_guard_callback, request_from_config
from workflow_env import workflow_project_dir_from_env, workflow_session_id_from_env


class WorkflowCacheRelationshipsError(RuntimeError):
    """Raised when pending workflow relationships cannot be applied."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--session", help="workflow session id for authoring guard; defaults to WORKFLOW_SESSION_ID")
    parser.add_argument("--type", default="task", help="workflow artifact type for authoring guard")
    parser.add_argument("--state-dir", type=Path, help="ledger state directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--stage", action="store_true", help="stage relationship intent instead of applying pending files")
    parser.add_argument("--parent")
    parser.add_argument("--child", action="append", default=[])
    parser.add_argument("--blocked-by", action="append", default=[])
    parser.add_argument("--blocking", action="append", default=[])
    parser.add_argument("--replace", action="store_true", help="replace an existing pending relationship file when staging")
    parser.add_argument(
        "issues",
        nargs="+",
        help="issue numbers or configured-repository GitHub issue references",
    )
    return parser


def stage_relationships_payload(
    *,
    project: Path,
    issues: list[str],
    parent: str | None = None,
    children: tuple[str, ...] = (),
    blocked_by: tuple[str, ...] = (),
    blocking: tuple[str, ...] = (),
    replace: bool = False,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Stage relationship intent for an existing configured GitHub issue."""

    config, repo, issue_numbers = _github_relationship_context(project, issues, runner=runner)
    if len(issue_numbers) != 1:
        raise WorkflowCacheRelationshipsError("relationship staging requires exactly one issue ref")

    issue = issue_numbers[0]
    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    if not cache.relationships_file(repo, issue).is_file():
        raise WorkflowCacheRelationshipsError(
            f"issue relationship cache projection is missing for #{issue}; refresh the issue cache first"
        )

    relationships_file = cache.relationships_pending_file(repo, issue)
    if relationships_file.exists() and not replace:
        raise WorkflowCacheRelationshipsError(f"pending relationship file already exists: {relationships_file}")

    payload: dict[str, object] = {"schema_version": SCHEMA_VERSION}
    if parent:
        payload["parent"] = _required_ref(parent, "parent")
    normalized_children = _normalized_refs(children)
    normalized_blocked_by = _normalized_refs(blocked_by)
    normalized_blocking = _normalized_refs(blocking)
    if normalized_children:
        payload["children"] = normalized_children
    dependencies: dict[str, object] = {}
    if normalized_blocked_by:
        dependencies["blocked_by"] = normalized_blocked_by
    if normalized_blocking:
        dependencies["blocking"] = normalized_blocking
    if dependencies:
        payload["dependencies"] = dependencies
    if len(payload) == 1:
        raise WorkflowCacheRelationshipsError("at least one relationship value is required")

    relationships_file.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(relationships_file, _dump_yaml(payload))
    operations = cache.read_pending_issue_relationships(repo, issue)
    return {
        "operation": "cache_stage_pending_relationships",
        "role": "issue",
        "kind": "github",
        "repository": repo.to_json(),
        "issue": issue,
        "relationships_file": str(relationships_file),
        "operations": [operation.to_json() for operation in operations],
    }


def apply_pending_relationships_payload(
    *,
    project: Path,
    issues: list[str],
    artifact_type: str,
    session_id: str,
    state_dir: Path | None = None,
    runner: CommandRunner | None = None,
    guard: Callable[[ProviderRequest], None] | None = None,
) -> dict[str, object]:
    """Apply pending local relationship files to configured GitHub issues."""

    config, repo, issue_numbers = _github_relationship_context(project, issues, runner=runner)
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard or authoring_guard_callback())
    results = []
    for issue in issue_numbers:
        request = request_from_config(
            config,
            role="issue",
            operation="apply_relationships",
            artifact_type=artifact_type,
            payload={"issue": issue, "from_pending": True},
            session_id=session_id,
            state_dir=state_dir,
        )
        response = dispatcher.dispatch(request)
        results.append(dict(response.payload))

    return {
        "operation": "cache_apply_pending_relationships",
        "role": "issue",
        "kind": "github",
        "repository": repo.to_json(),
        "issues": results,
    }


def _github_relationship_context(
    project: Path,
    issues: list[str],
    *,
    runner: CommandRunner | None = None,
):
    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowCacheRelationshipsError(str(exc)) from exc
    if config is None:
        raise WorkflowCacheRelationshipsError(".workflow/config.yml was not found")
    if config.issues.kind != "github":
        raise WorkflowCacheRelationshipsError("workflow pending relationship apply supports GitHub issue providers only")

    try:
        repo = resolve_github_repository(config.root, runner=runner)
    except GitHubRepositoryError as exc:
        raise WorkflowCacheRelationshipsError(str(exc)) from exc

    issue_numbers = issue_numbers_from_references(
        issues,
        repo=repo,
        issue_id_format=config.issue_id_format,
        allow_bare_numbers=True,
    )
    if not issue_numbers:
        raise WorkflowCacheRelationshipsError("no configured-repository GitHub issue references were found")
    return config, repo, issue_numbers


def _required_ref(value: str, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise WorkflowCacheRelationshipsError(f"{name} relationship ref is required")
    return text


def _normalized_refs(values: tuple[str, ...]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    runner: CommandRunner | None = None,
    guard: Callable[[ProviderRequest], None] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = stdout or sys.stdout
    errors = stderr or sys.stderr

    try:
        if args.stage:
            payload = stage_relationships_payload(
                project=args.project,
                issues=list(args.issues),
                parent=args.parent,
                children=tuple(args.child),
                blocked_by=tuple(args.blocked_by),
                blocking=tuple(args.blocking),
                replace=args.replace,
                runner=runner,
            )
        else:
            payload = apply_pending_relationships_payload(
                project=args.project,
                issues=list(args.issues),
                artifact_type=args.type,
                session_id=args.session or workflow_session_id_from_env(),
                state_dir=args.state_dir,
                runner=runner,
                guard=guard,
            )
    except Exception as exc:
        print(f"workflow pending relationship error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    if payload.get("operation") == "cache_stage_pending_relationships":
        print(f"#{payload.get('issue')} staged: {payload.get('relationships_file')}", file=output)
        return 0

    for item in payload.get("issues", []):
        if isinstance(item, dict):
            print(f"#{item.get('issue')} applied={item.get('applied')}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
