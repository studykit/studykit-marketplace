#!/usr/bin/env python3
# /// script
# dependencies = ["PyYAML"]
# ///
"""GitHub CLI wrapper utilities for workflow provider code."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from workflow_command import CommandRunner, WorkflowCommandError, run_command
from workflow_config import WorkflowConfigError, load_workflow_config
from workflow_env import workflow_project_dir_from_env


DEFAULT_ISSUE_FIELDS = (
    "number",
    "title",
    "state",
    "stateReason",
    "body",
    "labels",
    "comments",
    "projectItems",
    "url",
    "createdAt",
    "updatedAt",
    "closedAt",
)

BODY_EDIT_HISTORY_QUERY = """
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    issue(number:$number) {
      number
      title
      updatedAt
      lastEditedAt
      editor { login }
      userContentEdits(first: 20) {
        nodes {
          editedAt
          editor { login }
          deletedAt
          diff
        }
      }
    }
  }
}
""".strip()


class GitHubParseError(ValueError):
    """Raised when GitHub CLI output cannot be parsed."""


class GitHubRepositoryError(ValueError):
    """Raised when a GitHub repository context cannot be resolved."""


class GitHubVerificationError(RuntimeError):
    """Raised when a GitHub write cannot be verified after mutation."""


@dataclass(frozen=True)
class GitHubRepository:
    """Resolved GitHub repository context."""

    host: str
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"

    def to_json(self) -> dict[str, str]:
        return {"host": self.host, "owner": self.owner, "repo": self.name, "slug": self.slug}


def resolve_github_repository(
    project: Path,
    *,
    remote: str = "origin",
    runner: CommandRunner | None = None,
) -> GitHubRepository:
    """Resolve GitHub repository context from workflow config, then Git remotes."""

    configured = _github_repository_from_config(project)
    if configured is not None:
        return configured

    remote_url = _git_remote_url(project, name=remote, runner=runner)
    return parse_github_remote_url(remote_url)


def parse_github_remote_url(remote_url: str) -> GitHubRepository:
    """Parse common HTTPS and SSH GitHub remote URL forms."""

    value = remote_url.strip()
    if not value:
        raise GitHubRepositoryError("remote URL is empty")

    scp_match = re.match(r"^(?P<user>[^@]+)@(?P<host>[^:]+):(?P<path>.+)$", value)
    if scp_match:
        host = scp_match.group("host")
        path = scp_match.group("path")
        return _repo_from_host_path(host, path)

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "ssh", "git"} and parsed.hostname:
        return _repo_from_host_path(parsed.hostname, parsed.path)

    raise GitHubRepositoryError(f"unsupported GitHub remote URL: {remote_url}")


def view_issue(
    issue: int | str,
    *,
    project: Path,
    fields: tuple[str, ...] = DEFAULT_ISSUE_FIELDS,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read one GitHub issue through ``gh issue view``."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    data = _view_issue_with_repo(repo, issue_number, project=project, fields=fields, runner=runner)
    data.setdefault("repository", repo.to_json())
    return data


def _view_issue_with_repo(
    repo: GitHubRepository,
    issue_number: str,
    *,
    project: Path,
    fields: tuple[str, ...],
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read one GitHub issue when repository context is already resolved."""

    result = _gh(
        [
            "issue",
            "view",
            issue_number,
            "--repo",
            repo.slug,
            "--json",
            ",".join(fields),
        ],
        project=project,
        runner=runner,
    )
    return _loads_json_object(result.stdout, "gh issue view")


def create_issue(
    *,
    title: str,
    body: str,
    project: Path,
    labels: tuple[str, ...] = (),
    state: str = "open",
    state_reason: str | None = None,
    verify: bool = True,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Create an issue."""

    repo = resolve_github_repository(project, runner=runner)
    normalized_state = _normalize_issue_state(state)
    with _body_file(body) as body_file:
        args = [
            "issue",
            "create",
            "--repo",
            repo.slug,
            "--title",
            title,
            "--body-file",
            str(body_file),
        ]
        for label in labels:
            if label:
                args.extend(["--label", label])
        result = _gh(args, project=project, runner=runner)

    issue_number = _issue_number_from_create_output(result.stdout, repo)
    if normalized_state == "CLOSED":
        _gh(
            [
                "issue",
                "close",
                issue_number,
                "--repo",
                repo.slug,
                "--reason",
                _close_reason_from_state_reason(state_reason),
            ],
            project=project,
            runner=runner,
        )
    if verify:
        _verify_created_issue(
            repo,
            issue_number,
            expected_title=title,
            expected_body=body,
            expected_labels=labels,
            expected_state=normalized_state,
            expected_state_reason=_expected_state_reason(normalized_state, state_reason),
            project=project,
            runner=runner,
        )
    return {"operation": "create_issue", "issue": issue_number, "verified": verify}


def edit_issue(
    issue: int | str,
    *,
    project: Path,
    title: str | None = None,
    body: str | None = None,
    labels: tuple[str, ...] | None = None,
    current_labels: tuple[str, ...] | None = None,
    operation: str = "edit_issue",
    verify: bool = True,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Edit issue title, body, and labels."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    label_edits = _label_edit_args(
        repo,
        issue_number,
        labels=labels,
        current_labels=current_labels,
        project=project,
        runner=runner,
    )
    if title is None and body is None and not label_edits:
        return {"operation": operation, "issue": issue_number, "verified": verify}

    args = ["issue", "edit", issue_number, "--repo", repo.slug]
    if title is not None:
        args.extend(["--title", title])
    args.extend(label_edits)
    if body is None:
        _gh(args, project=project, runner=runner)
    else:
        with _body_file(body) as body_file:
            args.extend(["--body-file", str(body_file)])
            _gh(args, project=project, runner=runner)

    if verify:
        _verify_issue_fields(
            repo,
            issue_number,
            expected_title=title,
            expected_body=body,
            expected_labels=labels,
            exact_labels=labels is not None,
            project=project,
            runner=runner,
        )
    return {"operation": operation, "issue": issue_number, "verified": verify}


def edit_issue_body(
    issue: int | str,
    *,
    body: str,
    project: Path,
    verify: bool = True,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Replace an issue body."""

    payload = edit_issue(
        issue,
        body=body,
        project=project,
        operation="edit_issue_body",
        verify=verify,
        runner=runner,
    )
    return {"operation": "edit_issue_body", "issue": payload["issue"], "verified": verify}


def comment_issue(
    issue: int | str,
    *,
    body: str,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Add an issue comment."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    with _body_file(body) as body_file:
        _gh(
            ["issue", "comment", issue_number, "--repo", repo.slug, "--body-file", str(body_file)],
            project=project,
            runner=runner,
        )
    return {"repository": repo.to_json(), "issue": issue_number, "operation": "comment_issue"}


def close_issue(
    issue: int | str,
    *,
    project: Path,
    reason: str = "completed",
    comment: str | None = None,
    verify: bool = True,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Close an issue."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    args = ["issue", "close", issue_number, "--repo", repo.slug, "--reason", reason]
    if comment:
        args.extend(["--comment", comment])
    _gh(args, project=project, runner=runner)
    if verify:
        _verify_issue_state(
            repo,
            issue_number,
            expected_state="CLOSED",
            expected_state_reason=_expected_closed_state_reason(reason),
            project=project,
            runner=runner,
        )
    return {"operation": "close_issue", "issue": issue_number, "verified": verify}


def reopen_issue(
    issue: int | str,
    *,
    project: Path,
    comment: str | None = None,
    verify: bool = True,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Reopen an issue."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    args = ["issue", "reopen", issue_number, "--repo", repo.slug]
    if comment:
        args.extend(["--comment", comment])
    _gh(args, project=project, runner=runner)
    if verify:
        _verify_issue_state(
            repo,
            issue_number,
            expected_state="OPEN",
            expected_state_reason=None,
            project=project,
            runner=runner,
        )
    return {"operation": "reopen_issue", "issue": issue_number, "verified": verify}


def add_sub_issue(
    parent_issue: int | str,
    child_issue: int | str,
    *,
    project: Path,
    replace_parent: bool = False,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Add a GitHub sub-issue."""

    repo = resolve_github_repository(project, runner=runner)
    parent_number = normalize_issue_number(parent_issue)
    child_number = normalize_issue_number(child_issue)
    child_id = issue_rest_id(child_number, project=project, runner=runner)
    args = [
        "api",
        "-X",
        "POST",
        f"repos/{repo.slug}/issues/{parent_number}/sub_issues",
        "-F",
        f"sub_issue_id={child_id}",
    ]
    if replace_parent:
        args.extend(["-F", "replace_parent=true"])
    _gh(args, project=project, runner=runner)
    return {
        "operation": "add_sub_issue",
        "parent_issue": parent_number,
        "child_issue": child_number,
    }


def remove_sub_issue(
    parent_issue: int | str,
    child_issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Remove a GitHub sub-issue."""

    repo = resolve_github_repository(project, runner=runner)
    parent_number = normalize_issue_number(parent_issue)
    child_number = normalize_issue_number(child_issue)
    child_id = issue_rest_id(child_number, project=project, runner=runner)
    _gh(
        [
            "api",
            "-X",
            "DELETE",
            f"repos/{repo.slug}/issues/{parent_number}/sub_issue",
            "-F",
            f"sub_issue_id={child_id}",
        ],
        project=project,
        runner=runner,
    )
    return {
        "operation": "remove_sub_issue",
        "parent_issue": parent_number,
        "child_issue": child_number,
    }


def add_issue_dependency(
    issue: int | str,
    blocking_issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Add a GitHub dependency where ``issue`` is blocked by ``blocking_issue``."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    blocking_number = normalize_issue_number(blocking_issue)
    blocking_id = issue_rest_id(blocking_number, project=project, runner=runner)
    _gh(
        [
            "api",
            "-X",
            "POST",
            f"repos/{repo.slug}/issues/{issue_number}/dependencies/blocked_by",
            "-F",
            f"issue_id={blocking_id}",
        ],
        project=project,
        runner=runner,
    )
    return {
        "operation": "add_issue_dependency",
        "issue": issue_number,
        "blocking_issue": blocking_number,
    }


def remove_issue_dependency(
    issue: int | str,
    blocking_issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Remove a GitHub dependency where ``issue`` is blocked by ``blocking_issue``."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    blocking_number = normalize_issue_number(blocking_issue)
    blocking_id = issue_rest_id(blocking_number, project=project, runner=runner)
    _gh(
        [
            "api",
            "-X",
            "DELETE",
            f"repos/{repo.slug}/issues/{issue_number}/dependencies/blocked_by/{blocking_id}",
        ],
        project=project,
        runner=runner,
    )
    return {
        "operation": "remove_issue_dependency",
        "issue": issue_number,
        "blocking_issue": blocking_number,
    }


def issue_rest_id(
    issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> str:
    """Return the REST numeric id for an issue."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    data = _issue_rest_object(repo, issue_number, project=project, runner=runner)
    raw_id = data.get("id")
    if raw_id is None:
        raise GitHubParseError(f"GitHub issue #{issue_number} REST payload is missing id")
    return str(raw_id)


def issue_relationships(
    issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read current GitHub issue relationships through provider-native REST endpoints."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    issue_data = _issue_rest_object(repo, issue_number, project=project, runner=runner)
    parent = _optional_issue_rest_object(
        repo,
        f"repos/{repo.slug}/issues/{issue_number}/parent",
        project=project,
        runner=runner,
    )
    children = _issue_rest_items(
        repo,
        f"repos/{repo.slug}/issues/{issue_number}/sub_issues",
        project=project,
        runner=runner,
    )
    blocked_by = _issue_rest_items(
        repo,
        f"repos/{repo.slug}/issues/{issue_number}/dependencies/blocked_by",
        project=project,
        runner=runner,
    )
    blocking = _issue_rest_items(
        repo,
        f"repos/{repo.slug}/issues/{issue_number}/dependencies/blocking",
        project=project,
        runner=runner,
    )

    payload: dict[str, Any] = {
        "repository": repo.to_json(),
        "number": int(issue_number),
        "updated_at": issue_data.get("updated_at") or issue_data.get("updatedAt"),
    }
    if parent:
        payload["parent"] = parent
    if children:
        payload["children"] = children
    dependency_payload: dict[str, Any] = {}
    if blocked_by:
        dependency_payload["blocked_by"] = blocked_by
    if blocking:
        dependency_payload["blocking"] = blocking
    if dependency_payload:
        payload["dependencies"] = dependency_payload
    return payload


def _verify_issue_body(
    repo: GitHubRepository,
    issue_number: str,
    *,
    expected_body: str,
    project: Path,
    runner: CommandRunner | None = None,
) -> None:
    data = _view_issue_with_repo(repo, issue_number, project=project, fields=("body",), runner=runner)
    actual_body = data.get("body")
    if actual_body != expected_body:
        raise GitHubVerificationError(f"GitHub issue #{issue_number} body verification failed")


def _verify_issue_fields(
    repo: GitHubRepository,
    issue_number: str,
    *,
    expected_title: str | None,
    expected_body: str | None,
    expected_labels: tuple[str, ...] | None,
    exact_labels: bool,
    project: Path,
    runner: CommandRunner | None = None,
) -> None:
    fields: list[str] = []
    if expected_title is not None:
        fields.append("title")
    if expected_body is not None:
        fields.append("body")
    if expected_labels is not None:
        fields.append("labels")
    if not fields:
        return

    data = _view_issue_with_repo(
        repo,
        issue_number,
        project=project,
        fields=tuple(fields),
        runner=runner,
    )
    if expected_title is not None and data.get("title") != expected_title:
        raise GitHubVerificationError(f"GitHub issue #{issue_number} title verification failed")
    if expected_body is not None and data.get("body") != expected_body:
        raise GitHubVerificationError(f"GitHub issue #{issue_number} body verification failed")
    if expected_labels is not None:
        actual_labels = set(_label_names(data.get("labels")))
        expected_label_set = {label for label in expected_labels if label}
        if exact_labels and actual_labels != expected_label_set:
            raise GitHubVerificationError(
                f"GitHub issue #{issue_number} labels verification failed: "
                f"expected {sorted(expected_label_set)}, got {sorted(actual_labels)}"
            )
        if not exact_labels and not expected_label_set.issubset(actual_labels):
            raise GitHubVerificationError(
                f"GitHub issue #{issue_number} labels verification failed: "
                f"expected {sorted(expected_label_set)}, got {sorted(actual_labels)}"
            )


def _verify_issue_state(
    repo: GitHubRepository,
    issue_number: str,
    *,
    expected_state: str,
    expected_state_reason: str | None,
    project: Path,
    runner: CommandRunner | None = None,
) -> None:
    data = _view_issue_with_repo(
        repo,
        issue_number,
        project=project,
        fields=("state", "stateReason"),
        runner=runner,
    )
    state = str(data.get("state") or "").upper()
    state_reason = data.get("stateReason")
    normalized_state_reason = str(state_reason).upper() if state_reason else None
    if state != expected_state:
        raise GitHubVerificationError(
            f"GitHub issue #{issue_number} state verification failed: expected {expected_state}, got {state}"
        )
    if expected_state_reason is not None and normalized_state_reason != expected_state_reason:
        raise GitHubVerificationError(
            "GitHub issue "
            f"#{issue_number} stateReason verification failed: "
            f"expected {expected_state_reason}, got {normalized_state_reason}"
        )


def _verify_created_issue(
    repo: GitHubRepository,
    issue_number: str,
    *,
    expected_title: str,
    expected_body: str,
    expected_labels: tuple[str, ...],
    expected_state: str,
    expected_state_reason: str | None,
    project: Path,
    runner: CommandRunner | None = None,
) -> None:
    data = _view_issue_with_repo(
        repo,
        issue_number,
        project=project,
        fields=("title", "body", "labels", "state", "stateReason"),
        runner=runner,
    )
    if data.get("title") != expected_title:
        raise GitHubVerificationError(f"GitHub issue #{issue_number} title verification failed")
    if data.get("body") != expected_body:
        raise GitHubVerificationError(f"GitHub issue #{issue_number} body verification failed")
    actual_labels = set(_label_names(data.get("labels")))
    expected_label_set = {label for label in expected_labels if label}
    if expected_label_set and not expected_label_set.issubset(actual_labels):
        raise GitHubVerificationError(
            f"GitHub issue #{issue_number} labels verification failed: "
            f"expected {sorted(expected_label_set)}, got {sorted(actual_labels)}"
        )

    state = str(data.get("state") or "").upper()
    state_reason = data.get("stateReason")
    normalized_state_reason = str(state_reason).upper() if state_reason else None
    if state != expected_state:
        raise GitHubVerificationError(
            f"GitHub issue #{issue_number} state verification failed: expected {expected_state}, got {state}"
        )
    if expected_state_reason is not None and normalized_state_reason != expected_state_reason:
        raise GitHubVerificationError(
            "GitHub issue "
            f"#{issue_number} stateReason verification failed: "
            f"expected {expected_state_reason}, got {normalized_state_reason}"
        )


def _expected_closed_state_reason(reason: str) -> str | None:
    normalized = reason.strip().lower().replace("_", "-")
    if normalized in {"completed", "complete", "done"}:
        return "COMPLETED"
    if normalized in {"not-planned", "not planned"}:
        return "NOT_PLANNED"
    return None


def _expected_state_reason(state: str, state_reason: str | None) -> str | None:
    if state != "CLOSED":
        return None
    if state_reason:
        normalized = state_reason.strip().lower().replace("_", "-")
        if normalized in {"completed", "complete", "done"}:
            return "COMPLETED"
        if normalized in {"not-planned", "not planned"}:
            return "NOT_PLANNED"
    return "COMPLETED"


def _close_reason_from_state_reason(state_reason: str | None) -> str:
    if state_reason:
        normalized = state_reason.strip().lower().replace("_", "-")
        if normalized in {"not-planned", "not planned"}:
            return "not planned"
    return "completed"


def _label_edit_args(
    repo: GitHubRepository,
    issue_number: str,
    *,
    labels: tuple[str, ...] | None,
    current_labels: tuple[str, ...] | None,
    project: Path,
    runner: CommandRunner | None = None,
) -> list[str]:
    if labels is None:
        return []

    desired = {label for label in labels if label}
    if current_labels is None:
        data = _view_issue_with_repo(
            repo,
            issue_number,
            project=project,
            fields=("labels",),
            runner=runner,
        )
        current = set(_label_names(data.get("labels")))
    else:
        current = {label for label in current_labels if label}

    args: list[str] = []
    for label in sorted(desired - current):
        args.extend(["--add-label", label])
    for label in sorted(current - desired):
        args.extend(["--remove-label", label])
    return args


def _normalize_issue_state(state: str) -> str:
    normalized = state.strip().upper().replace("-", "_")
    if normalized in {"OPEN", "CLOSED"}:
        return normalized
    raise GitHubParseError(f"unsupported issue state for creation: {state}")


def _issue_number_from_create_output(output: str, repo: GitHubRepository) -> str:
    patterns = (
        rf"https?://{re.escape(repo.host)}/{re.escape(repo.owner)}/{re.escape(repo.name)}/issues/([1-9]\d*)",
        r"/issues/([1-9]\d*)\b",
        r"#([1-9]\d*)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, output.strip())
        if match:
            return normalize_issue_number(match.group(1))
    raise GitHubParseError(f"could not determine created issue number from gh output: {output.strip()}")


def _label_names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if isinstance(nodes, list):
            return _label_names(nodes)
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        labels: list[str] = []
        for item in value:
            labels.extend(_label_names(item))
        return labels
    return [str(value)]


def issue_timeline(
    issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read issue timeline events through the REST timeline endpoint."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    result = _gh(
        ["api", f"repos/{repo.slug}/issues/{issue_number}/timeline", "--paginate"],
        project=project,
        runner=runner,
    )
    return {
        "repository": repo.to_json(),
        "issue": issue_number,
        "events": _loads_json_items(result.stdout, "gh api issue timeline"),
    }


def issue_events(
    issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read structured issue events through the REST events endpoint."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    result = _gh(
        ["api", f"repos/{repo.slug}/issues/{issue_number}/events", "--paginate"],
        project=project,
        runner=runner,
    )
    return {
        "repository": repo.to_json(),
        "issue": issue_number,
        "events": _loads_json_items(result.stdout, "gh api issue events"),
    }


def issue_body_edit_history(
    issue: int | str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Read issue body edit history through GraphQL ``userContentEdits``."""

    repo = resolve_github_repository(project, runner=runner)
    issue_number = normalize_issue_number(issue)
    result = _gh(
        [
            "api",
            "graphql",
            "-f",
            f"owner={repo.owner}",
            "-f",
            f"repo={repo.name}",
            "-F",
            f"number={issue_number}",
            "-f",
            f"query={BODY_EDIT_HISTORY_QUERY}",
        ],
        project=project,
        runner=runner,
    )
    data = _loads_json_object(result.stdout, "gh api graphql userContentEdits")
    issue_data = _dig(data, "data", "repository", "issue")
    if not isinstance(issue_data, dict):
        raise GitHubParseError("GraphQL response did not contain data.repository.issue")
    return {
        "repository": repo.to_json(),
        "issue": issue_number,
        "body_edit_history": issue_data,
    }


def normalize_issue_number(issue: int | str) -> str:
    """Normalize a same-repository issue number."""

    value = str(issue).strip()
    if value.startswith("#"):
        value = value[1:]
    if not value.isdigit():
        raise GitHubParseError(f"issue number must be numeric or #number: {issue}")
    return value


def _github_repository_from_config(project: Path) -> GitHubRepository | None:
    try:
        config = load_workflow_config(project)
    except WorkflowConfigError as exc:
        raise GitHubRepositoryError(str(exc)) from exc
    if config is None or config.issues.kind != "github":
        return None

    settings = config.issues.settings
    host = _string_setting(settings, "host", "hostname") or "github.com"
    repo_slug = _string_setting(settings, "repo", "repository", "slug")
    owner = _string_setting(settings, "owner", "org", "organization")
    name = _string_setting(settings, "name", "repo_name", "repository_name")

    if repo_slug:
        if repo_slug.startswith(("http://", "https://", "ssh://", "git@")):
            return parse_github_remote_url(repo_slug)
        parts = repo_slug.strip("/").split("/")
        if len(parts) == 2:
            owner, name = parts
        elif len(parts) > 2:
            host = parts[0]
            owner = parts[-2]
            name = parts[-1]

    if not owner or not name:
        return None
    return GitHubRepository(host=host, owner=owner, name=_strip_dot_git(name))


def _string_setting(settings: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = settings.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _repo_from_host_path(host: str, raw_path: str) -> GitHubRepository:
    path = raw_path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise GitHubRepositoryError(f"remote URL path does not include owner and repo: {raw_path}")
    owner = parts[-2]
    name = _strip_dot_git(parts[-1])
    if not owner or not name:
        raise GitHubRepositoryError(f"remote URL path does not include owner and repo: {raw_path}")
    return GitHubRepository(host=host, owner=owner, name=name)


def _strip_dot_git(value: str) -> str:
    return value[:-4] if value.endswith(".git") else value


def _git_remote_url(
    project: Path,
    *,
    name: str = "origin",
    runner: CommandRunner | None = None,
) -> str:
    """Private Git fallback for repository context resolution."""

    project_path = project.expanduser().resolve(strict=False)
    result = run_command(
        ["git", "-C", str(project_path), "remote", "get-url", name],
        runner=runner,
    )
    value = result.stdout.strip()
    if not value:
        raise GitHubRepositoryError(f"git remote get-url {name} returned empty output")
    return value


def _issue_rest_object(
    repo: GitHubRepository,
    issue_number: str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    return _gh_api_json_object(
        f"repos/{repo.slug}/issues/{issue_number}",
        project=project,
        runner=runner,
    )


def _optional_issue_rest_object(
    _repo: GitHubRepository,
    path: str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any] | None:
    result = _gh(["api", path], project=project, runner=runner, check=False)
    if result.returncode == 404 or _gh_result_is_not_found(result):
        return None
    if result.returncode != 0:
        _raise_gh_error(result)
    return _loads_json_object(result.stdout, f"gh api {path}")


def _issue_rest_items(
    _repo: GitHubRepository,
    path: str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> list[Any]:
    result = _gh(["api", path, "--paginate"], project=project, runner=runner)
    return _loads_json_items(result.stdout, f"gh api {path}")


def _gh_api_json_object(
    path: str,
    *,
    project: Path,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    result = _gh(["api", path], project=project, runner=runner)
    return _loads_json_object(result.stdout, f"gh api {path}")


def _gh(args: list[str], *, project: Path, runner: CommandRunner | None = None, check: bool = True):
    cwd = project.expanduser().resolve(strict=False)
    return run_command(["gh", *args], cwd=cwd, runner=runner, check=check)


def _raise_gh_error(result) -> None:
    stderr = result.stderr.strip()
    detail = f": {stderr}" if stderr else ""
    raise WorkflowCommandError(
        f"command failed with exit code {result.returncode}: {result.request.args[0]}{detail}",
        request=result.request,
        result=result,
    )


def _gh_result_is_not_found(result) -> bool:
    text = f"{result.stderr}\n{result.stdout}".lower()
    return result.returncode != 0 and ("http 404" in text or "not found" in text)


class _body_file:
    """Temporary file context for gh options that require a file path."""

    def __init__(self, body: str):
        self.body = body
        self.path: Path | None = None

    def __enter__(self) -> Path:
        handle = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            prefix="workflow-github-",
            suffix=".md",
            delete=False,
        )
        with handle:
            handle.write(self.body)
        self.path = Path(handle.name)
        return self.path

    def __exit__(self, *_exc_info: object) -> None:
        if self.path is None:
            return
        try:
            self.path.unlink()
        except OSError:
            pass


def _loads_json_object(raw: str, context: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GitHubParseError(f"could not parse {context} JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GitHubParseError(f"{context} JSON must be an object")
    return data


def _loads_json_items(raw: str, context: str) -> list[Any]:
    decoder = json.JSONDecoder()
    index = 0
    values: list[Any] = []
    text = raw.strip()
    try:
        while index < len(text):
            value, next_index = decoder.raw_decode(text, index)
            if isinstance(value, list):
                values.extend(value)
            else:
                values.append(value)
            index = next_index
            while index < len(text) and text[index].isspace():
                index += 1
    except json.JSONDecodeError as exc:
        raise GitHubParseError(f"could not parse {context} JSON: {exc}") from exc
    return values


def _dig(data: Mapping[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--remote", default="origin", help="Git remote fallback name")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("repo", help="resolve GitHub repository context")

    view_parser = subparsers.add_parser("issue-view", help="read issue fields")
    view_parser.add_argument("issue")
    view_parser.add_argument("--fields", help="comma-separated gh issue fields")

    for name in ("timeline", "events", "body-edits"):
        child = subparsers.add_parser(name, help=f"read issue {name}")
        child.add_argument("issue")

    create_parser = _add_write_parser(subparsers, "create", "create issue")
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--body-file", type=Path, required=True)
    create_parser.add_argument("--label", action="append", default=[])
    create_parser.add_argument("--state", default="open")
    create_parser.add_argument("--state-reason")

    edit_parser = _add_write_parser(subparsers, "edit-body", "replace issue body")
    edit_parser.add_argument("issue")
    edit_parser.add_argument("--body-file", type=Path, required=True)

    comment_parser = _add_write_parser(subparsers, "comment", "add issue comment")
    comment_parser.add_argument("issue")
    comment_parser.add_argument("--body-file", type=Path, required=True)

    close_parser = _add_write_parser(subparsers, "close", "close issue")
    close_parser.add_argument("issue")
    close_parser.add_argument("--reason", default="completed")
    close_parser.add_argument("--comment")

    reopen_parser = _add_write_parser(subparsers, "reopen", "reopen issue")
    reopen_parser.add_argument("issue")
    reopen_parser.add_argument("--comment")

    for child in subparsers.choices.values():
        child.add_argument("--json", action="store_true", help=argparse.SUPPRESS)

    return parser


def _add_write_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    help_text: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help_text)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = _run_cli(args)
    except Exception as exc:
        print(f"workflow github error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        _print_plain(payload)
    return 0


def _run_cli(args: argparse.Namespace) -> Any:
    project = args.project
    if args.command == "repo":
        return resolve_github_repository(project, remote=args.remote).to_json()
    if args.command == "issue-view":
        fields = DEFAULT_ISSUE_FIELDS
        if args.fields:
            fields = tuple(field.strip() for field in args.fields.split(",") if field.strip())
        return view_issue(args.issue, project=project, fields=fields)
    if args.command == "timeline":
        return issue_timeline(args.issue, project=project)
    if args.command == "events":
        return issue_events(args.issue, project=project)
    if args.command == "body-edits":
        return issue_body_edit_history(args.issue, project=project)

    if args.command == "create":
        return create_issue(
            title=args.title,
            body=args.body_file.read_text(encoding="utf-8"),
            labels=tuple(args.label),
            state=args.state,
            state_reason=args.state_reason,
            project=project,
        )
    if args.command == "edit-body":
        return edit_issue_body(
            args.issue,
            body=args.body_file.read_text(encoding="utf-8"),
            project=project,
        )
    if args.command == "comment":
        return comment_issue(
            args.issue,
            body=args.body_file.read_text(encoding="utf-8"),
            project=project,
        )
    if args.command == "close":
        return close_issue(
            args.issue,
            project=project,
            reason=args.reason,
            comment=args.comment,
        )
    if args.command == "reopen":
        return reopen_issue(args.issue, project=project, comment=args.comment)
    raise GitHubParseError(f"unsupported command: {args.command}")


def _print_plain(payload: Any) -> None:
    if isinstance(payload, dict):
        print(json.dumps(payload, sort_keys=False))
        return
    if isinstance(payload, list):
        for item in payload:
            print(json.dumps(item, sort_keys=False) if isinstance(item, dict) else item)
        return
    print(payload)


if __name__ == "__main__":
    raise SystemExit(main())
