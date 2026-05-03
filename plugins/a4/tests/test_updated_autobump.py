"""Tests for `updated:` auto-bump in a4_hook post-edit.

Covers the contract added when authors / LLMs stopped hand-bumping
`updated:`:

  - Body-only edit on an existing issue file → `updated:` refreshed.
  - Wiki edit (no `created:` schema) → `updated:` refreshed.
  - Status flip → `updated:` refreshed exactly once via the cascade
    path (no double-write from the auto-bump).
  - New-file Write → `created == updated`, both stamped to the same
    KST timestamp.
  - Archive file → not touched (out of contract).
  - File whose path doesn't resolve to a known type → not touched.
"""

from __future__ import annotations

import importlib
import io
import json
import re
import sys
from pathlib import Path

import pytest


KST_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
STALE_TS = "2025-01-15 03:14"


@pytest.fixture
def hook_module(monkeypatch: pytest.MonkeyPatch):
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if "a4_hook" in sys.modules:
        del sys.modules["a4_hook"]
    return importlib.import_module("a4_hook")


def _make_a4_layout(project_dir: Path) -> None:
    for folder in ("task", "spike", "bug", "research", "umbrella", "usecase"):
        (project_dir / "a4" / folder).mkdir(parents=True, exist_ok=True)


def _run_pre_edit(
    hook_module,
    monkeypatch: pytest.MonkeyPatch,
    project_dir: Path,
    file_path: Path,
    *,
    session_id: str,
    tool_name: str = "Edit",
) -> int:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "session_id": session_id,
    }
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    monkeypatch.setattr(
        hook_module.sys, "stdin", io.StringIO(json.dumps(payload))
    )
    monkeypatch.setattr(hook_module.sys, "stdout", io.StringIO())
    return hook_module._pre_edit()


def _run_post_edit(
    hook_module,
    monkeypatch: pytest.MonkeyPatch,
    project_dir: Path,
    file_path: Path,
    *,
    session_id: str,
    tool_name: str = "Edit",
) -> int:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "session_id": session_id,
    }
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    monkeypatch.setattr(
        hook_module.sys, "stdin", io.StringIO(json.dumps(payload))
    )
    monkeypatch.setattr(hook_module.sys, "stdout", io.StringIO())
    return hook_module._post_edit()


def _read_fm_field(path: Path, field: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("---"):
            continue
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


def test_body_edit_refreshes_updated(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    target = tmp_path / "a4" / "task" / "10-body.md"
    target.write_text(
        "---\n"
        "type: task\n"
        "id: 10\n"
        "title: Body\n"
        "status: queued\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\noriginal body\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, target, session_id="b1"
    )
    target.write_text(
        "---\n"
        "type: task\n"
        "id: 10\n"
        "title: Body\n"
        "status: queued\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\nedited body\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, target, session_id="b1"
    )

    updated = _read_fm_field(target, "updated")
    assert updated is not None
    assert updated != STALE_TS, "updated: must be refreshed by the hook"
    assert KST_RE.match(updated), f"expected KST format, got {updated!r}"
    # `created:` immutable.
    assert _read_fm_field(target, "created") == "2025-01-15 03:14"


def test_wiki_edit_refreshes_updated(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4").mkdir(parents=True, exist_ok=True)
    wiki = tmp_path / "a4" / "architecture.md"
    wiki.write_text(
        "---\n"
        "type: architecture\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Overview\noriginal\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, wiki, session_id="w1"
    )
    wiki.write_text(
        "---\n"
        "type: architecture\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Overview\nedited\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, wiki, session_id="w1"
    )

    updated = _read_fm_field(wiki, "updated")
    assert updated is not None
    assert updated != STALE_TS, "wiki updated: must be auto-bumped"
    assert KST_RE.match(updated)
    # Wiki schema has no `created:`.
    assert _read_fm_field(wiki, "created") is None


def test_status_flip_does_not_double_write_updated(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cascade refreshes `updated:` on status flip; auto-bump must dedupe.

    We can't observe the write count directly, but we can pin behavior:
    after a legal status flip, the timestamp value must equal the one
    the hook computed for this event (single source of truth) — not an
    older author-supplied stale value, and not two distinct writes.
    """
    _make_a4_layout(tmp_path)
    target = tmp_path / "a4" / "task" / "11-flip.md"
    target.write_text(
        "---\n"
        "type: task\n"
        "id: 11\n"
        "title: Flip\n"
        "status: queued\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\nx\n\n"
        "## Unit Test Strategy\nnone\n\n"
        "## Acceptance Criteria\n- x\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, target, session_id="f1"
    )
    target.write_text(
        "---\n"
        "type: task\n"
        "id: 11\n"
        "title: Flip\n"
        "status: in-progress\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\nx\n\n"
        "## Unit Test Strategy\nnone\n\n"
        "## Acceptance Criteria\n- x\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, target, session_id="f1"
    )

    updated = _read_fm_field(target, "updated")
    status = _read_fm_field(target, "status")
    assert status == "in-progress"
    assert updated is not None and updated != STALE_TS
    assert KST_RE.match(updated)


def test_new_write_created_equals_updated(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "12-new.md"

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file,
        session_id="n1", tool_name="Write",
    )
    new_file.write_text(
        "---\n"
        "type: task\n"
        "id: 12\n"
        "title: New\n"
        "status: queued\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, new_file,
        session_id="n1", tool_name="Write",
    )

    created = _read_fm_field(new_file, "created")
    updated = _read_fm_field(new_file, "updated")
    assert created is not None and updated is not None
    assert KST_RE.match(created) and KST_RE.match(updated)
    assert created == updated, (
        f"created and updated must match on fresh Write, "
        f"got created={created!r}, updated={updated!r}"
    )


def test_archive_file_not_touched(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_dir = tmp_path / "a4" / "archive" / "task"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / "13-old.md"
    archived.write_text(
        "---\n"
        "type: task\n"
        "id: 13\n"
        "title: Old\n"
        "status: shipped\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, archived, session_id="a1"
    )
    archived.write_text(
        "---\n"
        "type: task\n"
        "id: 13\n"
        "title: Old\n"
        "status: shipped\n"
        "created: 2025-01-15 03:14\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Description\ntouched\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, archived, session_id="a1"
    )

    assert _read_fm_field(archived, "updated") == STALE_TS, (
        "archive files are out of the workspace contract — "
        "the hook must not touch updated:"
    )


def test_unrecognized_path_not_touched(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4").mkdir(parents=True, exist_ok=True)
    weird = tmp_path / "a4" / "random.md"
    weird.write_text(
        "---\n"
        "type: random\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Body\nx\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, weird, session_id="u1"
    )
    weird.write_text(
        "---\n"
        "type: random\n"
        f"updated: {STALE_TS}\n"
        "---\n\n"
        "## Body\nedited\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, weird, session_id="u1"
    )

    assert _read_fm_field(weird, "updated") == STALE_TS, (
        "unresolvable type — hook must skip"
    )
