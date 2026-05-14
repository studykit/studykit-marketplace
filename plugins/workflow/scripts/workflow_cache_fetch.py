#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Agent-facing workflow provider cache fetch entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from workflow_command import CommandRunner
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_issue_cache import IssueCacheContext, cache_issue_references, format_issue_cache_context
from workflow_issue_cache import format_issue_cache_json, issue_numbers_from_references
from workflow_providers import CACHE_POLICY_DEFAULT, CACHE_POLICY_REFRESH
from workflow_env import workflow_project_dir_from_env

CACHE_FETCH_POLICIES = (CACHE_POLICY_DEFAULT, CACHE_POLICY_REFRESH)


class WorkflowCacheFetchError(RuntimeError):
    """Raised when explicit workflow cache fetch cannot proceed."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument(
        "--cache-policy",
        choices=CACHE_FETCH_POLICIES,
        default=CACHE_POLICY_DEFAULT,
        help="provider cache policy",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("references", nargs="+", help="issue numbers or GitHub issue references")
    return parser


def fetch_cache_payload(
    *,
    project: Path,
    references: list[str],
    cache_policy: str = CACHE_POLICY_DEFAULT,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Fetch configured GitHub issue references into the workflow cache."""

    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowCacheFetchError(str(exc)) from exc
    if config is None:
        raise WorkflowCacheFetchError(".workflow/config.yml was not found")
    if config.issues.kind != "github":
        raise WorkflowCacheFetchError("workflow cache fetch currently supports GitHub issue providers only")

    try:
        repo = resolve_github_repository(config.root, runner=runner)
    except GitHubRepositoryError as exc:
        raise WorkflowCacheFetchError(str(exc)) from exc

    issue_numbers = issue_numbers_from_references(
        references,
        repo=repo,
        issue_id_format=config.issue_id_format,
        allow_bare_numbers=True,
    )
    if not issue_numbers:
        raise WorkflowCacheFetchError("no configured-repository GitHub issue references were found")

    contexts = cache_issue_references(
        config,
        issue_numbers,
        repo=repo,
        cache_policy=cache_policy,
        runner=runner,
        strict=True,
    )
    return format_issue_cache_json(contexts, repo=repo, cache_policy=cache_policy)


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
        payload = fetch_cache_payload(
            project=args.project,
            references=list(args.references),
            cache_policy=args.cache_policy,
            runner=runner,
        )
    except Exception as exc:
        print(f"workflow cache fetch error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    print(format_issue_cache_context_from_payload(payload), file=output)
    return 0


def format_issue_cache_context_from_payload(payload: dict[str, object]) -> str:
    """Render plain output from the JSON payload without re-reading cache files."""

    contexts: list[IssueCacheContext] = []
    for item in payload.get("issues", []):
        if not isinstance(item, dict):
            continue
        cache_hit = item.get("cache_hit")
        contexts.append(
            IssueCacheContext(
                number=str(item.get("issue") or ""),
                issue_dir=str(item.get("issue_dir") or ""),
                title=str(item.get("title") or ""),
                state=str(item.get("state") or ""),
                cache_hit=cache_hit if isinstance(cache_hit, bool) else None,
                relationship_summary=str(item.get("relationships") or ""),
            )
        )

    return format_issue_cache_context(contexts)


if __name__ == "__main__":
    raise SystemExit(main())
