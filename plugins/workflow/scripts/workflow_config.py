#!/usr/bin/env python3
"""Load and validate repository-local workflow configuration.

The workflow plugin uses a repository-root ``.workflow/config.yml`` even when
the canonical artifacts live in remote issue and knowledge providers. This
module is the shared loader for resolver, hooks, setup, and provider wrappers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

CONFIG_DIR_NAME = ".workflow"
CONFIG_FILE_NAME = "config.yml"
CONFIG_NAME = f"{CONFIG_DIR_NAME}/{CONFIG_FILE_NAME}"
CONFIG_RELATIVE_PATH = Path(CONFIG_DIR_NAME) / CONFIG_FILE_NAME

ISSUE_PROVIDERS = {"github", "jira", "filesystem"}
KNOWLEDGE_PROVIDERS = {"github", "confluence", "filesystem"}

PROVIDER_ALIASES = {
    "fs": "filesystem",
    "file": "filesystem",
    "files": "filesystem",
    "local": "filesystem",
    "local-files": "filesystem",
    "local_files": "filesystem",
    "github-issues": "github",
    "github_issue": "github",
    "github-issue": "github",
    "gh-issues": "github",
    "gh_issue": "github",
    "gh-issue": "github",
    "github-wiki": "github",
    "github_wiki": "github",
    "githubwiki": "github",
    "github-knowledge": "github",
    "github_knowledge": "github",
    "github-repo-wiki": "github",
    "repo-wiki": "github",
    "repo_wiki": "github",
    "repository-wiki": "github",
    "repository_wiki": "github",
    "wiki": "github",
    "jira-issue": "jira",
    "jira_issue": "jira",
    "jira-issues": "jira",
    "jira_issues": "jira",
    "confluence-page": "confluence",
    "confluence_page": "confluence",
    "confluence-pages": "confluence",
    "confluence_pages": "confluence",
    "conf": "confluence",
}

LOCAL_PROJECTION_MODES = {"none", "ephemeral", "persistent"}
LOCAL_PROJECTION_ALIASES = {
    "off": "none",
    "disabled": "none",
    "disable": "none",
    "no": "none",
    "false": "none",
    "temp": "ephemeral",
    "temporary": "ephemeral",
    "cache": "ephemeral",
    "cached": "ephemeral",
    "mirror": "persistent",
    "mirrored": "persistent",
    "committed": "persistent",
}

COMMIT_REF_STYLES = {"provider-native", "issue-prefix", "issue-suffix", "disabled"}
COMMIT_REF_STYLE_ALIASES = {
    "provider_native": "provider-native",
    "native": "provider-native",
    "provider": "provider-native",
    "issue_prefix": "issue-prefix",
    "prefix": "issue-prefix",
    "prefixed": "issue-prefix",
    "issue_suffix": "issue-suffix",
    "suffix": "issue-suffix",
    "suffixed": "issue-suffix",
    "none": "disabled",
    "off": "disabled",
    "disable": "disabled",
    "false": "disabled",
}

ISSUE_ID_FORMATS = {"github", "jira", "number"}
ISSUE_ID_FORMAT_ALIASES = {
    "gh": "github",
    "github-issue": "github",
    "github-issues": "github",
    "github-native": "github",
    "jira-issue": "jira",
    "jira-issues": "jira",
    "jira-native": "jira",
    "numeric": "number",
    "plain-number": "number",
    "plain_number": "number",
}
PROVIDER_NATIVE_ISSUE_ID_FORMATS = {
    "github": "github",
    "jira": "jira",
    "filesystem": "number",
}


class WorkflowConfigError(ValueError):
    """Raised when ``.workflow/config.yml`` is missing or invalid."""


@dataclass(frozen=True)
class ProviderConfig:
    """Provider configuration for one workflow role."""

    role: str
    kind: str
    settings: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "kind": self.kind,
            "settings": dict(self.settings),
        }


@dataclass(frozen=True)
class LocalProjectionConfig:
    """Local projection configuration."""

    mode: str = "none"
    path: str | None = None
    settings: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        result = {"mode": self.mode, "path": self.path}
        if self.settings:
            result["settings"] = dict(self.settings)
        return result


@dataclass(frozen=True)
class CommitRefsConfig:
    """Commit reference configuration."""

    enabled: bool = True
    style: str = "provider-native"
    settings: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        result = {"enabled": self.enabled, "style": self.style}
        if self.settings:
            result["settings"] = dict(self.settings)
        return result


@dataclass(frozen=True)
class WorkflowConfig:
    """Validated workflow configuration."""

    path: Path
    root: Path
    version: int
    mode: str
    issues: ProviderConfig
    knowledge: ProviderConfig
    issue_id_format: str
    local_projection: LocalProjectionConfig
    commit_refs: CommitRefsConfig
    raw: Mapping[str, Any] = field(default_factory=dict)

    def provider_for_role(self, role: str) -> str:
        normalized_role = normalize_role(role)
        if normalized_role == "issue":
            return self.issues.kind
        return self.knowledge.kind

    def to_json(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "root": str(self.root),
            "version": self.version,
            "mode": self.mode,
            "providers": {
                "issues": self.issues.to_json(),
                "knowledge": self.knowledge.to_json(),
            },
            "issue_id_format": self.issue_id_format,
            "local_projection": self.local_projection.to_json(),
            "commit_refs": self.commit_refs.to_json(),
        }


def find_workflow_config(project: Path) -> Path | None:
    """Find ``.workflow/config.yml`` from ``project`` upward."""

    current = project.expanduser().resolve()
    if current.is_file() and _is_workflow_config_path(current):
        return current
    if current.is_file():
        current = current.parent
    for candidate_dir in (current, *current.parents):
        candidate = candidate_dir / CONFIG_RELATIVE_PATH
        if candidate.exists():
            return candidate
    return None


def load_workflow_config(project: Path, *, require: bool = False) -> WorkflowConfig | None:
    """Load and validate ``.workflow/config.yml`` for ``project``.

    Returns ``None`` when the file is absent and ``require`` is false.
    """

    config_path = find_workflow_config(project)
    if config_path is None:
        if require:
            raise WorkflowConfigError(f"{CONFIG_NAME} was not found for {project}")
        return None

    raw = _load_yaml_mapping(config_path)
    return parse_workflow_config(raw, path=config_path)


def parse_workflow_config(raw: Mapping[str, Any], *, path: Path) -> WorkflowConfig:
    """Validate a raw config mapping."""

    version = _parse_version(raw.get("version", 1), path=path)
    mode = _parse_mode(raw.get("mode", "remote-native"), path=path)

    issues = _parse_provider(raw, role="issue", slot="issues", path=path)
    knowledge = _parse_provider(raw, role="knowledge", slot="knowledge", path=path)
    issue_id_format = _parse_issue_id_format(
        raw.get("issue_id_format"),
        issue_provider=issues.kind,
        path=path,
    )
    local_projection = _parse_local_projection(raw.get("local_projection"), path=path)
    commit_refs = _parse_commit_refs(raw.get("commit_refs"), path=path)

    return WorkflowConfig(
        path=path.resolve(),
        root=_project_root_from_config_path(path),
        version=version,
        mode=mode,
        issues=issues,
        knowledge=knowledge,
        issue_id_format=issue_id_format,
        local_projection=local_projection,
        commit_refs=commit_refs,
        raw=dict(raw),
    )


def _is_workflow_config_path(path: Path) -> bool:
    return path.name == CONFIG_FILE_NAME and path.parent.name == CONFIG_DIR_NAME


def _project_root_from_config_path(path: Path) -> Path:
    resolved = path.resolve()
    if _is_workflow_config_path(resolved):
        return resolved.parent.parent
    return resolved.parent


def normalize_role(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"issues", "issue-provider", "work", "work-item", "work-items"}:
        normalized = "issue"
    if normalized in {"knowledge-provider", "page", "pages", "wiki", "doc", "docs", "document"}:
        normalized = "knowledge"
    if normalized not in {"issue", "knowledge"}:
        raise WorkflowConfigError(f"unsupported provider role: {value}")
    return normalized


def normalize_provider(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace("_", "-")
    if not normalized:
        return None
    return PROVIDER_ALIASES.get(normalized, normalized)


def validate_provider_for_role(role: str, provider: str | None) -> None:
    if provider is None:
        raise WorkflowConfigError(f"provider kind is required for role '{role}'")

    normalized_role = normalize_role(role)
    allowed = ISSUE_PROVIDERS if normalized_role == "issue" else KNOWLEDGE_PROVIDERS
    if provider not in allowed:
        choices = ", ".join(sorted(allowed))
        raise WorkflowConfigError(
            f"provider '{provider}' is not valid for role '{normalized_role}'. "
            f"Use one of: {choices}"
        )


def _parse_provider(raw: Mapping[str, Any], *, role: str, slot: str, path: Path) -> ProviderConfig:
    data = _provider_mapping(raw, slot)
    if data is None:
        raise WorkflowConfigError(f"providers.{slot} is required in {path}")

    kind = normalize_provider(_scalar_string(data.get("kind") or data.get("provider")))
    validate_provider_for_role(role, kind)

    settings = {key: value for key, value in data.items() if key not in {"kind", "provider"}}
    return ProviderConfig(role=role, kind=kind or "", settings=settings)


def _provider_mapping(raw: Mapping[str, Any], slot: str) -> Mapping[str, Any] | None:
    provider = _dig(raw, "providers", slot)
    if provider is None:
        provider = _dig(raw, "source_of_truth", slot)
    if provider is None:
        return None
    if isinstance(provider, str):
        return {"kind": provider}
    if not isinstance(provider, Mapping):
        raise WorkflowConfigError(f"providers.{slot} must be a mapping or provider name")
    return provider


def _parse_local_projection(value: Any, *, path: Path) -> LocalProjectionConfig:
    if value is None:
        return LocalProjectionConfig()
    if isinstance(value, str):
        return LocalProjectionConfig(mode=_normalize_local_projection_mode(value, path=path))
    if not isinstance(value, Mapping):
        raise WorkflowConfigError(f"local_projection must be a mapping in {path}")

    mode = _normalize_local_projection_mode(_scalar_string(value.get("mode", "none")), path=path)
    projection_path = _scalar_string(value.get("path"))
    settings = {key: item for key, item in value.items() if key not in {"mode", "path"}}
    return LocalProjectionConfig(mode=mode, path=projection_path, settings=settings)


def _normalize_local_projection_mode(value: str | None, *, path: Path) -> str:
    if value is None:
        return "none"
    normalized = value.strip().lower().replace("_", "-")
    normalized = LOCAL_PROJECTION_ALIASES.get(normalized, normalized)
    if normalized not in LOCAL_PROJECTION_MODES:
        choices = ", ".join(sorted(LOCAL_PROJECTION_MODES))
        raise WorkflowConfigError(
            f"local_projection.mode '{value}' is invalid in {path}. Use one of: {choices}"
        )
    return normalized


def _parse_commit_refs(value: Any, *, path: Path) -> CommitRefsConfig:
    if value is None:
        return CommitRefsConfig()
    if isinstance(value, str):
        style = _normalize_commit_ref_style(value, path=path)
        return CommitRefsConfig(enabled=style != "disabled", style=style)
    if not isinstance(value, Mapping):
        raise WorkflowConfigError(f"commit_refs must be a mapping in {path}")

    enabled = _parse_bool(value.get("enabled", True), path=path, field="commit_refs.enabled")
    style = _normalize_commit_ref_style(_scalar_string(value.get("style", "provider-native")), path=path)
    if not enabled:
        style = "disabled"
    settings = {key: item for key, item in value.items() if key not in {"enabled", "style"}}
    return CommitRefsConfig(enabled=enabled, style=style, settings=settings)


def _normalize_commit_ref_style(value: str | None, *, path: Path) -> str:
    if value is None:
        return "provider-native"
    normalized = value.strip().lower().replace("_", "-")
    normalized = COMMIT_REF_STYLE_ALIASES.get(normalized, normalized)
    if normalized not in COMMIT_REF_STYLES:
        choices = ", ".join(sorted(COMMIT_REF_STYLES))
        raise WorkflowConfigError(
            f"commit_refs.style '{value}' is invalid in {path}. Use one of: {choices}"
        )
    return normalized


def _parse_issue_id_format(value: Any, *, issue_provider: str, path: Path) -> str:
    raw = _scalar_string(value)
    if raw is None:
        return _provider_native_issue_id_format(issue_provider, path=path)

    normalized = raw.strip().lower().replace("_", "-")
    if normalized in {"provider-native", "native", "provider"}:
        return _provider_native_issue_id_format(issue_provider, path=path)
    normalized = ISSUE_ID_FORMAT_ALIASES.get(normalized, normalized)
    if normalized not in ISSUE_ID_FORMATS:
        choices = ", ".join(sorted(ISSUE_ID_FORMATS | {"provider-native"}))
        raise WorkflowConfigError(
            f"issue_id_format '{value}' is invalid in {path}. Use one of: {choices}"
        )

    expected = _provider_native_issue_id_format(issue_provider, path=path)
    if normalized != expected:
        raise WorkflowConfigError(
            f"issue_id_format '{value}' is invalid for issue provider '{issue_provider}' in {path}"
        )
    return normalized


def _provider_native_issue_id_format(issue_provider: str, *, path: Path) -> str:
    try:
        return PROVIDER_NATIVE_ISSUE_ID_FORMATS[issue_provider]
    except KeyError as exc:
        raise WorkflowConfigError(f"unsupported issue provider for issue_id_format: {issue_provider}") from exc


def _parse_version(value: Any, *, path: Path) -> int:
    if isinstance(value, bool):
        raise WorkflowConfigError(f"version must be 1 in {path}")
    if isinstance(value, int):
        version = value
    elif isinstance(value, str) and value.strip().isdigit():
        version = int(value.strip())
    else:
        raise WorkflowConfigError(f"version must be 1 in {path}")
    if version != 1:
        raise WorkflowConfigError(f"unsupported workflow config version: {version}")
    return version


def _parse_mode(value: Any, *, path: Path) -> str:
    mode = _scalar_string(value)
    if mode is None:
        return "remote-native"
    normalized = mode.strip().lower().replace("_", "-")
    if not normalized:
        raise WorkflowConfigError(f"mode must not be empty in {path}")
    return normalized


def _parse_bool(value: Any, *, path: Path, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False
    raise WorkflowConfigError(f"{field} must be true or false in {path}")


def _scalar_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _dig(data: Mapping[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        data = _load_minimal_yaml_mapping(path)
    else:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise WorkflowConfigError(f"config must be a mapping: {path}")
    return data


def _load_minimal_yaml_mapping(path: Path) -> dict[str, Any]:
    """Fallback parser for the simple mapping shape used by workflow config.

    This is not a general YAML parser. It supports nested mappings and scalar
    values, which is enough for the first workflow configuration schema when
    PyYAML is unavailable.
    """

    result: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, result)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = _strip_yaml_comment(raw_line).rstrip()
        if not line.strip() or ":" not in line:
            continue

        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise WorkflowConfigError(f"invalid indentation in {path}")
        parent = stack[-1][1]

        if value:
            parent[key] = _parse_minimal_scalar(value)
            continue

        child: dict[str, Any] = {}
        parent[key] = child
        stack.append((indent, child))

    return result


def _strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _parse_minimal_scalar(value: str) -> Any:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.isdigit():
        return int(value)
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project path")
    parser.add_argument("--require", action="store_true", help=f"fail when {CONFIG_NAME} is absent")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_workflow_config(args.project, require=args.require)
    except WorkflowConfigError as exc:
        print(f"workflow config error: {exc}", file=sys.stderr)
        return 2

    if config is None:
        if args.json:
            print(json.dumps({"configured": False, "config_path": None}, indent=2))
        return 1

    if args.json:
        result = {"configured": True, **config.to_json()}
        print(json.dumps(result, indent=2, sort_keys=False))
    else:
        print(config.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
