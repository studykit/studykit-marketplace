"""Tests for workflow provider reference parsing and normalization."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_config import load_workflow_config  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_refs import (  # noqa: E402
    ProviderReferenceAmbiguityError,
    ProviderReferenceMismatchError,
    normalize_provider_reference,
)


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]):
        self.responses = responses
        self.requests: list[CommandRequest] = []

    def __call__(self, request: CommandRequest) -> CommandResult:
        self.requests.append(request)
        response = self.responses.get(request.args)
        if response is None:
            return CommandResult(request=request, returncode=127, stderr="unexpected command")
        return response


def result(args: tuple[str, ...], stdout: str = "", stderr: str = "", returncode: int = 0) -> CommandResult:
    return CommandResult(request=CommandRequest(args=args), returncode=returncode, stdout=stdout, stderr=stderr)


def _config_path(project: Path) -> Path:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _github_config(project: Path, *, issue_repo: str | None = "studykit/studykit-plugins") -> None:
    repo_line = f"    repo: {issue_repo}\n" if issue_repo is not None else ""
    _config_path(project).write_text(
        f"""
version: 1
providers:
  issues:
    kind: github
{repo_line.rstrip()}
  knowledge:
    kind: github
    path: wiki/workflow
issue_id_format: github
""".lstrip(),
        encoding="utf-8",
    )


def _jira_confluence_config(project: Path) -> None:
    _config_path(project).write_text(
        """
version: 1
providers:
  issues:
    kind: jira
    site: acme.atlassian.net
    project: PROJ
  knowledge:
    kind: confluence
    site: acme.atlassian.net
    space: ENG
    space_id: "98765"
""".lstrip(),
        encoding="utf-8",
    )


def test_normalizes_same_repo_github_issue_from_config(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference("#123", config, role="issue")

    assert ref.to_json() == {
        "input": "#123",
        "provider": "github",
        "kind": "issue",
        "authority": "github.com",
        "native": {"owner": "studykit", "repo": "studykit-plugins", "number": 123},
        "display": "#123",
        "url": "https://github.com/studykit/studykit-plugins/issues/123",
        "ref": "workflowref:github:issue:github.com/studykit/studykit-plugins/123",
    }


def test_same_repo_github_issue_can_resolve_from_git_remote(tmp_path: Path) -> None:
    _github_config(tmp_path, issue_repo=None)
    config = load_workflow_config(tmp_path)
    assert config is not None
    args = ("git", "-C", str(tmp_path.resolve()), "remote", "get-url", "origin")
    runner = FakeRunner({args: result(args, stdout="git@github.com:remote-org/remote-repo.git\n")})

    ref = normalize_provider_reference("#123", config, role="issue", runner=runner)

    assert ref.native == {"owner": "remote-org", "repo": "remote-repo", "number": 123}
    assert ref.url == "https://github.com/remote-org/remote-repo/issues/123"
    assert [request.args for request in runner.requests] == [args]


def test_same_repo_github_issue_without_context_fails_clearly(tmp_path: Path) -> None:
    _github_config(tmp_path, issue_repo=None)
    config = load_workflow_config(tmp_path)
    assert config is not None
    args = ("git", "-C", str(tmp_path.resolve()), "remote", "get-url", "origin")
    runner = FakeRunner({args: result(args, stderr="not a git repository", returncode=128)})

    with pytest.raises(ProviderReferenceAmbiguityError, match="repository context"):
        normalize_provider_reference("#123", config, role="issue", runner=runner)


def test_normalizes_cross_repo_github_issue_ref(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference("octo-org/octo-repo#456", config, role="issue")

    assert ref.provider == "github"
    assert ref.kind == "issue"
    assert ref.authority == "github.com"
    assert ref.native == {"owner": "octo-org", "repo": "octo-repo", "number": 456}
    assert ref.display == "octo-org/octo-repo#456"
    assert ref.url == "https://github.com/octo-org/octo-repo/issues/456"


def test_normalizes_github_issue_url_display_for_same_repo(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference(
        "https://github.com/studykit/studykit-plugins/issues/33",
        config,
        role="issue",
    )

    assert ref.native["number"] == 33
    assert ref.display == "#33"


def test_normalizes_jira_issue_key(tmp_path: Path) -> None:
    _jira_confluence_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference("proj-123", config, role="issue")

    assert ref.to_json() == {
        "input": "proj-123",
        "provider": "jira",
        "kind": "issue",
        "authority": "acme.atlassian.net",
        "native": {"key": "PROJ-123", "project": "PROJ", "number": 123},
        "display": "PROJ-123",
        "url": "https://acme.atlassian.net/browse/PROJ-123",
        "ref": "workflowref:jira:issue:acme.atlassian.net/PROJ-123",
    }


def test_normalizes_confluence_page_url(tmp_path: Path) -> None:
    _jira_confluence_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None
    url = "https://acme.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2"

    ref = normalize_provider_reference(url, config, role="knowledge")

    assert ref.provider == "confluence"
    assert ref.kind == "page"
    assert ref.authority == "acme.atlassian.net"
    assert ref.native == {
        "page_id": "123456789",
        "space": "ENG",
        "space_id": "98765",
        "title": "Auth Session v2",
    }
    assert ref.display == "Auth Session v2"
    assert ref.ref == "workflowref:confluence:page:acme.atlassian.net/123456789"


def test_normalizes_confluence_page_display_ref_with_config_context(tmp_path: Path) -> None:
    _jira_confluence_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference("Auth Session v2", config, role="knowledge")

    assert ref.provider == "confluence"
    assert ref.kind == "page"
    assert ref.authority == "acme.atlassian.net"
    assert ref.native == {"title": "Auth Session v2", "space": "ENG", "space_id": "98765"}
    assert ref.display == "Auth Session v2"
    assert ref.url is None


def test_normalizes_github_repository_wiki_page(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    ref = normalize_provider_reference(
        "wiki/workflow/workflow-provider-reference-formats.md",
        config,
        role="knowledge",
    )

    assert ref.provider == "github"
    assert ref.kind == "page"
    assert ref.authority == "github.com"
    assert ref.native == {
        "owner": "studykit",
        "repo": "studykit-plugins",
        "path": "wiki/workflow/workflow-provider-reference-formats.md",
        "branch": "main",
    }
    assert ref.display == "wiki/workflow/workflow-provider-reference-formats.md"
    assert ref.url == (
        "https://github.com/studykit/studykit-plugins/blob/main/"
        "wiki/workflow/workflow-provider-reference-formats.md"
    )


def test_bare_issue_numbers_require_explicit_metadata_opt_in(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    with pytest.raises(ProviderReferenceAmbiguityError, match="bare numeric"):
        normalize_provider_reference("123", config, role="issue")

    ref = normalize_provider_reference("123", config, role="issue", allow_bare_issue_number=True)

    assert ref.input == "123"
    assert ref.display == "#123"
    assert ref.native["number"] == 123


def test_provider_mismatch_errors_are_clear(tmp_path: Path) -> None:
    _github_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    with pytest.raises(ProviderReferenceMismatchError, match="configured issue provider is 'github'"):
        normalize_provider_reference("PROJ-123", config, role="issue")

    with pytest.raises(ProviderReferenceMismatchError, match="not a issue reference"):
        normalize_provider_reference(
            "wiki/workflow/workflow-provider-reference-formats.md",
            config,
            role="issue",
        )


def test_page_display_refs_are_ambiguous_without_knowledge_context(tmp_path: Path) -> None:
    _jira_confluence_config(tmp_path)
    config = load_workflow_config(tmp_path)
    assert config is not None

    with pytest.raises(ProviderReferenceAmbiguityError):
        normalize_provider_reference("Auth Session v2", config)
