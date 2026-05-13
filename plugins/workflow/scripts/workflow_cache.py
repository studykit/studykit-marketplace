#!/usr/bin/env python3
"""Local workflow provider read cache projections."""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from workflow_github import GitHubRepository, normalize_issue_number

CACHE_ROOT_NAME = ".workflow-cache"
SCHEMA_VERSION = 1


class WorkflowCacheError(RuntimeError):
    """Base error for workflow cache failures."""


class WorkflowCacheMiss(WorkflowCacheError):
    """Raised when a cache projection does not exist."""


class WorkflowCacheCorrupt(WorkflowCacheError):
    """Raised when a cache projection exists but cannot be parsed."""


@dataclass(frozen=True)
class CacheWriteResult:
    """Paths written for one cache projection refresh."""

    issue_dir: Path
    issue_file: Path
    comments_index: Path
    relationships_file: Path

    def to_json(self) -> dict[str, str]:
        return {
            "issue_dir": str(self.issue_dir),
            "issue_file": str(self.issue_file),
            "comments_index": str(self.comments_index),
            "relationships_file": str(self.relationships_file),
        }


class GitHubIssueCache:
    """Repo-local cache for GitHub issue read projections."""

    def __init__(self, root: Path):
        self.root = root

    @classmethod
    def for_project(cls, project: Path) -> GitHubIssueCache:
        return cls(project.expanduser().resolve(strict=False) / CACHE_ROOT_NAME)

    def issue_dir(self, repo: GitHubRepository, issue: int | str) -> Path:
        return (
            self.root
            / "github"
            / _safe_path_segment(repo.host)
            / _safe_path_segment(repo.owner)
            / _safe_path_segment(repo.name)
            / "issues"
            / normalize_issue_number(issue)
        )

    def issue_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "issue.md"

    def comments_dir(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "comments"

    def comments_index_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.comments_dir(repo, issue) / "index.yml"

    def relationships_file(self, repo: GitHubRepository, issue: int | str) -> Path:
        return self.issue_dir(repo, issue) / "relationships.yml"

    def has_issue_projection(self, repo: GitHubRepository, issue: int | str) -> bool:
        return self.issue_file(repo, issue).is_file()

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
            for key in ("title", "state", "state_reason", "labels", "source_updated_at", "fetched_at"):
                if key not in frontmatter:
                    raise WorkflowCacheCorrupt(f"missing issue frontmatter field {key}: {issue_path}")

            labels = frontmatter.get("labels")
            if labels is None:
                labels = []
            if not isinstance(labels, list):
                raise WorkflowCacheCorrupt(f"issue labels must be a list: {issue_path}")

            payload: dict[str, Any] = {
                "number": int(normalize_issue_number(issue)),
                "title": str(frontmatter.get("title") or ""),
                "state": frontmatter.get("state"),
                "stateReason": frontmatter.get("state_reason"),
                "labels": [str(label) for label in labels],
                "updatedAt": frontmatter.get("source_updated_at"),
                "repository": repo.to_json(),
                "cache": {
                    "hit": True,
                    "issue_file": str(issue_path),
                    "fetchedAt": frontmatter.get("fetched_at"),
                    "sourceUpdatedAt": frontmatter.get("source_updated_at"),
                },
            }
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
        path = self.relationships_file(repo, issue)
        if not path.is_file():
            raise WorkflowCacheMiss(f"relationships cache does not exist: {path}")
        try:
            data = _read_yaml_mapping(path)
            _require_schema(data, path)
            return dict(data)
        except WorkflowCacheError:
            raise
        except Exception as exc:
            raise WorkflowCacheCorrupt(f"could not read relationships cache {path}: {exc}") from exc

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

        issue_frontmatter = {
            "schema_version": SCHEMA_VERSION,
            "title": str(issue.get("title") or ""),
            "state": _normalize_state(issue.get("state")),
            "state_reason": _normalize_state_reason(issue.get("stateReason") or issue.get("state_reason")),
            "labels": _label_names(issue.get("labels")),
            "source_updated_at": _normalize_optional(issue.get("updatedAt") or issue.get("updated_at")) or now,
            "fetched_at": now,
        }
        issue_path = self.issue_file(repo, issue_number)
        _atomic_write_text(issue_path, _format_markdown(issue_frontmatter, str(issue.get("body") or "")))

        comments_index = self._write_comments(repo, issue_number, issue, fetched_at=now)
        relationships_file = self._write_relationships(repo, issue_number, issue, fetched_at=now)

        return CacheWriteResult(
            issue_dir=issue_dir,
            issue_file=issue_path,
            comments_index=comments_index,
            relationships_file=relationships_file,
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

    def _write_relationships(
        self,
        repo: GitHubRepository,
        issue_number: str,
        issue: Mapping[str, Any],
        *,
        fetched_at: str,
    ) -> Path:
        relationships = _relationships_from_issue(issue)
        data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "source_updated_at": _normalize_optional(issue.get("updatedAt") or issue.get("updated_at")) or fetched_at,
            "fetched_at": fetched_at,
        }
        data.update(relationships)
        path = self.relationships_file(repo, issue_number)
        _atomic_write_text(path, _dump_yaml(data))
        return path


def _read_frontmatter_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise WorkflowCacheCorrupt(f"missing markdown frontmatter: {path}")
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end < 0:
        raise WorkflowCacheCorrupt(f"unterminated markdown frontmatter: {path}")
    frontmatter_text = text[4:end]
    body = text[end + len(marker) :]
    if body.startswith("\n"):
        body = body[1:]
    data = _loads_yaml_mapping(frontmatter_text, path)
    return data, body


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


def _require_schema(data: Mapping[str, Any], path: Path) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise WorkflowCacheCorrupt(f"unsupported schema_version in {path}")


def _format_markdown(frontmatter: Mapping[str, Any], body: str) -> str:
    return f"---\n{_dump_yaml(frontmatter)}---\n\n{body}"


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


def _safe_path_segment(value: str) -> str:
    text = str(value).strip().strip("/")
    if not text or text in {".", ".."} or "/" in text:
        raise WorkflowCacheError(f"unsafe cache path segment: {value}")
    return text


def _safe_file_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip(".-")
