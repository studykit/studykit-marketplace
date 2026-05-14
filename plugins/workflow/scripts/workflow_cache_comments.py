#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Agent-facing workflow pending comment append entrypoint."""

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
from workflow_env import workflow_project_dir_from_env, workflow_session_id_from_env


class WorkflowCacheCommentsError(RuntimeError):
    """Raised when pending workflow comments cannot be appended."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--session", help="workflow session id for authoring guard; defaults to WORKFLOW_SESSION_ID")
    parser.add_argument("--type", default="task", help="workflow artifact type for authoring guard")
    parser.add_argument("--state-dir", type=Path, help="ledger state directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "issues",
        nargs="+",
        help="issue numbers or configured-repository GitHub issue references",
    )
    return parser


def append_pending_comments_payload(
    *,
    project: Path,
    issues: list[str],
    artifact_type: str,
    session_id: str,
    state_dir: Path | None = None,
    runner: CommandRunner | None = None,
    guard: Callable[[ProviderRequest], None] | None = None,
) -> dict[str, object]:
    """Append pending local comment files to configured GitHub issues."""

    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowCacheCommentsError(str(exc)) from exc
    if config is None:
        raise WorkflowCacheCommentsError(".workflow/config.yml was not found")
    if config.issues.kind != "github":
        raise WorkflowCacheCommentsError("workflow pending comment append supports GitHub issue providers only")

    try:
        repo = resolve_github_repository(config.root, runner=runner)
    except GitHubRepositoryError as exc:
        raise WorkflowCacheCommentsError(str(exc)) from exc

    issue_numbers = issue_numbers_from_references(
        issues,
        repo=repo,
        issue_id_format=config.issue_id_format,
        allow_bare_numbers=True,
    )
    if not issue_numbers:
        raise WorkflowCacheCommentsError("no configured-repository GitHub issue references were found")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner), guard=guard or authoring_guard_callback())
    results = []
    for issue in issue_numbers:
        request = request_from_config(
            config,
            role="issue",
            operation="add_comment",
            artifact_type=artifact_type,
            payload={"issue": issue, "from_pending": True},
            session_id=session_id,
            state_dir=state_dir,
        )
        response = dispatcher.dispatch(request)
        results.append(dict(response.payload))

    return {
        "operation": "cache_append_pending_comments",
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
        payload = append_pending_comments_payload(
            project=args.project,
            issues=list(args.issues),
            artifact_type=args.type,
            session_id=args.session or workflow_session_id_from_env(),
            state_dir=args.state_dir,
            runner=runner,
            guard=guard,
        )
    except Exception as exc:
        print(f"workflow pending comment append error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    for item in payload["issues"]:
        if isinstance(item, dict):
            print(f"#{item.get('issue')} appended={item.get('appended')}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
