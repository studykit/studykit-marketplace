"""Tests for `created:` auto-stamp in a4_hook.

Covers PreToolUse new-file snapshot + PostToolUse stamp:

  - New-file Write under an issue folder → `created:` stamped in
    `YYYY-MM-DD HH:mm` KST format, inserted immediately before
    `updated:`.
  - Edit on an existing file → no stamp.
  - File whose schema lacks `created:` (wiki) → no stamp even on new
    Write.
  - Author-supplied `created:` → immutable; not overwritten.
  - The status-cascade `updated:` refresh emits the same KST timestamp
    format.
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
    tool_name: str = "Write",
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
    tool_name: str = "Write",
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
    """Quick scalar lookup from frontmatter without YAML loading."""
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("---"):
            continue
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


def _frontmatter_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    after = text[4:]
    end = after.find("\n---")
    assert end != -1, "no closing fence"
    return after[:end]


def test_created_stamped_on_new_task_write(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "1-new.md"

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s1"
    )

    new_file.write_text(
        "---\n"
        "type: task\n"
        "id: 1\n"
        "title: New\n"
        "status: queued\n"
        "updated: 2026-05-02 14:30\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    _run_post_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s1"
    )

    created = _read_fm_field(new_file, "created")
    assert created is not None, "created: should be stamped"
    assert KST_RE.match(created), f"expected KST HH:mm format, got {created!r}"


def test_created_inserted_before_updated(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "2-order.md"

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s2"
    )
    new_file.write_text(
        "---\n"
        "type: task\n"
        "id: 2\n"
        "title: Order\n"
        "status: queued\n"
        "updated: 2026-05-02 14:30\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s2"
    )

    fm_block = _frontmatter_block(new_file)
    lines = [line for line in fm_block.split("\n") if line.strip()]
    created_idx = next(
        i for i, line in enumerate(lines) if line.startswith("created:")
    )
    updated_idx = next(
        i for i, line in enumerate(lines) if line.startswith("updated:")
    )
    assert created_idx < updated_idx, "created: must precede updated:"
    assert created_idx + 1 == updated_idx, (
        "created: must be the line immediately before updated:"
    )


def test_existing_file_edit_does_not_stamp_created(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    existing = tmp_path / "a4" / "task" / "3-live.md"
    existing.write_text(
        "---\n"
        "type: task\n"
        "id: 3\n"
        "title: Live\n"
        "status: queued\n"
        "updated: 2026-05-02 14:30\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, existing,
        session_id="s3", tool_name="Edit",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, existing,
        session_id="s3", tool_name="Edit",
    )

    assert _read_fm_field(existing, "created") is None, (
        "Edit on an existing file (no prior `created:`) must not stamp"
    )


def test_author_supplied_created_is_immutable(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_a4_layout(tmp_path)
    new_file = tmp_path / "a4" / "task" / "4-auth.md"

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s4"
    )
    author_value = "2025-01-15 03:14"
    new_file.write_text(
        "---\n"
        "type: task\n"
        "id: 4\n"
        "title: Auth\n"
        "status: queued\n"
        f"created: {author_value}\n"
        "updated: 2026-05-02 14:30\n"
        "---\n\n"
        "## Description\nx\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, new_file, session_id="s4"
    )

    assert _read_fm_field(new_file, "created") == author_value


def test_wiki_new_write_does_not_stamp_created(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "a4").mkdir(parents=True, exist_ok=True)
    wiki_file = tmp_path / "a4" / "architecture.md"

    _run_pre_edit(
        hook_module, monkeypatch, tmp_path, wiki_file, session_id="s5"
    )
    wiki_file.write_text(
        "---\n"
        "type: architecture\n"
        "updated: 2026-05-02 14:30\n"
        "---\n\n"
        "## Overview\nx\n",
        encoding="utf-8",
    )
    _run_post_edit(
        hook_module, monkeypatch, tmp_path, wiki_file, session_id="s5"
    )

    assert _read_fm_field(wiki_file, "created") is None, (
        "wiki schema has no `created:` field — must not be stamped"
    )


def test_now_kst_returns_minute_precision_format() -> None:
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from common import now_kst  # noqa: WPS433

    value = now_kst()
    assert KST_RE.match(value), f"now_kst() must return YYYY-MM-DD HH:mm, got {value!r}"


def test_types_with_created_excludes_wiki() -> None:
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from markdown_validator.frontmatter import types_with_created  # noqa: WPS433

    types = types_with_created()
    assert "wiki" not in types
    # Every issue family + the umbrella/review/spec/idea/brainstorm types
    # carry `created:` per their schema.
    for expected in (
        "usecase", "task", "bug", "spike", "research",
        "umbrella", "review", "spec", "idea", "brainstorm",
    ):
        assert expected in types, f"{expected!r} should be in types_with_created()"
