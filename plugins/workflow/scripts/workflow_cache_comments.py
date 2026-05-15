#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Agent-facing workflow pending comment append entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from workflow_command import CommandRunner
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_issue_cache import issue_numbers_from_references
from workflow_providers import ProviderDispatcher, default_provider_registry, request_from_config
from workflow_env import workflow_project_dir_from_env


class WorkflowCacheCommentsError(RuntimeError):
    """Raised when pending workflow comments cannot be appended."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--type", default="task", help="workflow artifact type")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "issues",
        nargs="+",
        help="issue IDs or configured provider issue references",
    )
    return parser


def append_pending_comments_payload(
    *,
    project: Path,
    issues: list[str],
    artifact_type: str,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Append pending local comment files to configured provider issues."""

    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowCacheCommentsError(str(exc)) from exc
    if config is None:
        raise WorkflowCacheCommentsError(".workflow/config.yml was not found")
    if config.issues.kind not in {"github", "jira"}:
        raise WorkflowCacheCommentsError(
            f"workflow pending comment append supports GitHub and Jira issue providers, not {config.issues.kind}"
        )

    repo = None
    if config.issues.kind == "github":
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
        raise WorkflowCacheCommentsError(f"no configured {config.issues.kind} issue references were found")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    results = []
    for issue in issue_numbers:
        request = request_from_config(
            config,
            role="issue",
            operation="add_comment",
            artifact_type=artifact_type,
            payload={"issue": issue, "from_pending": True},
        )
        response = dispatcher.dispatch(request)
        results.append(dict(response.payload))

    payload: dict[str, object] = {
        "operation": "cache_append_pending_comments",
        "role": "issue",
        "kind": config.issues.kind,
        "issues": results,
    }
    if repo is not None:
        payload["repository"] = repo.to_json()
    return payload


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    runner: CommandRunner | None = None,
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
            runner=runner,
        )
    except Exception as exc:
        print(f"workflow pending comment append error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    for item in payload["issues"]:
        if isinstance(item, dict):
            issue_ref = f"#{item.get('issue')}" if payload.get("kind") == "github" else str(item.get("issue"))
            print(f"{issue_ref} appended={item.get('appended')}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
