"""Tests for the agent-facing workflow pending comment append entrypoint."""

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
from workflow_cache_comments import main as cache_comments_main  # noqa: E402
from workflow_command import CommandRequest, CommandResult  # noqa: E402
from workflow_github import DEFAULT_ISSUE_FIELDS, GitHubRepository  # noqa: E402
from workflow_providers import ProviderRequest  # noqa: E402


def repo() -> GitHubRepository:
    return GitHubRepository(host="github.com", owner="studykit", name="studykit-plugins")


def issue_payload() -> dict[str, object]:
    return {
        "number": 43,
        "title": "Cached issue",
        "state": "OPEN",
        "stateReason": None,
        "body": "Cached body.",
        "labels": [],
        "updatedAt": "2026-05-14T00:00:00Z",
        "comments": [],
    }


def refreshed_issue_payload() -> dict[str, object]:
    payload = issue_payload()
    payload["comments"] = [
        {
            "id": "IC_kwDOQplzFM8AAAABCKrz_g",
            "url": "https://github.com/studykit/studykit-plugins/issues/43#issuecomment-4440388606",
            "author": {"login": "studykit"},
            "body": "Pending comment body.\n",
            "createdAt": "2026-05-14T00:00:00Z",
            "updatedAt": "2026-05-14T00:00:00Z",
        }
    ]
    return payload


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


def test_cache_comments_script_dispatches_guarded_pending_comment_append(tmp_path: Path) -> None:
    write_config(tmp_path)
    cache = GitHubIssueCache.for_project(tmp_path, configured_repo=repo())
    cache.write_issue_bundle(repo(), issue_payload(), fetched_at="2026-05-14T00:10:00Z")
    pending_dir = cache.comments_pending_dir(repo(), 43)
    pending_dir.mkdir(parents=True)
    pending_file = pending_dir / "2026-05-14T000000Z-local.md"
    pending_file.write_text(
        """---
schema_version: 1
---

Pending comment body.
""",
        encoding="utf-8",
    )
    guard_calls: list[ProviderRequest] = []

    def guard(request: ProviderRequest) -> None:
        guard_calls.append(request)

    def runner(request: CommandRequest) -> CommandResult:
        if request.args[:3] == ("gh", "issue", "comment"):
            body_file = Path(request.args[request.args.index("--body-file") + 1])
            assert body_file.read_text(encoding="utf-8") == "Pending comment body.\n"
            return CommandResult(request=request, returncode=0)
        if request.args == gh_issue_view_args(43, ",".join(DEFAULT_ISSUE_FIELDS)):
            return CommandResult(request=request, returncode=0, stdout=json.dumps(refreshed_issue_payload()))
        return CommandResult(request=request, returncode=127, stderr="unexpected command")

    stdout = io.StringIO()

    code = cache_comments_main(
        ["--project", str(tmp_path), "--session", "s1", "--type", "task", "--json", "43"],
        stdout=stdout,
        runner=runner,
        guard=guard,
    )

    payload = json.loads(stdout.getvalue())
    assert code == 0
    assert payload["operation"] == "cache_append_pending_comments"
    assert payload["issues"][0]["operation"] == "append_pending_comments"
    assert payload["issues"][0]["issue"] == "43"
    assert payload["issues"][0]["appended"] == 1
    assert guard_calls[0].operation == "add_comment"
    assert guard_calls[0].payload["from_pending"] is True
    assert not pending_file.exists()
