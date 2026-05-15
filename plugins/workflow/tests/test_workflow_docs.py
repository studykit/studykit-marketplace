"""Tests for workflow documentation and operator boundary text."""

from __future__ import annotations

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
