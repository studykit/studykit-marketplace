#!/usr/bin/env python3
"""Local workflow provider read cache projections."""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter as frontmatter_lib

from workflow_github import GitHubRepository, normalize_issue_number

CACHE_ROOT_NAME = ".workflow-cache"
SCHEMA_VERSION = 1
_FRONTMATTER_HANDLER = frontmatter_lib.YAMLHandler()


class WorkflowCacheError(RuntimeError):
    """Base error for workflow cache failures."""


class WorkflowCacheMiss(WorkflowCacheError):
    """Raised when a cache projection does not exist."""


class WorkflowCacheCorrupt(WorkflowCacheError):
    """Raised when a cache projection exists but cannot be parsed."""


class WorkflowFreshnessConflict(WorkflowCacheError):
    """Raised when cache freshness metadata blocks a provider write."""

    def __init__(self, result: FreshnessCheckResult):
        super().__init__(result.message)
        self.result = result


@dataclass(frozen=True)
class CacheWriteResult:
    """Paths written for one cache projection refresh."""

    issue_dir: Path
    issue_file: Path
    metadata_file: Path
    comments_index: Path
    relationship_location: Path

    def to_json(self) -> dict[str, str]:
        return {
            "issue_dir": str(self.issue_dir),
            "issue_file": str(self.issue_file),
            "metadata_file": str(self.metadata_file),
            "comments_index": str(self.comments_index),
            "relationship_location": str(self.relationship_location),
        }


@dataclass(frozen=True)
class PendingIssueDraft:
    """Parsed pending provider issue draft."""

    local_id: str
    path: Path
    title: str
    body: str
    labels: tuple[str, ...] = ()
    state: str = "open"
    state_reason: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "local_id": self.local_id,
            "path": str(self.path),
            "title": self.title,
            "labels": list(self.labels),
            "state": self.state,
            "state_reason": self.state_reason,
        }


@dataclass(frozen=True)
class PendingIssueComment:
    """Parsed pending provider issue comment body."""

    target_kind: str
    target_id: str
    path: Path
    body: str

    @property
    def file_name(self) -> str:
        return self.path.name

    def to_json(self) -> dict[str, Any]:
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "file": self.file_name,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class PendingIssueRelationshipOperation:
    """Parsed pending provider-native relationship operation."""

    target_kind: str
    target_id: str
    path: Path
    action: str
    relationship: str
    target_ref: str
    replace_parent: bool = False

    @property
    def file_name(self) -> str:
        return self.path.name

    def to_json(self) -> dict[str, Any]:
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "file": self.file_name,
            "path": str(self.path),
            "action": self.action,
            "relationship": self.relationship,
            "target_ref": self.target_ref,
            "replace_parent": self.replace_parent,
        }


@dataclass(frozen=True)
class FreshnessMetadata:
    """Local cache freshness metadata for one write-back target."""

    source_updated_at: str | None
    fetched_at: str | None
    path: Path | None = None
    target: str = "artifact"

    def to_json(self) -> dict[str, str | None]:
        result: dict[str, str | None] = {
            "target": self.target,
            "source_updated_at": self.source_updated_at,
            "fetched_at": self.fetched_at,
        }
        if self.path is not None:
            result["path"] = str(self.path)
        return result


@dataclass(frozen=True)
class FreshnessCheckResult:
    """Result of comparing local cache metadata with provider state."""

    ok: bool
    status: str
    message: str
    artifact: str
    source_updated_at: str | None = None
    fetched_at: str | None = None
    provider_updated_at: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "message": self.message,
            "artifact": self.artifact,
            "source_updated_at": self.source_updated_at,
            "fetched_at": self.fetched_at,
            "provider_updated_at": self.provider_updated_at,
        }


def check_provider_freshness(
    metadata: FreshnessMetadata | None,
    *,
    provider_updated_at: str | None,
    artifact: str,
    pending_new: bool = False,
) -> FreshnessCheckResult:
    """Compare local cache metadata with the current provider timestamp."""

    if pending_new:
        return FreshnessCheckResult(
            ok=True,
            status="pending_new",
            message=f"{artifact} is pending creation; no provider freshness check is required.",
            artifact=artifact,
            provider_updated_at=provider_updated_at,
        )

    if metadata is None or not metadata.source_updated_at or not metadata.fetched_at:
        return FreshnessCheckResult(
            ok=False,
            status="missing_metadata",
            message=(
                f"Cannot safely write {artifact}: cache freshness metadata is missing. "
                "Refresh the provider cache before writing."
            ),
            artifact=artifact,
            source_updated_at=metadata.source_updated_at if metadata else None,
            fetched_at=metadata.fetched_at if metadata else None,
            provider_updated_at=provider_updated_at,
        )

    source_dt = _parse_freshness_timestamp(metadata.source_updated_at)
    fetched_dt = _parse_freshness_timestamp(metadata.fetched_at)
    if source_dt is None or fetched_dt is None:
        return FreshnessCheckResult(
            ok=False,
            status="invalid_metadata",
            message=(
                f"Cannot safely write {artifact}: cache freshness timestamps are invalid. "
                "Refresh the provider cache before writing."
            ),
            artifact=artifact,
            source_updated_at=metadata.source_updated_at,
            fetched_at=metadata.fetched_at,
            provider_updated_at=provider_updated_at,
        )

    provider_dt = _parse_freshness_timestamp(provider_updated_at)
    if provider_dt is None:
        return FreshnessCheckResult(
            ok=True,
            status="provider_timestamp_unavailable",
            message=(
                f"{artifact} provider timestamp is unavailable; no stale-cache conflict "
                "could be detected."
            ),
            artifact=artifact,
            source_updated_at=metadata.source_updated_at,
            fetched_at=metadata.fetched_at,
            provider_updated_at=provider_updated_at,
        )

    if provider_dt > fetched_dt or provider_dt > source_dt:
        return FreshnessCheckResult(
            ok=False,
            status="stale",
            message=(
                f"Stale workflow cache for {artifact}: provider timestamp "
                f"{provider_updated_at} is newer than cached source_updated_at "
                f"{metadata.source_updated_at} or fetched_at {metadata.fetched_at}. "
                "Refresh the provider cache before writing."
            ),
            artifact=artifact,
            source_updated_at=metadata.source_updated_at,
            fetched_at=metadata.fetched_at,
            provider_updated_at=provider_updated_at,
        )

    return FreshnessCheckResult(
        ok=True,
        status="fresh",
        message=f"{artifact} cache is fresh enough for write-back.",
        artifact=artifact,
        source_updated_at=metadata.source_updated_at,
        fetched_at=metadata.fetched_at,
        provider_updated_at=provider_updated_at,
    )


def require_provider_freshness(
    metadata: FreshnessMetadata | None,
    *,
    provider_updated_at: str | None,
    artifact: str,
    pending_new: bool = False,
) -> FreshnessCheckResult:
    """Return freshness status or raise when a write-back should be blocked."""

    result = check_provider_freshness(
        metadata,
        provider_updated_at=provider_updated_at,
        artifact=artifact,
        pending_new=pending_new,
    )
    if not result.ok:
        raise WorkflowFreshnessConflict(result)
    return result


class GitHubIssueCache:
    """Repo-local cache for GitHub issue read projections."""

    def __init__(self, root: Path, *, configured_repo: GitHubRepository | None = None):
        self.root = root
        self.configured_repo = configured_repo

    @classmethod
    def for_project(
        cls,
        project: Path,
        *,
        configured_repo: GitHubRepository | None = None,
    ) -> GitHubIssueCache:
        return cls(
            project.expanduser().resolve(strict=False) / CACHE_ROOT_NAME,
            configured_repo=configured_repo,
        )

    def issue_dir(self, repo: GitHubRepository, issue: int | str) -> Path:
        if self.configured_repo is None or _same_github_repo(repo, self.configured_repo):
            return self.root / "issues" / normalize_issue_number(issue)
        return (
            self.root
            / _safe_path_segment(repo.host)
            / _safe_path_segment(repo.owner)
            / _safe_path_segment(repo.name)
            / "issues"
            / normalize_issue_number(issue)
        )

    def pending_issue_dir(self, repo: GitHubRepository, local_id: str) -> Path:
        safe_local_id = _safe_path_segment(local_id)
        if self.configured_repo is None or _same_github_repo(repo, self.configured_repo):
            return self.root / "issues-pending" / safe_local_id
        return (
            self.root
            / _safe_path_segment(repo.host)
            / _safe_path_segment(repo.owner)
            / _safe_path_segment(repo.name)
            / "issues-pending"
            / safe_local_id
        )

    def pending_issue_file(self, repo: GitHubRepository, local_id: str) -> Path:
        return self.pending_issue_dir(repo, local_id) / "issue.md"

    def created_issue_archive_dir(
        self,
        repo: GitHubRepository,
        local_id: str,
        issue: int | str,
    ) -> Path:
        safe_local_id = _safe_path_segment(local_id)
        issue_number = normalize_issue_number(issue)
        if self.configured_repo is None or _same_github_repo(repo, self.configured_repo):
            return self.root / "issues-created" / f"{issue_number}-{safe_local_id}"
        return (
            self.root
            / _safe_path_segment(repo.host)
            / _safe_path_segment(repo.owner)
            / _safe_path_segment(repo.name)
            / "issues-created"
            / f"{issue_number}-{safe_local_id}"
        )

    def issue_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "issue.md"

    def issue_metadata_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "metadata.yml"

    def comments_dir(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "comments"

    def comments_index_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.comments_dir(repo, issue) / "index.yml"

    def comments_pending_dir(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "comments-pending"

    def pending_issue_comments_pending_dir(self, repo: GitHubRepository, local_id: str) -> Path:
        return self.pending_issue_dir(repo, local_id) / "comments-pending"

    def freshness_file(self, repo: GitHubRepository, issue: int | str, target: str) -> Path:
        normalized = _normalize_freshness_target(target)
        if normalized == "issue":
            return self.issue_metadata_file(repo, issue)
        if normalized == "comments":
            return self.comments_index_file(repo, issue)
        if normalized == "relationships":
            return self.issue_metadata_file(repo, issue)
        raise WorkflowCacheError(f"unsupported freshness target: {target}")

    def has_issue_projection(self, repo: GitHubRepository, issue: int | str) -> bool:
        return self.issue_file(repo, issue).is_file()

    def read_pending_issue_draft(self, repo: GitHubRepository, local_id: str) -> PendingIssueDraft:
        """Read a pending issue draft from ``issues-pending/<local-id>/issue.md``."""

        path = self.pending_issue_file(repo, local_id)
        if not path.is_file():
            raise WorkflowCacheMiss(f"pending issue draft does not exist: {path}")

        frontmatter, body = _read_frontmatter_markdown(path)
        schema_version = frontmatter.get("schema_version")
        if schema_version is not None:
            _require_schema(frontmatter, path)

        title = str(frontmatter.get("title") or "").strip()
        if not title:
            raise WorkflowCacheCorrupt(f"pending issue draft is missing title: {path}")

        labels = tuple(_label_names(frontmatter.get("labels")))
        state = _normalize_state(frontmatter.get("state"))
        if state not in {"open", "closed"}:
            raise WorkflowCacheCorrupt(f"unsupported pending issue state: {state}: {path}")
        state_reason = _normalize_state_reason(frontmatter.get("state_reason") or frontmatter.get("stateReason"))
        return PendingIssueDraft(
            local_id=_safe_path_segment(local_id),
            path=path,
            title=title,
            body=body,
            labels=labels,
            state=state,
            state_reason=state_reason,
        )

    def read_pending_issue_comments(
        self,
        repo: GitHubRepository,
        issue: int | str,
    ) -> list[PendingIssueComment]:
        """Read pending comment files for an existing issue projection."""

        issue_number = normalize_issue_number(issue)
        return _read_pending_comments(
            self.comments_pending_dir(repo, issue_number),
            target_kind="issue",
            target_id=issue_number,
        )

    def read_pending_draft_comments(
        self,
        repo: GitHubRepository,
        local_id: str,
    ) -> list[PendingIssueComment]:
        """Read pending comment files for a pending issue projection."""

        safe_local_id = _safe_path_segment(local_id)
        return _read_pending_comments(
            self.pending_issue_comments_pending_dir(repo, safe_local_id),
            target_kind="pending_issue",
            target_id=safe_local_id,
        )

    def read_pending_issue_relationships(
        self,
        repo: GitHubRepository,
        issue: int | str,
    ) -> list[PendingIssueRelationshipOperation]:
        """Read pending relationship operations for an existing issue projection."""

        issue_number = normalize_issue_number(issue)
        issue_path = self.issue_file(repo, issue_number)
        _found, operations = _read_frontmatter_pending_relationships(
            issue_path,
            target_kind="issue",
            target_id=issue_number,
        )
        return operations

    def read_pending_draft_relationships(
        self,
        repo: GitHubRepository,
        local_id: str,
    ) -> list[PendingIssueRelationshipOperation]:
        """Read pending relationship operations for a pending issue projection."""

        safe_local_id = _safe_path_segment(local_id)
        issue_path = self.pending_issue_file(repo, safe_local_id)
        _found, operations = _read_frontmatter_pending_relationships(
            issue_path,
            target_kind="pending_issue",
            target_id=safe_local_id,
        )
        return operations

    def write_pending_issue_relationships(
        self,
        repo: GitHubRepository,
        issue: int | str,
        operations: Iterable[PendingIssueRelationshipOperation],
        *,
        replace_existing: bool = False,
    ) -> Path:
        """Write canonical pending relationship operations into issue frontmatter."""

        issue_number = normalize_issue_number(issue)
        issue_path = self.issue_file(repo, issue_number)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"issue cache does not exist: {issue_path}")
        if not replace_existing and self.read_pending_issue_relationships(repo, issue_number):
            raise WorkflowCacheError(f"pending relationship operations already exist for GitHub issue #{issue_number}")
        normalized = _retarget_relationship_operations(
            operations,
            path=issue_path,
            target_kind="issue",
            target_id=issue_number,
        )
        if not normalized:
            raise WorkflowCacheError(f"no pending relationship operations for GitHub issue #{issue_number}")
        self._write_frontmatter_pending_relationships(issue_path, normalized)
        return issue_path

    def write_pending_draft_relationships(
        self,
        repo: GitHubRepository,
        local_id: str,
        operations: Iterable[PendingIssueRelationshipOperation],
        *,
        replace_existing: bool = False,
    ) -> Path:
        """Write canonical pending relationship operations into draft frontmatter."""

        safe_local_id = _safe_path_segment(local_id)
        issue_path = self.pending_issue_file(repo, safe_local_id)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"pending issue draft does not exist: {issue_path}")
        if not replace_existing and self.read_pending_draft_relationships(repo, safe_local_id):
            raise WorkflowCacheError(f"pending relationship operations already exist for GitHub pending issue {safe_local_id}")
        normalized = _retarget_relationship_operations(
            operations,
            path=issue_path,
            target_kind="pending_issue",
            target_id=safe_local_id,
        )
        if not normalized:
            raise WorkflowCacheError(f"no pending relationship operations for GitHub pending issue {safe_local_id}")
        self._write_frontmatter_pending_relationships(issue_path, normalized)
        return issue_path

    def _write_frontmatter_pending_relationships(
        self,
        issue_path: Path,
        operations: list[PendingIssueRelationshipOperation],
    ) -> None:
        frontmatter, body = _read_frontmatter_markdown(issue_path)
        relationships = _frontmatter_relationship_block(frontmatter, issue_path, create=True)
        relationships["pending"] = {
            "operations": [_pending_relationship_operation_to_frontmatter(operation) for operation in operations]
        }
        _atomic_write_text(issue_path, _format_markdown(frontmatter, body))

    def remove_pending_issue_comments(
        self,
        repo: GitHubRepository,
        issue: int | str,
        comments: Iterable[PendingIssueComment],
    ) -> list[Path]:
        """Remove successfully consumed pending comment files."""

        issue_number = normalize_issue_number(issue)
        pending_dir = self.comments_pending_dir(repo, issue_number)
        removed: list[Path] = []
        for comment in comments:
            path = comment.path
            if path.parent.resolve(strict=False) != pending_dir.resolve(strict=False):
                raise WorkflowCacheError(f"pending comment is outside issue pending directory: {path}")
            if path.exists():
                path.unlink()
                removed.append(path)
        _remove_empty_parents(pending_dir, stop_at=self.issue_dir(repo, issue_number))
        return removed

    def remove_pending_draft_comments(
        self,
        repo: GitHubRepository,
        local_id: str,
        comments: Iterable[PendingIssueComment],
    ) -> list[Path]:
        """Remove successfully consumed pending comment files from a draft."""

        safe_local_id = _safe_path_segment(local_id)
        pending_dir = self.pending_issue_comments_pending_dir(repo, safe_local_id)
        removed: list[Path] = []
        for comment in comments:
            path = comment.path
            if path.parent.resolve(strict=False) != pending_dir.resolve(strict=False):
                raise WorkflowCacheError(f"pending comment is outside draft pending directory: {path}")
            if path.exists():
                path.unlink()
                removed.append(path)
        _remove_empty_parents(pending_dir, stop_at=self.pending_issue_dir(repo, safe_local_id))
        return removed

    def remove_pending_issue_relationships(
        self,
        repo: GitHubRepository,
        issue: int | str,
        operations: Iterable[PendingIssueRelationshipOperation],
    ) -> list[Path]:
        """Remove successfully consumed pending relationship operations from frontmatter."""

        issue_number = normalize_issue_number(issue)
        issue_path = self.issue_file(repo, issue_number)
        operation_list = list(operations)
        if not operation_list:
            return []
        if not all(operation.path.resolve(strict=False) == issue_path.resolve(strict=False) for operation in operation_list):
            raise WorkflowCacheError(f"pending relationship operation is outside issue frontmatter: {issue_path}")
        changed = self._remove_frontmatter_pending_relationships(issue_path, operation_list)
        return [issue_path] if changed else []

    def remove_pending_draft_relationships(
        self,
        repo: GitHubRepository,
        local_id: str,
        operations: Iterable[PendingIssueRelationshipOperation],
    ) -> list[Path]:
        """Remove consumed pending relationship operations from draft frontmatter."""

        safe_local_id = _safe_path_segment(local_id)
        issue_path = self.pending_issue_file(repo, safe_local_id)
        operation_list = list(operations)
        if not operation_list:
            return []
        if not all(operation.path.resolve(strict=False) == issue_path.resolve(strict=False) for operation in operation_list):
            raise WorkflowCacheError(f"pending relationship operation is outside draft frontmatter: {issue_path}")
        changed = self._remove_frontmatter_pending_relationships(issue_path, operation_list)
        return [issue_path] if changed else []

    def _remove_frontmatter_pending_relationships(
        self,
        issue_path: Path,
        consumed: list[PendingIssueRelationshipOperation],
    ) -> bool:
        frontmatter, body = _read_frontmatter_markdown(issue_path)
        relationships = _frontmatter_relationship_block(frontmatter, issue_path, create=False)
        if relationships is None:
            return False
        pending = relationships.get("pending")
        if pending is None:
            return False
        if not isinstance(pending, Mapping):
            raise WorkflowCacheCorrupt(f"issue relationship pending frontmatter must be a mapping: {issue_path}")
        raw_operations = pending.get("operations")
        if raw_operations is None:
            return False
        if not isinstance(raw_operations, list):
            raise WorkflowCacheCorrupt(f"issue relationship pending operations must be a list: {issue_path}")

        consumed_keys = [_pending_relationship_key(operation) for operation in consumed]
        remaining: list[Any] = []
        changed = False
        for item in raw_operations:
            operation = _pending_relationship_operation_from_mapping(
                item,
                path=issue_path,
                target_kind=consumed[0].target_kind,
                target_id=consumed[0].target_id,
            )
            key = _pending_relationship_key(operation)
            try:
                consumed_keys.remove(key)
                changed = True
            except ValueError:
                remaining.append(item)

        if not changed:
            return False
        if remaining:
            relationships["pending"] = {"operations": remaining}
        else:
            relationships.pop("pending", None)
        if not relationships:
            frontmatter.pop("relationships", None)
        _atomic_write_text(issue_path, _format_markdown(frontmatter, body))
        return True

    def finalize_pending_issue_creation(
        self,
        repo: GitHubRepository,
        local_id: str,
        issue: int | str,
    ) -> dict[str, str | None]:
        """Archive the consumed draft and move pending frontmatter intent to the new issue."""

        safe_local_id = _safe_path_segment(local_id)
        issue_number = normalize_issue_number(issue)
        pending_operations = self.read_pending_draft_relationships(repo, safe_local_id)
        pending_dir = self.pending_issue_dir(repo, local_id)
        draft_path = pending_dir / "issue.md"
        archive_dir = self.created_issue_archive_dir(repo, local_id, issue)
        archived_issue: Path | None = None
        if draft_path.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_issue = archive_dir / "issue.md"
            os.replace(draft_path, archived_issue)

        issue_dir = self.issue_dir(repo, issue_number)
        issue_dir.mkdir(parents=True, exist_ok=True)
        moved_comments = _move_path_if_exists(pending_dir / "comments-pending", issue_dir / "comments-pending")
        relationships_pending: Path | None = None
        if pending_operations:
            relationships_pending = self.write_pending_issue_relationships(
                repo,
                issue_number,
                pending_operations,
                replace_existing=True,
            )
        _remove_empty_parents(pending_dir, stop_at=self.root)
        return {
            "archived_issue": str(archived_issue) if archived_issue is not None else None,
            "comments_pending": str(moved_comments) if moved_comments is not None else None,
            "relationships_pending": str(relationships_pending) if relationships_pending is not None else None,
        }

    def read_freshness_metadata(
        self,
        repo: GitHubRepository,
        issue: int | str,
        *,
        target: str = "issue",
    ) -> FreshnessMetadata:
        """Read freshness metadata for issue, comments, or relationships."""

        normalized = _normalize_freshness_target(target)
        if normalized == "relationships":
            metadata_path = self.issue_metadata_file(repo, issue)
            if metadata_path.is_file():
                data = _read_yaml_mapping(metadata_path)
                _require_schema(data, metadata_path)
                relationships = data.get("relationships")
                if relationships is not None:
                    if not isinstance(relationships, Mapping):
                        raise WorkflowCacheCorrupt(f"relationship freshness metadata must be a mapping: {metadata_path}")
                    return FreshnessMetadata(
                        source_updated_at=_normalize_optional(relationships.get("source_updated_at")),
                        fetched_at=_normalize_optional(relationships.get("fetched_at")),
                        path=metadata_path,
                        target=normalized,
                    )

            raise WorkflowCacheMiss(f"freshness cache does not exist: {metadata_path}")

        path = self.freshness_file(repo, issue, normalized)
        if not path.is_file():
            raise WorkflowCacheMiss(f"freshness cache does not exist: {path}")

        data = _read_yaml_mapping(path)
        _require_schema(data, path)
        return FreshnessMetadata(
            source_updated_at=_normalize_optional(data.get("source_updated_at")),
            fetched_at=_normalize_optional(data.get("fetched_at")),
            path=path,
            target=normalized,
        )

    def read_issue(
        self,
        repo: GitHubRepository,
        issue: int | str,
        *,
        include_body: bool = True,
        include_comments: bool = True,
        include_relationships: bool = True,
    ) -> dict[str, Any]:
        """Read a cached issue projection.

        The caller controls whether raw Markdown body files are loaded. Missing or
        malformed projections raise cache-specific errors so provider dispatch can
        treat them as misses.
        """

        issue_path = self.issue_file(repo, issue)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"issue cache does not exist: {issue_path}")

        try:
            frontmatter, body = _read_frontmatter_markdown(issue_path)
            _require_schema(frontmatter, issue_path)
            for key in ("title", "state", "state_reason", "labels", "source_updated_at"):
                if key not in frontmatter:
                    raise WorkflowCacheCorrupt(f"missing issue frontmatter field {key}: {issue_path}")

            labels = frontmatter.get("labels")
            if labels is None:
                labels = []
            if not isinstance(labels, list):
                raise WorkflowCacheCorrupt(f"issue labels must be a list: {issue_path}")

            metadata: dict[str, Any] = {}
            try:
                metadata = self.read_issue_metadata(repo, issue)
            except WorkflowCacheMiss:
                metadata = {}
            fetched_at = _normalize_optional(metadata.get("fetched_at")) or _normalize_optional(
                frontmatter.get("fetched_at")
            )
            source_updated_at = _normalize_optional(frontmatter.get("source_updated_at"))
            cache_metadata: dict[str, Any] = {
                "hit": True,
                "issue_file": str(issue_path),
                "fetchedAt": fetched_at,
                "sourceUpdatedAt": _normalize_optional(metadata.get("source_updated_at")) or source_updated_at,
            }
            if metadata:
                cache_metadata["metadata_file"] = str(self.issue_metadata_file(repo, issue))

            payload: dict[str, Any] = {
                "number": int(normalize_issue_number(issue)),
                "title": str(frontmatter.get("title") or ""),
                "state": frontmatter.get("state"),
                "stateReason": frontmatter.get("state_reason"),
                "labels": [str(label) for label in labels],
                "updatedAt": source_updated_at,
                "repository": repo.to_json(),
                "cache": cache_metadata,
            }
            projects = _project_items_for_frontmatter(frontmatter.get("projects"))
            if projects:
                payload["projects"] = projects
            if include_body:
                payload["body"] = body
            if include_comments:
                payload["comments"] = self.read_comments(repo, issue, include_body=include_body)["comments"]
            if include_relationships:
                payload["relationships"] = self.read_relationships(repo, issue)
            return payload
        except WorkflowCacheError:
            raise
        except Exception as exc:
            raise WorkflowCacheCorrupt(f"could not read issue cache {issue_path}: {exc}") from exc

    def read_issue_metadata(self, repo: GitHubRepository, issue: int | str) -> dict[str, Any]:
        """Read non-user-facing cache metadata for a cached issue projection."""

        path = self.issue_metadata_file(repo, issue)
        if not path.is_file():
            raise WorkflowCacheMiss(f"issue metadata cache does not exist: {path}")
        try:
            data = _read_yaml_mapping(path)
            _require_schema(data, path)
            return dict(data)
        except WorkflowCacheError:
            raise
        except Exception as exc:
            raise WorkflowCacheCorrupt(f"could not read issue metadata cache {path}: {exc}") from exc

    def read_comments(
        self,
        repo: GitHubRepository,
        issue: int | str,
        *,
        include_body: bool = True,
    ) -> dict[str, Any]:
        index_path = self.comments_index_file(repo, issue)
        if not index_path.is_file():
            raise WorkflowCacheMiss(f"comments cache does not exist: {index_path}")

        try:
            data = _read_yaml_mapping(index_path)
            _require_schema(data, index_path)
            comments = data.get("comments") or []
            if not isinstance(comments, list):
                raise WorkflowCacheCorrupt(f"comments must be a list: {index_path}")

            result_comments: list[dict[str, Any]] = []
            for item in comments:
                if not isinstance(item, Mapping):
                    raise WorkflowCacheCorrupt(f"comment index entry must be a mapping: {index_path}")
                file_name = item.get("file")
                provider_comment_id = item.get("provider_comment_id")
                author = item.get("author")
                if not file_name or not provider_comment_id or not author:
                    raise WorkflowCacheCorrupt(f"comment index entry is missing required fields: {index_path}")

                comment: dict[str, Any] = {
                    "id": str(provider_comment_id),
                    "author": {"login": str(author)},
                    "createdAt": _timestamp_from_comment_filename(str(file_name)),
                }
                provider_node_id = item.get("provider_node_id")
                if provider_node_id:
                    comment["nodeId"] = str(provider_node_id)

                if include_body:
                    body_path = index_path.parent / str(file_name)
                    frontmatter, body = _read_frontmatter_markdown(body_path)
                    if str(frontmatter.get("author") or "") != str(author):
                        raise WorkflowCacheCorrupt(f"comment author mismatch: {body_path}")
                    comment["updatedAt"] = frontmatter.get("updated_at")
                    comment["body"] = body
                result_comments.append(comment)

            return {
                "repository": repo.to_json(),
                "issue": normalize_issue_number(issue),
                "comments": result_comments,
                "cache": {
                    "hit": True,
                    "comments_index": str(index_path),
                    "fetchedAt": data.get("fetched_at"),
                    "sourceUpdatedAt": data.get("source_updated_at"),
                },
            }
        except WorkflowCacheError:
            raise
        except Exception as exc:
            raise WorkflowCacheCorrupt(f"could not read comments cache {index_path}: {exc}") from exc

    def read_relationships(self, repo: GitHubRepository, issue: int | str) -> dict[str, Any]:
        issue_path = self.issue_file(repo, issue)
        frontmatter_current = _read_frontmatter_current_relationships(issue_path)
        if frontmatter_current is None:
            raise WorkflowCacheMiss(f"relationship frontmatter does not exist: {issue_path}")
        data: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
        try:
            freshness = self.read_freshness_metadata(repo, issue, target="relationships")
        except WorkflowCacheError:
            freshness = None
        if freshness is not None:
            data["source_updated_at"] = freshness.source_updated_at
            data["fetched_at"] = freshness.fetched_at
        data.update(frontmatter_current)
        return data

    def write_relationships_projection(
        self,
        repo: GitHubRepository,
        issue: int | str,
        relationship_payload: Mapping[str, Any],
        *,
        fetched_at: str | None = None,
    ) -> Path:
        """Write only the current relationship projection for one issue."""

        now = fetched_at or _utc_now()
        issue_number = normalize_issue_number(issue)
        issue_path = self.issue_file(repo, issue_number)
        if not issue_path.is_file():
            raise WorkflowCacheMiss(f"issue cache does not exist: {issue_path}")
        current = _relationships_from_issue(relationship_payload)
        source_updated_at = _normalize_optional(
            relationship_payload.get("updatedAt") or relationship_payload.get("updated_at")
        ) or now
        self._write_relationships_to_issue_frontmatter(
            issue_path,
            current=current,
            preserve_body=True,
        )
        self._write_issue_metadata(
            repo,
            issue_number,
            issue_source_updated_at=None,
            fetched_at=now,
            relationship_source_updated_at=source_updated_at,
            relationship_fetched_at=now,
            preserve_existing=True,
        )
        return issue_path

    def write_issue_bundle(
        self,
        repo: GitHubRepository,
        issue: Mapping[str, Any],
        *,
        fetched_at: str | None = None,
    ) -> CacheWriteResult:
        """Write issue, comments, and relationships projections atomically per file."""

        issue_number = normalize_issue_number(issue.get("number") or issue.get("issue") or "")
        now = fetched_at or _utc_now()
        issue_dir = self.issue_dir(repo, issue_number)
        comments_dir = self.comments_dir(repo, issue_number)
        issue_dir.mkdir(parents=True, exist_ok=True)
        comments_dir.mkdir(parents=True, exist_ok=True)
        source_updated_at = _normalize_optional(issue.get("updatedAt") or issue.get("updated_at")) or now
        try:
            pending_relationships = self.read_pending_issue_relationships(repo, issue_number)
        except WorkflowCacheCorrupt:
            pending_relationships = []
        current_relationships = _relationships_from_issue(issue)

        issue_frontmatter = {
            "schema_version": SCHEMA_VERSION,
            "title": str(issue.get("title") or ""),
            "state": _normalize_state(issue.get("state")),
            "state_reason": _normalize_state_reason(issue.get("stateReason") or issue.get("state_reason")),
            "labels": _label_names(issue.get("labels")),
            "source_updated_at": source_updated_at,
        }
        projects = _project_items_for_frontmatter(issue.get("projectItems") or issue.get("projects"))
        if projects:
            issue_frontmatter["projects"] = projects
        issue_frontmatter["relationships"] = _relationship_frontmatter_block(
            current=current_relationships,
            pending=pending_relationships,
        )
        issue_path = self.issue_file(repo, issue_number)
        _atomic_write_text(issue_path, _format_markdown(issue_frontmatter, str(issue.get("body") or "")))

        metadata_path = self._write_issue_metadata(
            repo,
            issue_number,
            issue_source_updated_at=source_updated_at,
            fetched_at=now,
            relationship_source_updated_at=source_updated_at,
            relationship_fetched_at=now,
            preserve_existing=False,
        )

        comments_index = self._write_comments(repo, issue_number, issue, fetched_at=now)

        return CacheWriteResult(
            issue_dir=issue_dir,
            issue_file=issue_path,
            metadata_file=metadata_path,
            comments_index=comments_index,
            relationship_location=issue_path,
        )

    def _write_comments(
        self,
        repo: GitHubRepository,
        issue_number: str,
        issue: Mapping[str, Any],
        *,
        fetched_at: str,
    ) -> Path:
        comments_dir = self.comments_dir(repo, issue_number)
        raw_comments = _comments_from_issue(issue)
        index_comments: list[dict[str, Any]] = []
        expected_files: set[str] = {"index.yml"}

        for position, comment in enumerate(raw_comments, start=1):
            provider_comment_id, provider_node_id = _comment_ids(comment, fallback=str(position))
            created_at = _normalize_optional(comment.get("createdAt") or comment.get("created_at")) or fetched_at
            file_name = f"{_compact_timestamp(created_at)}-{_safe_file_segment(provider_comment_id)}.md"
            expected_files.add(file_name)

            author = _author_login(comment.get("author"))
            updated_at = _normalize_optional(comment.get("updatedAt") or comment.get("updated_at")) or created_at
            body = str(comment.get("body") or "")
            _atomic_write_text(
                comments_dir / file_name,
                _format_markdown({"author": author, "updated_at": updated_at}, body),
            )

            entry: dict[str, Any] = {
                "provider_comment_id": provider_comment_id,
                "author": author,
                "file": file_name,
            }
            if provider_node_id:
                entry["provider_node_id"] = provider_node_id
            index_comments.append(entry)

        for path in comments_dir.glob("*.md"):
            if path.name not in expected_files:
                path.unlink()

        index = {
            "schema_version": SCHEMA_VERSION,
            "source_updated_at": _latest_comment_timestamp(raw_comments)
            or _normalize_optional(issue.get("updatedAt") or issue.get("updated_at"))
            or fetched_at,
            "fetched_at": fetched_at,
            "comments": index_comments,
        }
        index_path = self.comments_index_file(repo, issue_number)
        _atomic_write_text(index_path, _dump_yaml(index))
        return index_path

    def _write_issue_metadata(
        self,
        repo: GitHubRepository,
        issue_number: str,
        *,
        issue_source_updated_at: str | None,
        fetched_at: str,
        relationship_source_updated_at: str | None,
        relationship_fetched_at: str,
        preserve_existing: bool,
    ) -> Path:
        metadata_path = self.issue_metadata_file(repo, issue_number)
        metadata: dict[str, Any] = {}
        if preserve_existing and metadata_path.is_file():
            metadata = _read_yaml_mapping(metadata_path)
            _require_schema(metadata, metadata_path)
        if issue_source_updated_at is not None or not preserve_existing:
            metadata["schema_version"] = SCHEMA_VERSION
            metadata["source_updated_at"] = issue_source_updated_at or fetched_at
            metadata["fetched_at"] = fetched_at
        else:
            metadata.setdefault("schema_version", SCHEMA_VERSION)
        metadata["relationships"] = {
            "source_updated_at": relationship_source_updated_at or relationship_fetched_at,
            "fetched_at": relationship_fetched_at,
        }
        _atomic_write_text(metadata_path, _dump_yaml(metadata))
        return metadata_path

    def _write_relationships_to_issue_frontmatter(
        self,
        issue_path: Path,
        *,
        current: Mapping[str, Any],
        preserve_body: bool,
    ) -> None:
        frontmatter, body = _read_frontmatter_markdown(issue_path)
        relationships = _frontmatter_relationship_block(frontmatter, issue_path, create=True)
        pending = relationships.get("pending")
        if pending is not None and not isinstance(pending, Mapping):
            raise WorkflowCacheCorrupt(f"issue relationship pending frontmatter must be a mapping: {issue_path}")
        pending_operations = pending.get("operations") if isinstance(pending, Mapping) else None
        if pending_operations is not None and not isinstance(pending_operations, list):
            raise WorkflowCacheCorrupt(f"issue relationship pending operations must be a list: {issue_path}")
        block = _relationship_frontmatter_block(current=current, pending=[])
        if pending_operations:
            block["pending"] = {"operations": pending_operations}
        frontmatter["relationships"] = block
        _atomic_write_text(issue_path, _format_markdown(frontmatter, body if preserve_body else body))

def _read_frontmatter_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not _FRONTMATTER_HANDLER.detect(text):
        raise WorkflowCacheCorrupt(f"missing markdown frontmatter: {path}")
    try:
        frontmatter_text, body = _FRONTMATTER_HANDLER.split(text)
    except ValueError as exc:
        raise WorkflowCacheCorrupt(f"unterminated markdown frontmatter: {path}") from exc
    if body.startswith("\n"):
        body = body[1:]
    data = _loads_frontmatter_mapping(frontmatter_text, path)
    return data, body


def _frontmatter_relationship_block(
    frontmatter: dict[str, Any],
    path: Path,
    *,
    create: bool,
) -> dict[str, Any] | None:
    raw = frontmatter.get("relationships")
    if raw is None:
        if not create:
            return None
        raw = {}
        frontmatter["relationships"] = raw
    if not isinstance(raw, dict):
        raise WorkflowCacheCorrupt(f"issue relationships frontmatter must be a mapping: {path}")
    return raw


def _read_frontmatter_current_relationships(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    frontmatter, _body = _read_frontmatter_markdown(path)
    relationships = _frontmatter_relationship_block(frontmatter, path, create=False)
    if relationships is None:
        return None
    current = relationships.get("current")
    if current is None:
        return {}
    if not isinstance(current, Mapping):
        raise WorkflowCacheCorrupt(f"issue relationship current frontmatter must be a mapping: {path}")
    return _relationships_from_issue(current)


def _read_frontmatter_pending_relationships(
    path: Path,
    *,
    target_kind: str,
    target_id: str,
) -> tuple[bool, list[PendingIssueRelationshipOperation]]:
    if not path.is_file():
        return False, []
    frontmatter, _body = _read_frontmatter_markdown(path)
    relationships = _frontmatter_relationship_block(frontmatter, path, create=False)
    if relationships is None or "pending" not in relationships:
        return False, []
    pending = relationships.get("pending")
    if pending is None:
        return True, []
    if not isinstance(pending, Mapping):
        raise WorkflowCacheCorrupt(f"issue relationship pending frontmatter must be a mapping: {path}")
    unknown = sorted(str(key) for key in pending if key != "operations")
    if unknown:
        raise WorkflowCacheCorrupt(f"unsupported pending relationship frontmatter fields in {path}: {', '.join(unknown)}")
    raw_operations = pending.get("operations")
    if raw_operations is None:
        return True, []
    if not isinstance(raw_operations, list):
        raise WorkflowCacheCorrupt(f"issue relationship pending operations must be a list: {path}")
    return True, [
        _pending_relationship_operation_from_mapping(
            item,
            path=path,
            target_kind=target_kind,
            target_id=target_id,
        )
        for item in raw_operations
    ]


def _relationship_frontmatter_block(
    *,
    current: Mapping[str, Any],
    pending: Iterable[PendingIssueRelationshipOperation],
) -> dict[str, Any]:
    block: dict[str, Any] = {"current": _compact_relationships_for_frontmatter(current)}
    pending_operations = [_pending_relationship_operation_to_frontmatter(operation) for operation in pending]
    if pending_operations:
        block["pending"] = {"operations": pending_operations}
    return block


def _compact_relationships_for_frontmatter(current: Mapping[str, Any]) -> dict[str, Any]:
    """Return the human-authored relationship projection stored in issue frontmatter."""

    compact: dict[str, Any] = {}

    parent = _compact_relationship_ref(
        current.get("parent") or current.get("parentIssue") or current.get("parent_issue")
    )
    if parent is not None:
        compact["parent"] = parent

    children = _compact_relationship_refs(
        current.get("children") or current.get("subIssues") or current.get("sub_issues")
    )
    if children:
        compact["children"] = children

    dependencies = current.get("dependencies")
    blocked_by = blocking = None
    if isinstance(dependencies, Mapping):
        blocked_by = dependencies.get("blocked_by") or dependencies.get("blockedBy")
        blocking = dependencies.get("blocking") or dependencies.get("blocks")
    blocked_by = blocked_by or current.get("blocked_by") or current.get("blockedBy")
    blocking = blocking or current.get("blocking") or current.get("blocks")
    dependency_payload: dict[str, Any] = {}
    blocked_by_refs = _compact_relationship_refs(blocked_by)
    blocking_refs = _compact_relationship_refs(blocking)
    if blocked_by_refs:
        dependency_payload["blocked_by"] = blocked_by_refs
    if blocking_refs:
        dependency_payload["blocking"] = blocking_refs
    if dependency_payload:
        compact["dependencies"] = dependency_payload

    related = _compact_relationship_refs(current.get("related"))
    if related:
        compact["related"] = related

    return compact


def _compact_relationship_refs(value: Any) -> list[int | str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if isinstance(nodes, list):
            return [ref for item in nodes if (ref := _compact_relationship_ref(item)) is not None]
        ref = _compact_relationship_ref(value)
        return [ref] if ref is not None else []
    if isinstance(value, list | tuple | set):
        return [ref for item in value if (ref := _compact_relationship_ref(item)) is not None]
    ref = _compact_relationship_ref(value)
    return [ref] if ref is not None else []


def _compact_relationship_ref(value: Any) -> int | str | None:
    if value is None:
        return None
    raw = value
    if isinstance(value, Mapping):
        raw = value.get("number") or value.get("issue") or value.get("target_ref") or value.get("target") or value.get("id")
        if raw is None:
            return None
    try:
        return int(normalize_issue_number(raw))
    except Exception:
        text = str(raw).strip()
        return text or None


def _pending_relationship_operation_to_frontmatter(
    operation: PendingIssueRelationshipOperation,
) -> dict[str, Any]:
    return {
        "action": operation.action,
        "relationship": operation.relationship,
        "target_ref": operation.target_ref,
        "replace_parent": operation.replace_parent,
    }


def _retarget_relationship_operations(
    operations: Iterable[PendingIssueRelationshipOperation],
    *,
    path: Path,
    target_kind: str,
    target_id: str,
) -> list[PendingIssueRelationshipOperation]:
    return [
        replace(
            operation,
            target_kind=target_kind,
            target_id=target_id,
            path=path,
        )
        for operation in operations
    ]


def _pending_relationship_key(operation: PendingIssueRelationshipOperation) -> tuple[str, str, str, bool]:
    return (
        operation.action,
        operation.relationship,
        operation.target_ref,
        operation.replace_parent,
    )


def _read_pending_comments(
    pending_dir: Path,
    *,
    target_kind: str,
    target_id: str,
) -> list[PendingIssueComment]:
    if not pending_dir.exists():
        return []
    if not pending_dir.is_dir():
        raise WorkflowCacheCorrupt(f"pending comments path is not a directory: {pending_dir}")

    comments: list[PendingIssueComment] = []
    for path in sorted(pending_dir.glob("*.md")):
        frontmatter, body = _read_frontmatter_markdown(path)
        if frontmatter.get("schema_version") is not None:
            _require_schema(frontmatter, path)
        if not body.strip():
            raise WorkflowCacheCorrupt(f"pending comment body is empty: {path}")
        comments.append(
            PendingIssueComment(
                target_kind=target_kind,
                target_id=target_id,
                path=path,
                body=body,
            )
        )
    return comments


def _read_pending_relationships(
    path: Path,
    *,
    target_kind: str,
    target_id: str,
) -> list[PendingIssueRelationshipOperation]:
    if not path.exists():
        return []
    if not path.is_file():
        raise WorkflowCacheCorrupt(f"pending relationships path is not a file: {path}")

    data = _read_yaml_mapping(path)
    if data.get("schema_version") is not None:
        _require_schema(data, path)
    return pending_relationship_operations_from_mapping(
        data,
        path=path,
        target_kind=target_kind,
        target_id=target_id,
    )


def pending_relationship_operations_from_mapping(
    data: Mapping[str, Any],
    *,
    path: Path,
    target_kind: str,
    target_id: str,
) -> list[PendingIssueRelationshipOperation]:
    """Normalize declarative or operation-list relationship intent."""

    operations: list[PendingIssueRelationshipOperation] = []
    raw_operations = data.get("operations")
    if raw_operations is not None:
        if not isinstance(raw_operations, list):
            raise WorkflowCacheCorrupt(f"pending relationship operations must be a list: {path}")
        for item in raw_operations:
            operations.append(
                _pending_relationship_operation_from_mapping(
                    item,
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )

    operations.extend(
        _pending_relationship_operations_from_declarative(
            data,
            path=path,
            target_kind=target_kind,
            target_id=target_id,
        )
    )

    if not operations:
        raise WorkflowCacheCorrupt(f"pending relationships file has no operations: {path}")
    return operations


def _pending_relationship_operation_from_mapping(
    item: Any,
    *,
    path: Path,
    target_kind: str,
    target_id: str,
) -> PendingIssueRelationshipOperation:
    if not isinstance(item, Mapping):
        raise WorkflowCacheCorrupt(f"pending relationship operation must be a mapping: {path}")
    relationship = _normalize_relationship_name(
        _required_relationship_value(item, path, "relationship", "type", "kind")
    )
    action = _normalize_relationship_action(item.get("action") or item.get("op") or "add", path)
    target_ref = _relationship_target_ref(item, path)
    replace_parent = bool(item.get("replace_parent") or item.get("replaceParent"))
    if relationship == "parent" and action == "add" and not (
        item.get("replace_parent") is not None or item.get("replaceParent") is not None
    ):
        replace_parent = True
    return PendingIssueRelationshipOperation(
        target_kind=target_kind,
        target_id=target_id,
        path=path,
        action=action,
        relationship=relationship,
        target_ref=target_ref,
        replace_parent=replace_parent,
    )


def _pending_relationship_operations_from_declarative(
    data: Mapping[str, Any],
    *,
    path: Path,
    target_kind: str,
    target_id: str,
) -> list[PendingIssueRelationshipOperation]:
    operations: list[PendingIssueRelationshipOperation] = []
    ignored = {"schema_version", "source_updated_at", "fetched_at", "operations"}

    if "parent" in data:
        operations.extend(
            _declarative_relationship_values(
                data["parent"],
                relationship="parent",
                path=path,
                target_kind=target_kind,
                target_id=target_id,
                default_replace_parent=True,
            )
        )

    if "children" in data:
        operations.extend(
            _declarative_relationship_values(
                data["children"],
                relationship="child",
                path=path,
                target_kind=target_kind,
                target_id=target_id,
            )
        )

    dependencies = data.get("dependencies")
    if isinstance(dependencies, Mapping):
        if "blocked_by" in dependencies or "blockedBy" in dependencies:
            operations.extend(
                _declarative_relationship_values(
                    dependencies.get("blocked_by") or dependencies.get("blockedBy"),
                    relationship="blocked_by",
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )
        if "blocking" in dependencies or "blocks" in dependencies:
            operations.extend(
                _declarative_relationship_values(
                    dependencies.get("blocking") or dependencies.get("blocks"),
                    relationship="blocking",
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )
    elif dependencies is not None:
        raise WorkflowCacheCorrupt(f"pending relationship dependencies must be a mapping: {path}")

    for key, relationship in (("blocked_by", "blocked_by"), ("blockedBy", "blocked_by"), ("blocking", "blocking"), ("blocks", "blocking"), ("related", "related")):
        if key in data:
            operations.extend(
                _declarative_relationship_values(
                    data[key],
                    relationship=relationship,
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )

    unknown = sorted(str(key) for key in data if key not in ignored and key not in {"parent", "children", "dependencies", "blocked_by", "blockedBy", "blocking", "blocks", "related"})
    if unknown:
        raise WorkflowCacheCorrupt(f"unsupported pending relationship fields in {path}: {', '.join(unknown)}")
    return operations


def _declarative_relationship_values(
    value: Any,
    *,
    relationship: str,
    path: Path,
    target_kind: str,
    target_id: str,
    default_replace_parent: bool = False,
) -> list[PendingIssueRelationshipOperation]:
    if value is None:
        return []
    if isinstance(value, Mapping) and any(key in value for key in ("add", "remove", "delete", "unset")):
        operations: list[PendingIssueRelationshipOperation] = []
        for key, action in (("add", "add"), ("remove", "remove"), ("delete", "remove"), ("unset", "remove")):
            if key in value:
                parsed = _declarative_relationship_values(
                    value[key],
                    relationship=relationship,
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                    default_replace_parent=default_replace_parent,
                )
                if action == "remove":
                    parsed = [
                        PendingIssueRelationshipOperation(
                            target_kind=operation.target_kind,
                            target_id=operation.target_id,
                            path=operation.path,
                            action="remove",
                            relationship=operation.relationship,
                            target_ref=operation.target_ref,
                            replace_parent=operation.replace_parent,
                        )
                        for operation in parsed
                    ]
                operations.extend(parsed)
        return operations
    if isinstance(value, list | tuple | set):
        result: list[PendingIssueRelationshipOperation] = []
        for item in value:
            result.extend(
                _declarative_relationship_values(
                    item,
                    relationship=relationship,
                    path=path,
                    target_kind=target_kind,
                    target_id=target_id,
                    default_replace_parent=default_replace_parent,
                )
            )
        return result

    action = "add"
    replace_parent = default_replace_parent
    if isinstance(value, Mapping):
        action = _normalize_relationship_action(value.get("action") or value.get("op") or action, path)
        replace_parent = _relationship_bool(value, "replace_parent", "replaceParent", default=replace_parent)
    target_ref = _relationship_target_ref(value, path)
    return [
        PendingIssueRelationshipOperation(
            target_kind=target_kind,
            target_id=target_id,
            path=path,
            action=action,
            relationship=relationship,
            target_ref=target_ref,
            replace_parent=replace_parent,
        )
    ]


def _required_relationship_value(item: Mapping[str, Any], path: Path, *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return value
    raise WorkflowCacheCorrupt(f"pending relationship operation is missing {keys[0]}: {path}")


def _relationship_target_ref(value: Any, path: Path) -> str:
    if isinstance(value, Mapping):
        for key in ("issue", "target", "target_ref", "ref", "number", "id"):
            raw = value.get(key)
            if raw is not None:
                text = str(raw).strip()
                if text:
                    return text
        raise WorkflowCacheCorrupt(f"pending relationship operation is missing target issue: {path}")
    text = str(value).strip()
    if not text:
        raise WorkflowCacheCorrupt(f"pending relationship target is empty: {path}")
    return text


def _normalize_relationship_name(value: Any) -> str:
    normalized = str(value).strip().lower().replace("-", "_")
    aliases = {
        "children": "child",
        "sub_issue": "child",
        "sub_issues": "child",
        "subissue": "child",
        "subissues": "child",
        "blockedby": "blocked_by",
        "blocked_by": "blocked_by",
        "depends_on": "blocked_by",
        "dependency": "blocked_by",
        "blocks": "blocking",
    }
    return aliases.get(normalized, normalized)


def _normalize_relationship_action(value: Any, path: Path) -> str:
    normalized = str(value).strip().lower().replace("-", "_")
    aliases = {
        "set": "add",
        "create": "add",
        "append": "add",
        "delete": "remove",
        "unset": "remove",
    }
    action = aliases.get(normalized, normalized)
    if action not in {"add", "remove"}:
        raise WorkflowCacheCorrupt(f"unsupported pending relationship action in {path}: {value}")
    return action


def _relationship_bool(value: Mapping[str, Any], *keys: str, default: bool) -> bool:
    for key in keys:
        if key in value:
            raw = value.get(key)
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)
    return default


def _normalize_freshness_target(target: str) -> str:
    normalized = str(target).strip().lower().replace("-", "_")
    aliases = {
        "issue_body": "issue",
        "body": "issue",
        "comment": "comments",
        "issue_comments": "comments",
        "relationship": "relationships",
        "issue_relationships": "relationships",
    }
    return aliases.get(normalized, normalized)


def _parse_freshness_timestamp(value: str | None) -> datetime | None:
    text = _normalize_optional(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    return _loads_yaml_mapping(path.read_text(encoding="utf-8"), path)


def _loads_yaml_mapping(text: str, path: Path) -> dict[str, Any]:
    try:
        value = _parse_yaml_subset(text)
    except Exception as exc:
        raise WorkflowCacheCorrupt(f"could not parse YAML: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowCacheCorrupt(f"YAML must be a mapping: {path}")
    return value


def _loads_frontmatter_mapping(text: str, path: Path) -> dict[str, Any]:
    try:
        value = _FRONTMATTER_HANDLER.load(text)
    except Exception as exc:
        raise WorkflowCacheCorrupt(f"could not parse YAML: {path}: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise WorkflowCacheCorrupt(f"YAML must be a mapping: {path}")
    return value


def _require_schema(data: Mapping[str, Any], path: Path) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise WorkflowCacheCorrupt(f"unsupported schema_version in {path}")


def _format_markdown(frontmatter: Mapping[str, Any], body: str) -> str:
    return f"---\n{_dump_frontmatter_yaml(frontmatter)}---\n\n{body}"


def _dump_frontmatter_yaml(data: Mapping[str, Any]) -> str:
    return _FRONTMATTER_HANDLER.export(dict(data), sort_keys=False) + "\n"


def _dump_yaml(data: Mapping[str, Any]) -> str:
    return "\n".join(_dump_mapping_lines(data, 0)) + "\n"


def _dump_mapping_lines(data: Mapping[str, Any], indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, Mapping):
            lines.append(f"{prefix}{key}:")
            lines.extend(_dump_mapping_lines(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            lines.extend(_dump_list_lines(value, indent + 2))
        else:
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")
    return lines


def _dump_list_lines(values: Iterable[Any], indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for value in values:
        if isinstance(value, Mapping):
            items = list(value.items())
            if not items:
                lines.append(f"{prefix}- {{}}")
                continue
            first_key, first_value = items[0]
            if isinstance(first_value, (Mapping, list)):
                lines.append(f"{prefix}- {first_key}:")
                lines.extend(_dump_nested_value(first_value, indent + 4))
            else:
                lines.append(f"{prefix}- {first_key}: {_dump_scalar(first_value)}")
            for key, nested_value in items[1:]:
                if isinstance(nested_value, Mapping):
                    lines.append(f"{prefix}  {key}:")
                    lines.extend(_dump_mapping_lines(nested_value, indent + 4))
                elif isinstance(nested_value, list):
                    lines.append(f"{prefix}  {key}:")
                    lines.extend(_dump_list_lines(nested_value, indent + 4))
                else:
                    lines.append(f"{prefix}  {key}: {_dump_scalar(nested_value)}")
        elif isinstance(value, list):
            lines.append(f"{prefix}-")
            lines.extend(_dump_list_lines(value, indent + 2))
        else:
            lines.append(f"{prefix}- {_dump_scalar(value)}")
    return lines


def _dump_nested_value(value: Any, indent: int) -> list[str]:
    if isinstance(value, Mapping):
        return _dump_mapping_lines(value, indent)
    if isinstance(value, list):
        return _dump_list_lines(value, indent)
    return [f"{' ' * indent}{_dump_scalar(value)}"]


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_.@/+:-]+", text) and text.lower() not in {"null", "true", "false"}:
        return text
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


@dataclass(frozen=True)
class _YamlLine:
    indent: int
    text: str


def _parse_yaml_subset(text: str) -> Any:
    lines = _yaml_lines(text)
    if not lines:
        return {}
    index = 0

    def parse_block(indent: int) -> Any:
        nonlocal index
        if index >= len(lines) or lines[index].indent < indent:
            return {}
        if lines[index].text.startswith("- ") or lines[index].text == "-":
            return parse_list(indent)
        return parse_mapping(indent)

    def parse_mapping(indent: int) -> dict[str, Any]:
        nonlocal index
        result: dict[str, Any] = {}
        while index < len(lines):
            line = lines[index]
            if line.indent < indent:
                break
            if line.indent != indent:
                raise ValueError(f"unexpected indentation: {line.text}")
            if line.text.startswith("- ") or line.text == "-":
                break
            key, raw_value = _split_yaml_key_value(line.text)
            index += 1
            if raw_value is None:
                if index < len(lines) and lines[index].indent > indent:
                    result[key] = parse_block(lines[index].indent)
                else:
                    result[key] = None
            else:
                result[key] = _parse_scalar(raw_value)
        return result

    def parse_list(indent: int) -> list[Any]:
        nonlocal index
        result: list[Any] = []
        while index < len(lines):
            line = lines[index]
            if line.indent < indent:
                break
            if line.indent != indent or not (line.text.startswith("- ") or line.text == "-"):
                break
            raw_item = line.text[1:].strip()
            index += 1
            if not raw_item:
                if index < len(lines) and lines[index].indent > indent:
                    result.append(parse_block(lines[index].indent))
                else:
                    result.append(None)
                continue
            if ":" in raw_item and not _looks_like_scalar_with_colon(raw_item):
                key, raw_value = _split_yaml_key_value(raw_item)
                item: dict[str, Any] = {}
                if raw_value is None:
                    if index < len(lines) and lines[index].indent > indent:
                        item[key] = parse_block(lines[index].indent)
                    else:
                        item[key] = None
                else:
                    item[key] = _parse_scalar(raw_value)
                if index < len(lines) and lines[index].indent > indent:
                    extra = parse_mapping(lines[index].indent)
                    item.update(extra)
                result.append(item)
            else:
                result.append(_parse_scalar(raw_item))
        return result

    parsed = parse_block(lines[0].indent)
    if index != len(lines):
        raise ValueError("unparsed YAML content remains")
    return parsed


def _yaml_lines(text: str) -> list[_YamlLine]:
    result: list[_YamlLine] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        stripped_comment = _strip_yaml_comment(raw).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        result.append(_YamlLine(indent=indent, text=stripped_comment.strip()))
    return result


def _split_yaml_key_value(text: str) -> tuple[str, str | None]:
    if ":" not in text:
        raise ValueError(f"expected key/value line: {text}")
    key, raw_value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError("empty key")
    raw_value = raw_value.strip()
    return key, raw_value if raw_value else None


def _looks_like_scalar_with_colon(text: str) -> bool:
    quote: str | None = None
    for index, char in enumerate(text):
        if char in {'"', "'"}:
            quote = char if quote is None else None if quote == char else quote
        if char == ":" and quote is None:
            return index + 1 < len(text) and not text[index + 1].isspace()
    return False


def _parse_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "null" or raw == "~":
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.startswith('"') and raw.endswith('"'):
        return bytes(raw[1:-1], "utf-8").decode("unicode_escape")
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    if re.fullmatch(r"-?\d+", raw):
        try:
            return int(raw)
        except ValueError:
            return raw
    return raw


def _strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _move_path_if_exists(source: Path, destination: Path) -> Path | None:
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_dir():
            for child in source.iterdir():
                os.replace(child, destination / child.name)
            source.rmdir()
            return destination
        destination.unlink()
    os.replace(source, destination)
    return destination


def _remove_empty_parents(path: Path, *, stop_at: Path) -> None:
    current = path
    stop = stop_at.resolve(strict=False)
    while current.resolve(strict=False) != stop:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _normalize_state(value: Any) -> str:
    if value is None:
        return "open"
    return str(value).strip().lower()


def _normalize_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_state_reason(value: Any) -> str | None:
    text = _normalize_optional(value)
    return text.lower() if text is not None else None


def _label_names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if nodes is not None:
            return _label_names(nodes)
        name = value.get("name")
        return [str(name)] if name else []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        labels: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                name = item.get("name")
                if name:
                    labels.append(str(name))
            elif item is not None:
                labels.append(str(item))
        return labels
    return [str(value)]


def _project_items_for_frontmatter(value: Any) -> list[dict[str, Any]]:
    items = _project_item_list(value)
    projects: list[dict[str, Any]] = []
    for item in items:
        project = item.get("project")
        project_data = project if isinstance(project, Mapping) else item
        entry: dict[str, Any] = {}

        owner = _project_owner(project_data) or _project_owner(item)
        if owner:
            entry["owner"] = owner
        number = _project_scalar(project_data, "number", "projectNumber")
        if number is not None:
            try:
                entry["number"] = int(str(number))
            except ValueError:
                entry["number"] = str(number)
        title = _project_scalar(project_data, "title", "name", "projectTitle")
        if title is not None:
            entry["title"] = str(title)
        url = _project_scalar(project_data, "url", "projectUrl")
        if url is not None:
            entry["url"] = str(url)
        item_id = _project_scalar(item, "id", "node_id", "nodeId", "item_id", "itemId")
        if item_id is not None:
            entry["item_id"] = str(item_id)
        status = _project_item_status(item)
        if status is not None:
            entry["status"] = status

        if entry:
            projects.append(entry)
    return projects


def _project_item_list(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if isinstance(nodes, list):
            return [item for item in nodes if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _project_scalar(value: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        raw = value.get(key)
        if raw is not None and str(raw).strip():
            return raw
    return None


def _project_owner(value: Mapping[str, Any]) -> str | None:
    raw_owner = value.get("owner")
    if isinstance(raw_owner, Mapping):
        owner = _project_scalar(raw_owner, "login", "name")
        return str(owner) if owner is not None else None
    if raw_owner is not None and str(raw_owner).strip():
        return str(raw_owner)
    return None


def _project_item_status(item: Mapping[str, Any]) -> str | None:
    direct = item.get("status")
    if isinstance(direct, Mapping):
        value = _project_scalar(direct, "name", "title", "value")
        return str(value) if value is not None else None
    if direct is not None and str(direct).strip():
        return str(direct)

    field_values = item.get("fieldValues") or item.get("field_values")
    for field_value in _project_item_list(field_values):
        field = field_value.get("field")
        field_name = None
        if isinstance(field, Mapping):
            field_name = _project_scalar(field, "name")
        elif field is not None:
            field_name = field
        if str(field_name or "").strip().lower() != "status":
            continue
        status = _project_scalar(field_value, "name", "text", "value", "title")
        if status is not None:
            return str(status)
    return None


def _comments_from_issue(issue: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    comments = issue.get("comments") or []
    if isinstance(comments, Mapping):
        nodes = comments.get("nodes")
        if isinstance(nodes, list):
            comments = nodes
    if not isinstance(comments, list):
        return []
    return [item for item in comments if isinstance(item, Mapping)]


def _comment_ids(comment: Mapping[str, Any], *, fallback: str) -> tuple[str, str | None]:
    for key in ("databaseId", "databaseID", "database_id"):
        value = comment.get(key)
        if value is not None:
            return str(value), _node_id(comment)

    url = str(comment.get("url") or "")
    match = re.search(r"issuecomment-(\d+)", url)
    if match:
        return match.group(1), _node_id(comment)

    raw_id = comment.get("id")
    if raw_id is not None:
        text = str(raw_id)
        if text.isdigit():
            return text, _node_id(comment)
        return text, text

    return fallback, _node_id(comment)


def _node_id(comment: Mapping[str, Any]) -> str | None:
    for key in ("nodeId", "nodeID", "node_id"):
        value = comment.get(key)
        if value:
            return str(value)
    raw_id = comment.get("id")
    if raw_id is not None and not str(raw_id).isdigit():
        return str(raw_id)
    return None


def _author_login(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("login", "name", "username", "displayName"):
            raw = value.get(key)
            if raw:
                return str(raw)
    if value:
        return str(value)
    return "unknown"


def _latest_comment_timestamp(comments: list[Mapping[str, Any]]) -> str | None:
    values = [
        str(value)
        for comment in comments
        for value in (comment.get("updatedAt"), comment.get("updated_at"), comment.get("createdAt"), comment.get("created_at"))
        if value
    ]
    if not values:
        return None
    return max(values)


def _relationships_from_issue(issue: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    parent = _relationship_item(
        issue.get("parent") or issue.get("parentIssue") or issue.get("parent_issue")
    )
    if parent:
        result["parent"] = parent

    children = _relationship_items(
        issue.get("children") or issue.get("subIssues") or issue.get("sub_issues")
    )
    if children:
        result["children"] = children

    dependencies = issue.get("dependencies")
    blocked_by = blocking = None
    if isinstance(dependencies, Mapping):
        blocked_by = dependencies.get("blocked_by") or dependencies.get("blockedBy")
        blocking = dependencies.get("blocking") or dependencies.get("blocks")
    blocked_by = blocked_by or issue.get("blocked_by") or issue.get("blockedBy")
    blocking = blocking or issue.get("blocking") or issue.get("blocks")
    dependency_payload: dict[str, Any] = {}
    blocked_by_items = _relationship_items(blocked_by)
    blocking_items = _relationship_items(blocking)
    if blocked_by_items:
        dependency_payload["blocked_by"] = blocked_by_items
    if blocking_items:
        dependency_payload["blocking"] = blocking_items
    if dependency_payload:
        result["dependencies"] = dependency_payload

    related = _relationship_items(issue.get("related"))
    if related:
        result["related"] = related

    return result


def _relationship_items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        nodes = value.get("nodes")
        if isinstance(nodes, list):
            return [_relationship_item(item) for item in nodes if _relationship_item(item)]
        item = _relationship_item(value)
        return [item] if item else []
    if isinstance(value, list | tuple | set):
        result: list[dict[str, Any]] = []
        for item in value:
            normalized = _relationship_item(item)
            if normalized:
                result.append(normalized)
        return result
    item = _relationship_item(value)
    return [item] if item else []


def _relationship_item(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        number = value.get("number") or value.get("issue") or value.get("id")
        if number is None:
            return None
        item: dict[str, Any] = {"number": int(normalize_issue_number(number))}
        if value.get("title") is not None:
            item["title"] = str(value.get("title"))
        if value.get("state") is not None:
            item["state"] = _normalize_state(value.get("state"))
        state_reason = value.get("stateReason") or value.get("state_reason")
        item["state_reason"] = _normalize_state_reason(state_reason)
        return item
    try:
        return {"number": int(normalize_issue_number(value))}
    except Exception:
        return None


def _compact_timestamp(value: str) -> str:
    normalized = value.strip()
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", normalized)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}T{match.group(4)}{match.group(5)}{match.group(6)}Z"
    return _safe_file_segment(normalized) or "unknown-time"


def _timestamp_from_comment_filename(file_name: str) -> str | None:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})T(\d{2})(\d{2})(\d{2})Z-", file_name)
    if not match:
        return None
    return f"{match.group(1)}T{match.group(2)}:{match.group(3)}:{match.group(4)}Z"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _same_github_repo(left: GitHubRepository, right: GitHubRepository) -> bool:
    return (
        left.host.lower(),
        left.owner.lower(),
        left.name.lower(),
    ) == (
        right.host.lower(),
        right.owner.lower(),
        right.name.lower(),
    )


def _safe_path_segment(value: str) -> str:
    text = str(value).strip().strip("/")
    if not text or text in {".", ".."} or "/" in text:
        raise WorkflowCacheError(f"unsafe cache path segment: {value}")
    return text


def _safe_file_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip(".-")
