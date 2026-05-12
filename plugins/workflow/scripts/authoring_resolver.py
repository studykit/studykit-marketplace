#!/usr/bin/env python3
"""Resolve workflow authoring contracts for provider-backed artifacts.

The resolver is intentionally small and deterministic. It returns absolute
paths to plugin-bundled authoring files so agents do not guess which files to
read before writing workflow artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
AUTHORING_DIR = PLUGIN_ROOT / "authoring"
CONFIG_NAME = "workflow.config.yml"

ISSUE_TYPES = {"task", "bug", "spike", "epic", "review"}
KNOWLEDGE_TYPES = {"spec", "architecture", "domain", "context", "actors", "nfr", "ci"}
DUAL_TYPES = {"usecase", "research"}
ALL_TYPES = ISSUE_TYPES | KNOWLEDGE_TYPES | DUAL_TYPES

ISSUE_PROVIDERS = {"github", "jira", "filesystem"}
KNOWLEDGE_PROVIDERS = {"github-wiki", "confluence", "filesystem"}

PROVIDER_ALIASES = {
    "fs": "filesystem",
    "file": "filesystem",
    "files": "filesystem",
    "local": "filesystem",
    "github-issues": "github",
    "github_issue": "github",
    "github-issue": "github",
    "github-wikis": "github-wiki",
    "github_wiki": "github-wiki",
    "githubwiki": "github-wiki",
    "wiki": "github-wiki",
}

ISSUE_PROVIDER_FILES = {
    "github": "providers/github-issue-authoring.md",
    "jira": "providers/jira-issue-authoring.md",
}

KNOWLEDGE_PROVIDER_FILES = {
    "github-wiki": "providers/github-wiki-authoring.md",
    "confluence": "providers/confluence-page-authoring.md",
}


@dataclass(frozen=True)
class Resolution:
    """Resolved authoring contract set."""

    artifact_type: str
    role: str
    provider: str | None
    files: tuple[Path, ...]
    config_path: Path | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "configured": self.config_path is not None,
            "config_path": str(self.config_path) if self.config_path else None,
            "artifact": {
                "type": self.artifact_type,
                "role": self.role,
                "provider": self.provider,
            },
            "required_authoring_files": [str(path) for path in self.files],
        }


class ResolverError(ValueError):
    """Raised when authoring cannot be resolved safely."""


def normalize_type(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized == "use-case":
        normalized = "usecase"
    if normalized not in ALL_TYPES:
        raise ResolverError(f"unsupported artifact type: {value}")
    return normalized


def normalize_role(value: str | None, artifact_type: str) -> str:
    if value is None:
        if artifact_type in ISSUE_TYPES:
            return "issue"
        if artifact_type in KNOWLEDGE_TYPES:
            return "knowledge"
        raise ResolverError(
            f"artifact type '{artifact_type}' can be issue or knowledge; specify --role"
        )

    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"page", "wiki", "doc", "document"}:
        normalized = "knowledge"
    if normalized not in {"issue", "knowledge"}:
        raise ResolverError(f"unsupported artifact role: {value}")

    if artifact_type in ISSUE_TYPES and normalized != "issue":
        raise ResolverError(f"artifact type '{artifact_type}' is issue-backed")
    if artifact_type in KNOWLEDGE_TYPES and normalized != "knowledge":
        raise ResolverError(f"artifact type '{artifact_type}' is knowledge-backed")
    return normalized


def normalize_provider(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().lower().replace("_", "-")
    return PROVIDER_ALIASES.get(normalized, normalized)


def find_config(project: Path) -> Path | None:
    current = project.resolve()
    if current.is_file():
        current = current.parent
    for candidate_dir in (current, *current.parents):
        candidate = candidate_dir / CONFIG_NAME
        if candidate.exists():
            return candidate
    return None


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        return _load_minimal_config(path)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ResolverError(f"config must be a mapping: {path}")
    return data


def _load_minimal_config(path: Path) -> dict[str, Any]:
    """Fallback parser for the simple provider shape used by workflow config.

    This is not a general YAML parser. It only extracts provider kind/provider
    values under `providers.issues`, `providers.knowledge`,
    `source_of_truth.issues`, and `source_of_truth.knowledge`.
    """

    result: dict[str, Any] = {"providers": {}, "source_of_truth": {}}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, result)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        value = value.strip().strip('"\'')

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value:
            parent[key] = value
            continue

        child: dict[str, Any] = {}
        parent[key] = child
        stack.append((indent, child))

    return result


def _dig(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def provider_from_config(config: dict[str, Any], role: str) -> str | None:
    slot = "issues" if role == "issue" else "knowledge"
    candidates = [
        _dig(config, "providers", slot, "kind"),
        _dig(config, "providers", slot, "provider"),
        _dig(config, "source_of_truth", slot, "provider"),
        _dig(config, "source_of_truth", slot, "kind"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return normalize_provider(candidate)
    return None


def validate_provider(role: str, provider: str | None) -> None:
    if provider is None:
        return
    allowed = ISSUE_PROVIDERS if role == "issue" else KNOWLEDGE_PROVIDERS
    if provider not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ResolverError(
            f"provider '{provider}' is not valid for role '{role}'. Use one of: {choices}"
        )


def absolute_authoring_paths(parts: Iterable[str]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for rel in parts:
        path = (AUTHORING_DIR / rel).resolve()
        if not path.exists():
            raise ResolverError(f"authoring file does not exist: {path}")
        paths.append(path)
    return tuple(paths)


def resolve_authoring(
    artifact_type: str,
    *,
    role: str | None = None,
    provider: str | None = None,
    project: Path | None = None,
    require_config: bool = False,
) -> Resolution:
    normalized_type = normalize_type(artifact_type)
    normalized_role = normalize_role(role, normalized_type)

    config_path: Path | None = None
    config_provider: str | None = None
    if project is not None:
        config_path = find_config(project)
        if config_path is not None:
            config_provider = provider_from_config(_load_yaml(config_path), normalized_role)

    if require_config and config_path is None:
        project_label = str(project) if project is not None else "current project"
        raise ResolverError(f"{CONFIG_NAME} was not found for {project_label}")

    normalized_provider = normalize_provider(provider) or config_provider
    validate_provider(normalized_role, normalized_provider)

    parts = [
        "metadata-contract.md",
        "body-conventions.md",
        "issue-body.md" if normalized_role == "issue" else "knowledge-body.md",
        f"{normalized_type}-authoring.md",
    ]

    if normalized_role == "issue" and normalized_provider in ISSUE_PROVIDER_FILES:
        parts.append(ISSUE_PROVIDER_FILES[normalized_provider])
    if normalized_role == "knowledge" and normalized_provider in KNOWLEDGE_PROVIDER_FILES:
        parts.append(KNOWLEDGE_PROVIDER_FILES[normalized_provider])

    return Resolution(
        artifact_type=normalized_type,
        role=normalized_role,
        provider=normalized_provider,
        files=absolute_authoring_paths(parts),
        config_path=config_path.resolve() if config_path else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", required=True, help="workflow artifact type")
    parser.add_argument("--role", help="issue or knowledge; required for usecase/research")
    parser.add_argument("--provider", help="provider override, such as github, jira, confluence, github-wiki")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project path used to find workflow.config.yml")
    parser.add_argument("--require-config", action="store_true", help="fail when workflow.config.yml is absent")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of one path per line")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        resolution = resolve_authoring(
            args.type,
            role=args.role,
            provider=args.provider,
            project=args.project,
            require_config=args.require_config,
        )
    except ResolverError as exc:
        print(f"authoring resolver error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(resolution.to_json(), indent=2, sort_keys=False))
    else:
        for path in resolution.files:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
