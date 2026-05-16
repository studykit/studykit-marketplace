#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Agent-facing workflow issue semantic metadata update entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from workflow_cache import GitHubIssueCache, WorkflowCacheError
from workflow_command import CommandRunner
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config
from workflow_env import workflow_project_dir_from_env
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_issue_cache import issue_numbers_from_references
from workflow_jira import (
    JiraDataCenterIssueCache,
    JiraProviderError,
    normalize_jira_issue_key,
    resolve_jira_data_center_site,
)
from workflow_providers import ProviderDispatcher, default_provider_registry, request_from_config


class WorkflowIssueMetadataError(RuntimeError):
    """Raised when semantic issue metadata cannot be updated safely."""


_GITHUB_TYPE_LABELS = {"task", "bug", "spike", "epic", "review", "usecase", "research"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--artifact-type", default="task", help="workflow artifact type for dispatch context")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--title", help="new semantic title")
    parser.add_argument("--workflow-type", help="new workflow type metadata value")
    parser.add_argument("--status", help="semantic status; unsupported unless mapping is configured")
    parser.add_argument("--priority", help="semantic priority; unsupported unless mapping is configured")
    parser.add_argument("issue", help="configured-provider issue reference")
    return parser


def update_issue_metadata_payload(
    *,
    project: Path,
    issue: str,
    artifact_type: str,
    title: str | None = None,
    workflow_type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Update safe semantic metadata for one configured-provider issue."""

    config = _load_issue_config(project)
    if config.issues.kind == "github":
        return _update_github_metadata(
            config,
            issue,
            artifact_type=artifact_type,
            title=title,
            workflow_type=workflow_type,
            status=status,
            priority=priority,
            runner=runner,
        )
    if config.issues.kind == "jira":
        return _update_jira_metadata(
            config,
            issue,
            artifact_type=artifact_type,
            title=title,
            workflow_type=workflow_type,
            status=status,
            priority=priority,
            runner=runner,
        )
    raise WorkflowIssueMetadataError(
        f"workflow issue metadata updates support GitHub and Jira issue providers, not {config.issues.kind}"
    )


def _update_github_metadata(
    config: WorkflowConfig,
    issue: str,
    *,
    artifact_type: str,
    title: str | None,
    workflow_type: str | None,
    status: str | None,
    priority: str | None,
    runner: CommandRunner | None,
) -> dict[str, Any]:
    if status is not None:
        raise WorkflowIssueMetadataError("GitHub semantic status writes require explicit metadata mapping config")
    if priority is not None:
        raise WorkflowIssueMetadataError("GitHub semantic priority writes require explicit metadata mapping config")

    try:
        repo = resolve_github_repository(config.root, runner=runner)
    except GitHubRepositoryError as exc:
        raise WorkflowIssueMetadataError(str(exc)) from exc
    issue_numbers = issue_numbers_from_references(
        [issue],
        repo=repo,
        issue_id_format=config.issue_id_format,
        allow_bare_numbers=True,
    )
    if len(issue_numbers) != 1:
        raise WorkflowIssueMetadataError("metadata update requires exactly one GitHub issue ref")
    issue_number = issue_numbers[0]

    cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
    try:
        cached = cache.read_issue(repo, issue_number, include_body=False, include_comments=False, include_relationships=False)
    except WorkflowCacheError as exc:
        raise WorkflowIssueMetadataError(f"refresh the GitHub issue cache before metadata update: {exc}") from exc

    labels = set(_string_list(cached.get("labels")))
    if workflow_type:
        labels = _replace_github_type_label(labels, workflow_type)

    payload: dict[str, Any] = {"issue": issue_number, "freshness_check": True}
    if title is not None:
        payload["title"] = title
    if workflow_type:
        payload["labels"] = sorted(labels)
    if len(payload) == 2:
        raise WorkflowIssueMetadataError("metadata update requires at least one supported metadata value")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    response = dispatcher.dispatch(
        request_from_config(
            config,
            role="issue",
            operation="update",
            artifact_type=artifact_type,
            payload=payload,
        )
    )
    return {
        "operation": "update_issue_metadata",
        "kind": "github",
        "issue": issue_number,
        "repository": repo.to_json(),
        "updated": _updated_fields(title=title, workflow_type=workflow_type),
        "provider": dict(response.payload),
    }


def _update_jira_metadata(
    config: WorkflowConfig,
    issue: str,
    *,
    artifact_type: str,
    title: str | None,
    workflow_type: str | None,
    status: str | None,
    priority: str | None,
    runner: CommandRunner | None,
) -> dict[str, Any]:
    if workflow_type is not None:
        raise WorkflowIssueMetadataError("Jira semantic type writes require explicit safe type-change config")
    if status is not None:
        raise WorkflowIssueMetadataError("Jira semantic status writes require explicit transition or field mapping config")
    if priority is not None:
        raise WorkflowIssueMetadataError("Jira semantic priority writes require explicit metadata mapping config")

    try:
        site = resolve_jira_data_center_site(config.root)
        issue_key = normalize_jira_issue_key(issue)
    except (WorkflowConfigError, JiraProviderError) as exc:
        raise WorkflowIssueMetadataError(str(exc)) from exc

    cache = JiraDataCenterIssueCache.for_project(config.root)
    try:
        cached = cache.read_issue(site, issue_key, include_body=False, include_comments=False, include_relationships=False)
    except WorkflowCacheError as exc:
        raise WorkflowIssueMetadataError(f"refresh the Jira issue cache before metadata update: {exc}") from exc

    payload: dict[str, Any] = {"issue": issue_key, "freshness_check": True}
    if title is not None:
        payload["title"] = title
    if len(payload) == 2:
        raise WorkflowIssueMetadataError("metadata update requires at least one supported metadata value")

    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    response = dispatcher.dispatch(
        request_from_config(
            config,
            role="issue",
            operation="update",
            artifact_type=artifact_type,
            payload=payload,
        )
    )
    return {
        "operation": "update_issue_metadata",
        "kind": "jira",
        "issue": issue_key,
        "key": issue_key,
        "site": site.to_json(),
        "updated": _updated_fields(title=title),
        "provider": dict(response.payload),
    }


def _replace_github_type_label(labels: set[str], workflow_type: str) -> set[str]:
    desired = workflow_type.strip()
    if not desired:
        raise WorkflowIssueMetadataError("workflow type metadata value is empty")
    labels = {label for label in labels if label not in _GITHUB_TYPE_LABELS}
    labels.add(desired)
    return labels


def _updated_fields(
    *,
    title: str | None,
    workflow_type: str | None = None,
) -> list[str]:
    fields = []
    if title is not None:
        fields.append("title")
    if workflow_type is not None:
        fields.append("type")
    return fields


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        nodes = value.get("nodes")
        if isinstance(nodes, list):
            return _string_list(nodes)
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, list | tuple | set):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    result.append(str(name))
            elif item is not None:
                result.append(str(item))
        return result
    return [str(value)]


def _load_issue_config(project: Path) -> WorkflowConfig:
    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowIssueMetadataError(str(exc)) from exc
    if config is None:
        raise WorkflowIssueMetadataError(".workflow/config.yml was not found")
    return config


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
        payload = update_issue_metadata_payload(
            project=args.project,
            issue=args.issue,
            artifact_type=args.artifact_type,
            title=args.title,
            workflow_type=args.workflow_type,
            status=args.status,
            priority=args.priority,
            runner=runner,
        )
    except Exception as exc:
        print(f"workflow issue metadata error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
        return 0

    print(f"{payload.get('issue')} metadata updated: {', '.join(payload.get('updated') or [])}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
