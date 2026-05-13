"""Tests for workflow.config.yml loading and validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_config import WorkflowConfigError, load_workflow_config  # noqa: E402


def test_loads_github_issues_and_repository_wiki_knowledge(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    (project / "workflow.config.yml").write_text(
        """
version: 1
mode: remote-native
providers:
  issues:
    kind: github-issues
    repo: studykit/studykit-plugins
  knowledge:
    kind: repo-wiki
    path: wiki/workflow
local_projection:
  mode: none
commit_refs:
  enabled: true
  style: provider-native
""".lstrip(),
        encoding="utf-8",
    )

    config = load_workflow_config(nested)

    assert config is not None
    assert config.path == project / "workflow.config.yml"
    assert config.root == project
    assert config.issues.kind == "github"
    assert config.issues.settings["repo"] == "studykit/studykit-plugins"
    assert config.knowledge.kind == "github"
    assert config.knowledge.settings["path"] == "wiki/workflow"
    assert config.local_projection.mode == "none"
    assert config.commit_refs.enabled is True
    assert config.commit_refs.style == "provider-native"


def test_loads_jira_issues_and_confluence_knowledge_from_source_of_truth_shape(
    tmp_path: Path,
) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: "1"
source_of_truth:
  issues:
    provider: jira-issues
    site: acme.atlassian.net
    project: PROJ
  knowledge:
    provider: confluence-page
    site: acme.atlassian.net
    space: ENG
local_projection:
  mode: temporary
commit_refs:
  style: issue-prefix
""".lstrip(),
        encoding="utf-8",
    )

    config = load_workflow_config(tmp_path)

    assert config is not None
    assert config.issues.kind == "jira"
    assert config.issues.settings["site"] == "acme.atlassian.net"
    assert config.knowledge.kind == "confluence"
    assert config.knowledge.settings["space"] == "ENG"
    assert config.local_projection.mode == "ephemeral"
    assert config.commit_refs.style == "issue-prefix"


def test_loads_filesystem_only_config(tmp_path: Path) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: fs
    path: workflow/issues
  knowledge:
    kind: local
    path: workflow/knowledge
local_projection:
  mode: mirror
  path: workflow
commit_refs:
  enabled: false
""".lstrip(),
        encoding="utf-8",
    )

    config = load_workflow_config(tmp_path)

    assert config is not None
    assert config.issues.kind == "filesystem"
    assert config.knowledge.kind == "filesystem"
    assert config.local_projection.mode == "persistent"
    assert config.local_projection.path == "workflow"
    assert config.commit_refs.enabled is False
    assert config.commit_refs.style == "disabled"


def test_missing_config_returns_none_and_can_be_required(tmp_path: Path) -> None:
    assert load_workflow_config(tmp_path) is None

    with pytest.raises(WorkflowConfigError, match="workflow.config.yml was not found"):
        load_workflow_config(tmp_path, require=True)


@pytest.mark.parametrize(
    ("issue_provider", "knowledge_provider", "message"),
    [
        ("confluence", "github", "not valid for role 'issue'"),
        ("github", "jira", "not valid for role 'knowledge'"),
    ],
)
def test_invalid_provider_role_combinations_are_rejected(
    tmp_path: Path,
    issue_provider: str,
    knowledge_provider: str,
    message: str,
) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        f"""
version: 1
providers:
  issues:
    kind: {issue_provider}
  knowledge:
    kind: {knowledge_provider}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowConfigError, match=message):
        load_workflow_config(tmp_path)


def test_config_requires_issue_and_knowledge_provider_slots(tmp_path: Path) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: github
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowConfigError, match="providers.knowledge is required"):
        load_workflow_config(tmp_path)


def test_invalid_local_projection_mode_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: github
  knowledge:
    kind: github
local_projection:
  mode: archive
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowConfigError, match="local_projection.mode"):
        load_workflow_config(tmp_path)


def test_invalid_commit_reference_style_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "workflow.config.yml").write_text(
        """
version: 1
providers:
  issues:
    kind: jira
  knowledge:
    kind: confluence
commit_refs:
  style: magic
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowConfigError, match="commit_refs.style"):
        load_workflow_config(tmp_path)
