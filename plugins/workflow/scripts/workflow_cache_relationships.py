#!/usr/bin/env python3
"""Agent-facing workflow pending relationship apply entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from workflow_command import CommandRunner
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_issue_cache import issue_numbers_from_references
from workflow_providers import ProviderDispatcher, ProviderRequest, default_provider_registry
from workflow_providers import authoring_guard_callback, request_from_config


class WorkflowCacheRelationshipsError(RuntimeError):
    """Raised when pending workflow relationships cannot be applied."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project path")
    parser.add_argument("--session", required=True, help="workflow session id for authoring guard")
    parser.add_argument("--type", default="task", help="workflow artifact type for authoring guard")
    parser.add_argument("--state-dir", type=Path, help="ledger state directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "issues",
        nargs="+",
        help="issue numbers or configured-repository GitHub issue references",
    )
    return parser


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
        payload = apply_pending_relationships_payload(
            project=args.project,
            issues=list(args.issues),
            artifact_type=args.type,
            session_id=args.session,
            state_dir=args.state_dir,
            runner=runner,
            guard=guard,
        )
    except Exception as exc:
        print(f"workflow pending relationship apply error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    for item in payload["issues"]:
        if isinstance(item, dict):
            print(f"#{item.get('issue')} applied={item.get('applied')}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
