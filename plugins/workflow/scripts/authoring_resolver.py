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

from workflow_config import (
    CONFIG_NAME,
    WorkflowConfigError,
    load_workflow_config,
    normalize_provider,
    validate_provider_for_role,
)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
AUTHORING_DIR = PLUGIN_ROOT / "authoring"

ISSUE_TYPES = {"task", "bug", "spike", "epic", "review"}
KNOWLEDGE_TYPES = {"spec", "architecture", "domain", "context", "actors", "nfr", "ci"}
DUAL_TYPES = {"usecase", "research"}
ALL_TYPES = ISSUE_TYPES | KNOWLEDGE_TYPES | DUAL_TYPES

ISSUE_PROVIDER_FILES = {
    "github": "providers/github-issue-authoring.md",
    "jira": "providers/jira-issue-authoring.md",
}

KNOWLEDGE_PROVIDER_FILES = {
    "github": "providers/github-knowledge-authoring.md",
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
    if project is not None or require_config:
        try:
            config = load_workflow_config(project or Path.cwd(), require=require_config)
        except WorkflowConfigError as exc:
            raise ResolverError(str(exc)) from exc
        if config is not None:
            config_path = config.path
            config_provider = config.provider_for_role(normalized_role)

    normalized_provider = normalize_provider(provider) or config_provider
    if normalized_provider is not None:
        try:
            validate_provider_for_role(normalized_role, normalized_provider)
        except WorkflowConfigError as exc:
            raise ResolverError(str(exc)) from exc

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
    parser.add_argument("--provider", help="provider override, such as github, jira, or confluence")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project path used to find .workflow/config.yml")
    parser.add_argument("--require-config", action="store_true", help="fail when .workflow/config.yml is absent")
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
