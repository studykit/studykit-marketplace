"""Tests for provider-owned pending issue draft helpers."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_cache_issue_drafts import prepare_pending_issue_draft  # noqa: E402
from workflow_cache_issue_drafts import stage_pending_issue_relationships  # noqa: E402
from workflow_github import GitHubRepository  # noqa: E402


def _write_config(project: Path) -> None:
    config_path = project / ".workflow" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
    path: wiki/workflow
issue_id_format: github
local_projection:
  mode: none
commit_refs:
  enabled: true
  style: provider-native
""".lstrip(),
        encoding="utf-8",
    )


def _repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def test_prepare_pending_issue_draft_writes_bodyless_provider_frontmatter(tmp_path: Path) -> None:
    _write_config(tmp_path)

    payload = prepare_pending_issue_draft(
        project=tmp_path,
        local_id="draft-1",
        artifact_type="task",
        title="Draft issue",
        labels=("workflow",),
    )

    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    draft = cache.read_pending_issue_draft(_repo(), "draft-1")
    issue_file = cache.pending_issue_file(_repo(), "draft-1")

    assert payload["operation"] == "prepare_pending_issue"
    assert payload["artifact_type"] == "task"
    assert payload["issue_file"] == str(issue_file)
    assert draft.title == "Draft issue"
    assert draft.labels == ("task", "workflow")
    assert draft.state == "open"
    assert draft.body == ""
    assert issue_file.read_text(encoding="utf-8").endswith("---\n\n")


def test_stage_pending_issue_relationships_writes_operator_owned_file(tmp_path: Path) -> None:
    _write_config(tmp_path)
    prepare_pending_issue_draft(
        project=tmp_path,
        local_id="draft-1",
        artifact_type="task",
        title="Draft issue",
        labels=("task",),
    )

    payload = stage_pending_issue_relationships(
        project=tmp_path,
        local_id="draft-1",
        parent="#28",
        blocked_by=("#33",),
        blocking=("#45",),
    )

    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=_repo())
    operations = cache.read_pending_draft_relationships(_repo(), "draft-1")

    assert payload["operation"] == "stage_pending_issue_relationships"
    assert payload["relationships_file"] == str(
        cache.pending_issue_relationships_pending_file(_repo(), "draft-1")
    )
    assert [(item.relationship, item.target_ref) for item in operations] == [
        ("parent", "#28"),
        ("blocked_by", "#33"),
        ("blocking", "#45"),
    ]
