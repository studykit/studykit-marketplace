"""Tests for workflow provider read cache projections."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
_REPO_ROOT = _PLUGIN_ROOT.parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import (  # noqa: E402
    FreshnessMetadata,
    GitHubIssueCache,
    WorkflowFreshnessConflict,
    check_provider_freshness,
    require_provider_freshness,
)
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_providers import (  # noqa: E402
    CACHE_POLICY_BYPASS,
    CACHE_POLICY_REFRESH,
    ProviderContext,
    ProviderDispatcher,
    ProviderRequest,
    default_provider_registry,
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


def git_args(project: Path, *args: str) -> tuple[str, ...]:
    return ("git", "-C", str(project.resolve(strict=False)), *args)


def gh_issue_view_args(issue: int | str) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        ",".join(DEFAULT_ISSUE_FIELDS),
    )


def repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def external_repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="other", name="repo")


def issue_payload(*, body: str = "Raw issue body.", updated_at: str = "2026-05-13T12:00:00Z") -> dict[str, object]:
    return {
        "number": 39,
        "title": "Add local cache for workflow provider reads",
        "state": "OPEN",
        "stateReason": None,
        "body": body,
        "labels": [{"name": "task"}, {"name": "workflow"}],
        "updatedAt": updated_at,
        "comments": [
            {
                "id": "IC_kwDOQplzFM8AAAABCKrz_g",
                "url": "https://github.com/studykit/studykit-plugins/issues/39#issuecomment-4440388606",
                "author": {"login": "studykit"},
                "body": "Raw provider comment body.",
                "createdAt": "2026-05-13T11:20:53Z",
                "updatedAt": "2026-05-13T11:21:00Z",
            }
        ],
        "parent": {"number": 28, "title": "Workflow plugin MVP", "state": "OPEN", "stateReason": None},
        "children": [{"number": 41, "title": "Create pending issues", "state": "OPEN", "stateReason": None}],
        "dependencies": {
            "blocked_by": [
                {"number": 32, "title": "Scaffold provider wrappers", "state": "CLOSED", "stateReason": "COMPLETED"}
            ],
            "blocking": [{"number": 36, "title": "Write flows", "state": "OPEN", "stateReason": None}],
        },
    }


def dispatch_get(tmp_path: Path, runner: FakeRunner, *, cache_policy: str = "default"):
    dispatcher = ProviderDispatcher(default_provider_registry(runner=runner))
    request = ProviderRequest(
        role="issue",
        kind="github",
        operation="get",
        context=ProviderContext(project=tmp_path, artifact_type="task", cache_policy=cache_policy),
        payload={"issue": 39},
    )
    return dispatcher.dispatch(request)


def test_gitignore_excludes_workflow_cache_root() -> None:
    assert "/.workflow-cache/" in (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")


def test_github_issue_cache_writes_minimal_markdown_comment_index_and_relationships(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path)

    write = cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-13T12:34:56Z")

    assert write.issue_dir == tmp_path / ".workflow-cache" / "issues" / "39"
    issue_text = write.issue_file.read_text(encoding="utf-8")
    assert "title: \"Add local cache for workflow provider reads\"" in issue_text
    assert "provider:" not in issue_text
    assert "# Issue" not in issue_text
    assert issue_text.endswith("Raw issue body.")

    index_text = write.comments_index.read_text(encoding="utf-8")
    assert "provider_comment_id: 4440388606" in index_text
    assert "provider_node_id: IC_kwDOQplzFM8AAAABCKrz_g" in index_text
    assert "created_at:" not in index_text
    assert "preview:" not in index_text

    comment_file = write.comments_index.parent / "2026-05-13T112053Z-4440388606.md"
    comment_text = comment_file.read_text(encoding="utf-8")
    assert "author: studykit" in comment_text
    assert "updated_at: 2026-05-13T11:21:00Z" in comment_text
    assert "provider_comment_id" not in comment_text
    assert comment_text.endswith("Raw provider comment body.")

    relationships = cache.read_relationships(repo(), 39)
    assert relationships["parent"]["number"] == 28
    assert relationships["children"][0]["number"] == 41
    assert relationships["dependencies"]["blocked_by"][0]["state_reason"] == "completed"


def test_configured_repo_cache_is_shallow_and_external_repo_cache_is_namespaced(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())

    assert cache.issue_dir(repo(), 39) == tmp_path / ".workflow-cache" / "issues" / "39"
    assert cache.pending_issue_dir(repo(), "local-1") == tmp_path / ".workflow-cache" / "issues-pending" / "local-1"
    assert (
        cache.issue_dir(external_repo(), 39)
        == tmp_path / ".workflow-cache" / "github.com" / "other" / "repo" / "issues" / "39"
    )
    assert (
        cache.pending_issue_dir(external_repo(), "local-1")
        == tmp_path / ".workflow-cache" / "github.com" / "other" / "repo" / "issues-pending" / "local-1"
    )


def test_pending_issue_draft_parses_frontmatter_and_raw_body(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    draft_path = cache.pending_issue_file(repo(), "draft-1")
    draft_path.parent.mkdir(parents=True)
    draft_path.write_text(
        """---
title: "Draft issue"
labels:
  - task
  - workflow
state: open
---

Draft body.
""",
        encoding="utf-8",
    )

    draft = cache.read_pending_issue_draft(repo(), "draft-1")

    assert draft.local_id == "draft-1"
    assert draft.title == "Draft issue"
    assert draft.labels == ("task", "workflow")
    assert draft.state == "open"
    assert draft.body == "Draft body.\n"


def test_finalize_pending_issue_creation_archives_draft_and_moves_sidecars(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    pending_dir = cache.pending_issue_dir(repo(), "draft-1")
    pending_dir.mkdir(parents=True)
    (pending_dir / "issue.md").write_text("---\ntitle: Draft\n---\n\nBody\n", encoding="utf-8")
    comments_pending = pending_dir / "comments-pending"
    comments_pending.mkdir()
    (comments_pending / "2026-05-14T000000Z-local.md").write_text("Comment\n", encoding="utf-8")
    (pending_dir / "relationships-pending.yml").write_text("parent: 28\n", encoding="utf-8")
    cache.write_issue_bundle(repo(), {**issue_payload(), "number": 51})

    result = cache.finalize_pending_issue_creation(repo(), "draft-1", 51)

    assert not (pending_dir / "issue.md").exists()
    assert Path(result["archived_issue"]).is_file()
    assert (cache.issue_dir(repo(), 51) / "comments-pending" / "2026-05-14T000000Z-local.md").is_file()
    assert (cache.issue_dir(repo(), 51) / "relationships-pending.yml").is_file()


def test_cache_read_can_skip_raw_markdown_bodies(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path)
    write = cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-13T12:34:56Z")
    comment_file = write.comments_index.parent / "2026-05-13T112053Z-4440388606.md"
    comment_file.unlink()

    cached = cache.read_issue(repo(), 39, include_body=False, include_comments=True, include_relationships=False)

    assert "body" not in cached
    assert "body" not in cached["comments"][0]
    assert cached["comments"][0]["id"] == "4440388606"


def test_default_cache_policy_uses_cache_hit_without_remote_issue_view(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(repo(), issue_payload(body="Cached body."), fetched_at="2026-05-13T12:34:56Z")
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            )
        }
    )

    response = dispatch_get(tmp_path, runner)

    assert response.payload["body"] == "Cached body."
    assert response.payload["cache"]["hit"] is True
    assert all(request.args[:3] != ("gh", "issue", "view") for request in runner.requests)


def test_default_cache_policy_miss_reads_remote_and_writes_cache(tmp_path: Path) -> None:
    remote = issue_payload(body="Remote body.")
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_issue_view_args(39): result(gh_issue_view_args(39), stdout=json.dumps(remote)),
        }
    )

    response = dispatch_get(tmp_path, runner)

    assert response.payload["body"] == "Remote body."
    assert GitHubIssueCache.for_project(tmp_path).issue_file(repo(), 39).is_file()


def test_refresh_policy_bypasses_cache_and_overwrites_projection(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path)
    cache.write_issue_bundle(repo(), issue_payload(body="Stale body."), fetched_at="2026-05-13T12:34:56Z")
    remote = issue_payload(body="Fresh body.", updated_at="2026-05-14T00:00:00Z")
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_issue_view_args(39): result(gh_issue_view_args(39), stdout=json.dumps(remote)),
        }
    )

    response = dispatch_get(tmp_path, runner, cache_policy=CACHE_POLICY_REFRESH)

    assert response.payload["body"] == "Fresh body."
    assert cache.read_issue(repo(), 39)["body"] == "Fresh body."


def test_bypass_policy_reads_remote_without_writing_cache(tmp_path: Path) -> None:
    remote = issue_payload(body="Bypass body.")
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_issue_view_args(39): result(gh_issue_view_args(39), stdout=json.dumps(remote)),
        }
    )

    response = dispatch_get(tmp_path, runner, cache_policy=CACHE_POLICY_BYPASS)

    assert response.payload["body"] == "Bypass body."
    assert not GitHubIssueCache.for_project(tmp_path).issue_file(repo(), 39).exists()


def test_corrupt_cache_entry_is_treated_as_miss(tmp_path: Path) -> None:
    cache = GitHubIssueCache.for_project(tmp_path)
    issue_file = cache.issue_file(repo(), 39)
    issue_file.parent.mkdir(parents=True, exist_ok=True)
    issue_file.write_text("not markdown frontmatter", encoding="utf-8")
    remote = issue_payload(body="Recovered body.")
    runner = FakeRunner(
        {
            git_args(tmp_path, "remote", "get-url", "origin"): result(
                git_args(tmp_path, "remote", "get-url", "origin"),
                stdout="git@github.com:studykit/studykit-plugins.git\n",
            ),
            gh_issue_view_args(39): result(gh_issue_view_args(39), stdout=json.dumps(remote)),
        }
    )

    response = dispatch_get(tmp_path, runner)

    assert response.payload["body"] == "Recovered body."
    assert cache.read_issue(repo(), 39)["body"] == "Recovered body."


def test_provider_freshness_allows_clean_cache_metadata() -> None:
    result = require_provider_freshness(
        FreshnessMetadata(
            source_updated_at="2026-05-13T12:00:00Z",
            fetched_at="2026-05-13T12:34:56Z",
        ),
        provider_updated_at="2026-05-13T12:00:00Z",
        artifact="GitHub issue #39 issue",
    )

    assert result.ok is True
    assert result.status == "fresh"


def test_provider_freshness_blocks_stale_provider_timestamp() -> None:
    with pytest.raises(WorkflowFreshnessConflict) as excinfo:
        require_provider_freshness(
            FreshnessMetadata(
                source_updated_at="2026-05-13T12:00:00Z",
                fetched_at="2026-05-13T12:34:56Z",
            ),
            provider_updated_at="2026-05-13T13:00:00Z",
            artifact="GitHub issue #39 issue",
        )

    assert excinfo.value.result.status == "stale"
    assert "Refresh the provider cache before writing" in str(excinfo.value)


def test_provider_freshness_blocks_missing_local_metadata() -> None:
    result = check_provider_freshness(
        FreshnessMetadata(source_updated_at=None, fetched_at="2026-05-13T12:34:56Z"),
        provider_updated_at="2026-05-13T12:00:00Z",
        artifact="GitHub issue #39 issue",
    )

    assert result.ok is False
    assert result.status == "missing_metadata"


def test_provider_freshness_allows_missing_provider_timestamp() -> None:
    result = require_provider_freshness(
        FreshnessMetadata(
            source_updated_at="2026-05-13T12:00:00Z",
            fetched_at="2026-05-13T12:34:56Z",
        ),
        provider_updated_at=None,
        artifact="GitHub issue #39 issue",
    )

    assert result.ok is True
    assert result.status == "provider_timestamp_unavailable"


def test_provider_freshness_skips_pending_new_artifact() -> None:
    result = require_provider_freshness(
        None,
        provider_updated_at=None,
        artifact="GitHub issue pending creation",
        pending_new=True,
    )

    assert result.ok is True
    assert result.status == "pending_new"
