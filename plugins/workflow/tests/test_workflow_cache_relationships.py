"""Tests for the agent-facing workflow pending relationship apply entrypoint."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_cache import GitHubIssueCache  # noqa: E402
from workflow_cache_relationships import main as cache_relationships_main  # noqa: E402
from workflow_cache_relationships import stage_relationships_payload  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import GitHubRepository  # noqa: E402
from workflow_providers import ProviderRequest  # noqa: E402


def repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def issue_payload() -> dict[str, object]:
    return {
        "number": 44,
        "title": "Cached issue",
        "state": "OPEN",
        "stateReason": None,
        "body": "Cached body.",
        "labels": [],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


def rest_issue(number: int, issue_id: int) -> dict[str, object]:
    return {
        "id": issue_id,
        "number": number,
        "title": f"Issue {number}",
        "state": "open",
        "state_reason": None,
        "updated_at": "2026-05-14T00:00:00Z",
    }


def gh_issue_view_args(issue: int | str, fields: str) -> tuple[str, ...]:
    return (
        "gh",
        "issue",
        "view",
        str(issue),
        "--repo",
        "studykit/studykit-plugins",
        "--json",
        fields,
    )


def gh_api_args(*args: str) -> tuple[str, ...]:
    return ("gh", "api", *args)


def write_config(project: Path) -> None:
    path = project / ".workflow" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
version: 1
providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins
  knowledge:
    kind: github
issue_id_format: github
""".lstrip(),
        encoding="utf-8",
    )


def test_cache_relationships_script_dispatches_guarded_pending_relationship_apply(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-14T00:10:00Z")
    pending_path = cache.relationships_pending_file(repo(), 44)
    pending_path.write_text(
        """
schema_version: 1
children:
  - "#45"
""".lstrip(),
        encoding="utf-8",
    )
    guard_calls: list[ProviderRequest] = []

    def guard(request: ProviderRequest) -> None:
        guard_calls.append(request)

    def runner(request: CommandRequest) -> CommandResult:
        if request.args == gh_issue_view_args(44, "number,updatedAt"):
            return CommandResult(request=request, returncode=0, stdout=json.dumps({"number": 44, "updatedAt": "2026-05-14T00:00:00Z"}))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/45"):
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(45, 4500)))
        if request.args == gh_api_args(
            "-X",
            "POST",
            "repos/studykit/studykit-plugins/issues/44/sub_issues",
            "-F",
            "sub_issue_id=4500",
        ):
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(45, 4500)))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44"):
            return CommandResult(request=request, returncode=0, stdout=json.dumps(rest_issue(44, 4400)))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/parent"):
            return CommandResult(request=request, returncode=404, stderr="not found")
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/sub_issues", "--paginate"):
            return CommandResult(request=request, returncode=0, stdout=json.dumps([rest_issue(45, 4500)]))
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/dependencies/blocked_by", "--paginate"):
            return CommandResult(request=request, returncode=0, stdout="[]")
        if request.args == gh_api_args("repos/studykit/studykit-plugins/issues/44/dependencies/blocking", "--paginate"):
            return CommandResult(request=request, returncode=0, stdout="[]")
        return CommandResult(request=request, returncode=127, stderr=f"unexpected command: {request.args}")

    stdout = io.StringIO()

    code = cache_relationships_main(
        ["--project", str(tmp_path), "--session", "s1", "--type", "task", "--json", "44"],
        stdout=stdout,
        runner=runner,
        guard=guard,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_apply_pending_relationships"
    assert payload["issues"][0]["operation"] == "apply_relationships"
    assert payload["issues"][0]["issue"] == "44"
    assert payload["issues"][0]["applied"] == 1
    assert guard_calls[0].operation == "apply_relationships"
    assert guard_calls[0].payload["from_pending"] is True
    assert not pending_path.exists()


def test_cache_relationships_stages_existing_issue_relationship_intent(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-14T00:10:00Z")

    payload = stage_relationships_payload(
        project=tmp_path,
        issues=["#44"],
        parent="#28",
        blocked_by=("#33",),
        blocking=("#45",),
    )

    pending_path = cache.relationships_pending_file(repo(), 44)
    operations = cache.read_pending_issue_relationships(repo(), 44)
    assert payload["operation"] == "cache_stage_pending_relationships"
    assert payload["issue"] == "44"
    assert payload["relationships_file"] == str(pending_path)
    assert [(item.relationship, item.target_ref) for item in operations] == [
        ("parent", "#28"),
        ("blocked_by", "#33"),
        ("blocking", "#45"),
    ]


def test_cache_relationships_script_stages_existing_issue_relationship_intent(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-14T00:10:00Z")

    stdout = io.StringIO()
    code = cache_relationships_main(
        [
            "--project",
            str(tmp_path),
            "--stage",
            "--parent",
            "#28",
            "--blocked-by",
            "#33",
            "--json",
            "#44",
        ],
        stdout=stdout,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_stage_pending_relationships"
    assert payload["issue"] == "44"
    assert cache.relationships_pending_file(repo(), 44).is_file()
