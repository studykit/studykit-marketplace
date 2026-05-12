"""Tests for workflow authoring resolver."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from authoring_resolver import ResolverError, resolve_authoring  # noqa: E402


def _rel_paths(paths: tuple[Path, ...]) -> list[str]:
    return [str(path.relative_to(_PLUGIN_ROOT / "authoring")) for path in paths]


def test_review_github_issue_resolution_uses_absolute_authoring_files() -> None:
    resolution = resolve_authoring("review", role="issue", provider="github")

    assert resolution.artifact_type == "review"
    assert resolution.role == "issue"
    assert resolution.provider == "github"
    assert _rel_paths(resolution.files) == [
        "metadata-contract.md",
        "body-conventions.md",
        "issue-body.md",
        "review-authoring.md",
        "providers/github-issue-authoring.md",
    ]
    assert all(path.is_absolute() for path in resolution.files)


def test_spec_confluence_knowledge_resolution() -> None:
    resolution = resolve_authoring("spec", provider="confluence")

    assert resolution.role == "knowledge"
    assert _rel_paths(resolution.files) == [
        "metadata-contract.md",
        "body-conventions.md",
        "knowledge-body.md",
        "spec-authoring.md",
        "providers/confluence-page-authoring.md",
    ]


def test_dual_artifact_requires_explicit_role() -> None:
    with pytest.raises(ResolverError, match="specify --role"):
        resolve_authoring("research", provider="jira")


def test_provider_can_be_inferred_from_workflow_config(tmp_path: Path) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: jira
  knowledge:
    kind: github-wiki
""".lstrip(),
        encoding="utf-8",
    )

    issue_resolution = resolve_authoring("task", project=tmp_path)
    knowledge_resolution = resolve_authoring("architecture", project=tmp_path)

    assert issue_resolution.provider == "jira"
    assert "providers/jira-issue-authoring.md" in _rel_paths(issue_resolution.files)
    assert knowledge_resolution.provider == "github-wiki"
    assert "providers/github-wiki-authoring.md" in _rel_paths(knowledge_resolution.files)


def test_invalid_provider_for_role_is_rejected() -> None:
    with pytest.raises(ResolverError, match="not valid for role 'knowledge'"):
        resolve_authoring("spec", provider="github")


def test_require_config_fails_when_missing(tmp_path: Path) -> None:
    with pytest.raises(ResolverError, match="workflow.config.yml was not found"):
        resolve_authoring("task", project=tmp_path, require_config=True)
