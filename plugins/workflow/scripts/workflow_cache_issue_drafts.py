#!/usr/bin/env python3
# /// script
# dependencies = ["python-frontmatter", "PyYAML"]
# ///
"""Prepare and create provider-backed pending issue drafts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from workflow_cache import (
    GitHubIssueCache,
    SCHEMA_VERSION,
    _atomic_write_text,
    _dump_yaml,
    _format_markdown,
    pending_relationship_operations_from_mapping,
)
from workflow_command import CommandRunner
from workflow_config import WorkflowConfig, WorkflowConfigError, load_workflow_config
from workflow_env import workflow_project_dir_from_env
from workflow_github import GitHubRepositoryError, resolve_github_repository
from workflow_jira import JiraDataCenterIssueCache, JiraProviderError, resolve_jira_data_center_site
from workflow_providers import ProviderDispatcher, default_provider_registry, request_from_config


class WorkflowCacheIssueDraftError(RuntimeError):
    """Raised when pending issue draft operations cannot proceed."""


JIRA_REVIEW_TITLE_PREFIX = "[Review] "
JIRA_RESEARCH_TITLE_PREFIX = "[Research] "
JIRA_SPIKE_TITLE_PREFIX = "[Spike] "


def prepare_pending_issue_draft(
    *,
    project: Path,
    local_id: str,
    artifact_type: str,
    title: str,
    labels: tuple[str, ...] = (),
    state: str = "open",
    state_reason: str | None = None,
    replace: bool = False,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Create a provider-owned pending issue draft with an empty body."""

    config = _load_issue_config(project)
    local_id = _required_text(local_id, "local id")
    artifact_type = _required_text(artifact_type, "artifact type")
    title = _required_text(title, "title")
    if config.issues.kind == "jira":
        title = _jira_issue_title(artifact_type, title)
    normalized_state = (state or "open").strip().lower()
    normalized_labels = tuple(label.strip() for label in labels if label.strip())
    if config.issues.kind == "github" and artifact_type not in normalized_labels:
        normalized_labels = (artifact_type, *normalized_labels)

    if config.issues.kind == "github":
        try:
            repo = resolve_github_repository(config.root, runner=runner)
        except GitHubRepositoryError as exc:
            raise WorkflowCacheIssueDraftError(str(exc)) from exc
        cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
        issue_file = cache.pending_issue_file(repo, local_id)
        provider_payload: dict[str, object] = {"repository": repo.to_json()}
    elif config.issues.kind == "jira":
        try:
            site = resolve_jira_data_center_site(config.root)
        except (WorkflowConfigError, JiraProviderError) as exc:
            raise WorkflowCacheIssueDraftError(str(exc)) from exc
        cache = JiraDataCenterIssueCache.for_project(config.root)
        issue_file = cache.pending_issue_file(site, local_id)
        provider_payload = {"site": site.to_json()}
    else:
        raise WorkflowCacheIssueDraftError(
            f"pending issue drafts currently support GitHub and Jira issue providers, not {config.issues.kind}"
        )

    if issue_file.exists() and not replace:
        raise WorkflowCacheIssueDraftError(f"pending issue draft already exists: {issue_file}")

    frontmatter: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "type": artifact_type,
        "role": "issue",
        "provider": config.issues.kind,
        "title": title,
        "labels": list(normalized_labels),
        "state": normalized_state,
    }
    if state_reason:
        frontmatter["state_reason"] = state_reason.strip()

    issue_file.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(issue_file, _format_markdown(frontmatter, ""))

    return {
        "operation": "prepare_pending_issue",
        "role": "issue",
        "kind": config.issues.kind,
        "local_id": local_id,
        "issue_file": str(issue_file),
        "artifact_type": artifact_type,
        "title": title,
        "labels": list(normalized_labels),
        "state": normalized_state,
        "body_empty": True,
        **provider_payload,
    }


def create_pending_issue(
    *,
    project: Path,
    local_id: str,
    artifact_type: str,
    confirm_provider_create: bool = False,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Create a provider issue from an existing pending issue draft."""

    if not confirm_provider_create:
        raise WorkflowCacheIssueDraftError(
            "provider issue creation requires --confirm-provider-create after explicit user approval"
        )

    config = _load_issue_config(project)
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    request = request_from_config(
        config,
        role="issue",
        operation="create",
        artifact_type=artifact_type,
        payload={"pending_local_id": _required_text(local_id, "local id")},
    )
    response = dispatcher.dispatch(request)
    return dict(response.payload)


def stage_pending_issue_relationships(
    *,
    project: Path,
    local_id: str,
    parent: str | None = None,
    children: tuple[str, ...] = (),
    blocked_by: tuple[str, ...] = (),
    blocking: tuple[str, ...] = (),
    related: tuple[str, ...] = (),
    replace: bool = False,
    runner: CommandRunner | None = None,
) -> dict[str, object]:
    """Stage provider-native relationships for a pending provider issue draft."""

    config = _load_issue_config(project)
    local_id = _required_text(local_id, "local id")
    if config.issues.kind == "github":
        if related:
            raise WorkflowCacheIssueDraftError("related relationship staging is not supported for GitHub issue providers")
        try:
            repo = resolve_github_repository(config.root, runner=runner)
        except GitHubRepositoryError as exc:
            raise WorkflowCacheIssueDraftError(str(exc)) from exc
        cache = GitHubIssueCache.for_project(config.root, configured_repo=repo)
        issue_file = cache.pending_issue_file(repo, local_id)
        provider_payload: dict[str, object] = {"kind": "github", "repository": repo.to_json()}
        read_operations = lambda: cache.read_pending_draft_relationships(repo, local_id)
        write_operations = lambda payload: cache.write_pending_draft_relationships(
            repo,
            local_id,
            pending_relationship_operations_from_mapping(
                payload,
                path=issue_file,
                target_kind="pending_issue",
                target_id=local_id,
            ),
            replace_existing=replace,
        )
    elif config.issues.kind == "jira":
        try:
            site = resolve_jira_data_center_site(config.root)
        except (WorkflowConfigError, JiraProviderError) as exc:
            raise WorkflowCacheIssueDraftError(str(exc)) from exc
        cache = JiraDataCenterIssueCache.for_project(config.root)
        issue_file = cache.pending_issue_file(site, local_id)
        relationships_file = cache.pending_issue_relationships_pending_file(site, local_id)
        provider_payload = {"kind": "jira", "site": site.to_json()}
        read_operations = lambda: cache.read_pending_draft_relationships(site, local_id)
        write_operations = None
    else:
        raise WorkflowCacheIssueDraftError(
            f"pending issue relationship staging supports GitHub and Jira issue providers, not {config.issues.kind}"
        )

    if not issue_file.is_file():
        raise WorkflowCacheIssueDraftError(f"pending issue draft does not exist: {issue_file}")

    if config.issues.kind == "github":
        if not replace and read_operations():
            raise WorkflowCacheIssueDraftError(f"pending relationship operations already exist for GitHub pending issue {local_id}")
    elif relationships_file.exists() and not replace:
        raise WorkflowCacheIssueDraftError(f"pending relationship file already exists: {relationships_file}")

    payload: dict[str, object] = {"schema_version": SCHEMA_VERSION}
    if parent:
        payload["parent"] = _required_text(parent, "parent")
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
    normalized_related = _normalized_refs(related)
    if normalized_related:
        payload["related"] = normalized_related
    if len(payload) == 1:
        raise WorkflowCacheIssueDraftError("at least one relationship value is required")

    if config.issues.kind == "github":
        assert write_operations is not None
        pending_location = write_operations(payload)
    else:
        relationships_file.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(relationships_file, _dump_yaml(payload))
        pending_location = relationships_file
    operations = read_operations()
    result: dict[str, object] = {
        "operation": "stage_pending_issue_relationships",
        "role": "issue",
        "local_id": local_id,
        "issue_file": str(issue_file),
        "pending_location": str(pending_location),
        "operations": [operation.to_json() for operation in operations],
        **provider_payload,
    }
    if config.issues.kind == "jira":
        result["relationships_file"] = str(pending_location)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="prepare a bodyless pending issue draft")
    prepare.add_argument("--local-id", required=True)
    prepare.add_argument("--type", required=True, help="workflow artifact type for the draft")
    prepare.add_argument("--title", required=True)
    prepare.add_argument("--label", action="append", default=[])
    prepare.add_argument("--state", default="open")
    prepare.add_argument("--state-reason")
    prepare.add_argument("--replace", action="store_true")

    create = subparsers.add_parser("create", help="create a provider issue from a pending draft")
    create.add_argument("--type", default="task", help="workflow artifact type")
    create.add_argument(
        "--confirm-provider-create",
        action="store_true",
        help="confirm that the user explicitly approved creating a provider issue from this pending draft",
    )
    create.add_argument("local_id")

    relationships = subparsers.add_parser(
        "stage-relationships",
        help="stage provider-native relationships for a pending issue draft",
    )
    relationships.add_argument("--local-id", required=True)
    relationships.add_argument("--parent")
    relationships.add_argument("--child", action="append", default=[])
    relationships.add_argument("--blocked-by", action="append", default=[])
    relationships.add_argument("--blocking", action="append", default=[])
    relationships.add_argument("--related", action="append", default=[])
    relationships.add_argument("--replace", action="store_true")

    for child in subparsers.choices.values():
        child.add_argument("--json", action="store_true", help=argparse.SUPPRESS)

    return parser


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
        if args.command == "prepare":
            payload = prepare_pending_issue_draft(
                project=args.project,
                local_id=args.local_id,
                artifact_type=args.type,
                title=args.title,
                labels=tuple(args.label),
                state=args.state,
                state_reason=args.state_reason,
                replace=args.replace,
                runner=runner,
            )
        elif args.command == "create":
            payload = create_pending_issue(
                project=args.project,
                local_id=args.local_id,
                artifact_type=args.type,
                confirm_provider_create=args.confirm_provider_create,
                runner=runner,
            )
        elif args.command == "stage-relationships":
            payload = stage_pending_issue_relationships(
                project=args.project,
                local_id=args.local_id,
                parent=args.parent,
                children=tuple(args.child),
                blocked_by=tuple(args.blocked_by),
                blocking=tuple(args.blocking),
                related=tuple(args.related),
                replace=args.replace,
                runner=runner,
            )
        else:
            raise WorkflowCacheIssueDraftError(f"unsupported command: {args.command}")
    except Exception as exc:
        print(f"workflow cache issue draft error: {exc}", file=errors)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False), file=output)
    else:
        _print_plain(payload, output)
    return 0


def _load_issue_config(project: Path) -> WorkflowConfig:
    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise WorkflowCacheIssueDraftError(str(exc)) from exc
    if config is None:
        raise WorkflowCacheIssueDraftError(".workflow/config.yml was not found")
    return config


def _required_text(value: str, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise WorkflowCacheIssueDraftError(f"{name} is required")
    return text


def _is_review_artifact_type(value: str) -> bool:
    return value.strip().lower() == "review"


def _is_research_artifact_type(value: str) -> bool:
    return value.strip().lower() == "research"


def _is_spike_artifact_type(value: str) -> bool:
    return value.strip().lower() == "spike"


def _jira_issue_title(artifact_type: str, title: str) -> str:
    if _is_review_artifact_type(artifact_type):
        return _jira_prefixed_title(title, JIRA_REVIEW_TITLE_PREFIX)
    if _is_research_artifact_type(artifact_type):
        return _jira_prefixed_title(title, JIRA_RESEARCH_TITLE_PREFIX)
    if _is_spike_artifact_type(artifact_type):
        return _jira_prefixed_title(title, JIRA_SPIKE_TITLE_PREFIX)
    return title


def _jira_review_title(title: str) -> str:
    return _jira_prefixed_title(title, JIRA_REVIEW_TITLE_PREFIX)


def _jira_prefixed_title(title: str, prefix: str) -> str:
    if title.startswith(prefix):
        return title
    marker = prefix.strip()
    if title.lower().startswith(marker.lower()):
        return f"{prefix}{title[len(marker):].lstrip()}"
    return f"{prefix}{title}"


def _normalized_refs(values: tuple[str, ...]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _print_plain(payload: dict[str, object], output: TextIO) -> None:
    operation = payload.get("operation")
    if operation == "prepare_pending_issue":
        print(f"prepared pending issue {payload.get('local_id')}: {payload.get('issue_file')}", file=output)
        return
    if operation == "stage_pending_issue_relationships":
        print(
            f"staged relationships for pending issue {payload.get('local_id')}: "
            f"{payload.get('pending_location')}",
            file=output,
        )
        return
    issue = payload.get("issue")
    print(f"created issue {issue} verified={payload.get('verified')}", file=output)


if __name__ == "__main__":
    raise SystemExit(main())
