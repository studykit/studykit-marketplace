"""Tests for workflow documentation and operator boundary text."""

from __future__ import annotations

import re
from pathlib import Path


_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _PLUGIN_ROOT.parent.parent


def test_readme_keeps_authoring_resolver_internal_to_operator() -> None:
    readme = (_PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    assert "ask `workflow-operator` for the required\nauthoring paths" in readme
    assert "- Authoring path discovery." in readme
    assert "authoring_resolver.py" not in readme
    assert "Resolve authoring files:" not in readme


def test_operator_instructions_do_not_return_internal_commands_to_callers() -> None:
    expected = (
        "Do not return resolver command names, launcher recipes, or\n"
        "script paths to the caller; those are operator internals."
    )
    expected_discovery = (
        "Do not return the command you ran, script names, or\n"
        "launcher details."
    )
    operator_md = (_PLUGIN_ROOT / "agents" / "workflow-operator.md").read_text(
        encoding="utf-8"
    )
    operator_toml = (_REPO_ROOT / ".codex" / "agents" / "workflow-operator.toml").read_text(
        encoding="utf-8"
    )

    for text in (operator_md, operator_toml):
        assert expected in text
        assert expected_discovery in text
        assert '"$WORKFLOW" authoring_resolver.py' in text


def test_authoring_enforcement_wiki_is_main_agent_facing() -> None:
    wiki = (
        _REPO_ROOT / "wiki" / "workflow" / "workflow-authoring-enforcement.md"
    ).read_text(encoding="utf-8")

    assert "main assistant asks `workflow-operator` for required authoring paths" in wiki
    assert "command\nnames and script paths are not part of the caller-facing response" in wiki
    assert "authoring_resolver.py" not in wiki
    assert "scripts/workflow" not in wiki


def test_authoring_docs_do_not_reference_removed_metadata_contract() -> None:
    assert not (_PLUGIN_ROOT / "authoring" / "common" / "metadata-contract.md").exists()

    checked_roots = [
        _PLUGIN_ROOT / "authoring",
        _REPO_ROOT / "wiki" / "workflow",
    ]
    for root in checked_roots:
        for path in root.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            assert "metadata-contract.md" not in text, path
            assert "Workflow Metadata Contract" not in text, path


def test_issue_relationship_contract_is_separate_from_metadata_contract() -> None:
    providers = _PLUGIN_ROOT / "authoring" / "providers"

    for name in (
        "github-issue-metadata.md",
        "jira-issue-metadata.md",
        "github-issue-relationships.md",
        "jira-issue-relationships.md",
    ):
        text = (providers / name).read_text(encoding="utf-8")
        assert "Relationship projection" not in text
        assert "relationships.yml" not in text
        assert "relationships-pending.yml" not in text

    github_relationships = (providers / "github-issue-relationships.md").read_text(
        encoding="utf-8"
    )
    jira_relationships = (providers / "jira-issue-relationships.md").read_text(
        encoding="utf-8"
    )

    assert "Issue relationships are not issue metadata fields." in github_relationships
    assert "GitHub sub-issue metadata" in github_relationships
    assert "GitHub issue dependency metadata" in github_relationships
    assert "Issue relationships are not issue metadata fields." in jira_relationships
    assert "Jira parent/subtask" in jira_relationships
    assert "configured Jira issue links" in jira_relationships


def test_main_facing_authoring_docs_do_not_expose_cache_projection_internals() -> None:
    forbidden = {
        "issue.md",
        "metadata.yml",
        "relationships.yml",
        "relationships-pending.yml",
        "issue.json",
        "snapshot.md",
        "schema_version",
        "fetched_at",
        "source_updated_at",
    }

    checked_paths = (
        list((_PLUGIN_ROOT / "authoring").rglob("*.md"))
        + [_PLUGIN_ROOT / "README.md"]
        + list((_REPO_ROOT / "wiki" / "workflow").rglob("*.md"))
    )
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        leaked = sorted(token for token in forbidden if token in text)
        assert leaked == [], f"{path}: {leaked}"


def test_projection_schema_docs_are_contributor_docs_not_operator_instructions() -> None:
    dev_root = _PLUGIN_ROOT / "dev"
    github_projection = (dev_root / "github-issue-cache-projection.md").read_text(
        encoding="utf-8"
    )
    jira_projection = (dev_root / "jira-issue-cache-projection.md").read_text(
        encoding="utf-8"
    )
    operator_md = (_PLUGIN_ROOT / "agents" / "workflow-operator.md").read_text(
        encoding="utf-8"
    )
    operator_toml = (
        _REPO_ROOT / ".codex" / "agents" / "workflow-operator.toml"
    ).read_text(encoding="utf-8")

    assert "relationships.yml" in github_projection
    assert "relationships-pending.yml" in github_projection
    assert "issue.json" in jira_projection
    assert "snapshot.md" in jira_projection
    for projection in (github_projection, jira_projection):
        assert "Contributor-facing cache projection contract" in projection
        assert "workflow plugin contributors" in projection
        assert "workflow-operator" not in projection
    for text in (operator_md, operator_toml):
        assert "plugins/workflow/operator/" not in text
        assert "plugins/workflow/dev/github-issue-cache-projection.md" not in text
        assert "plugins/workflow/dev/jira-issue-cache-projection.md" not in text
        assert "Do not directly edit provider metadata, projection frontmatter" in text
        assert "Use workflow provider/cache scripts for those\nmutations." in text
        assert "Treat paths returned by workflow scripts as opaque operational paths." in text


def test_common_metadata_sections_do_not_list_relationship_fields() -> None:
    relationship_fields = {
        "children",
        "depends_on",
        "implements",
        "knowledge_page",
        "parent",
        "related",
        "source_issue",
        "spec",
        "supersedes",
        "target",
    }

    for path in (_PLUGIN_ROOT / "authoring" / "common").glob("*-authoring.md"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"^## [^\n]*metadata[^\n]*\n(?P<body>.*?)(?=^## |\Z)",
            text,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        ):
            fields = {
                field_match.group(1)
                for field_match in re.finditer(
                    r"^\|\s*`([^`]+)`\s*\|",
                    match.group("body"),
                    flags=re.MULTILINE,
                )
            }
            assert fields.isdisjoint(relationship_fields), path
