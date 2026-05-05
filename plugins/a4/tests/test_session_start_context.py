"""Tests for SessionStart a4 workspace context injection."""

from __future__ import annotations

import importlib
import io
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def hook_module():
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if "a4_hook" in sys.modules:
        del sys.modules["a4_hook"]
    return importlib.import_module("a4_hook")


def _run_session_start(
    hook_module,
    monkeypatch: pytest.MonkeyPatch,
    project_dir: Path,
    *,
    runtime: str,
) -> str:
    payload = {
        "session_id": f"{runtime}-session",
        "cwd": str(project_dir),
        "hook_event_name": "SessionStart",
    }
    monkeypatch.setenv("A4_HOOK_RUNTIME", runtime)
    if runtime == "codex":
        plugin_root = Path(__file__).resolve().parent.parent
        monkeypatch.setenv("PLUGIN_ROOT", str(plugin_root))
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    else:
        plugin_root = Path(__file__).resolve().parent.parent
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
        monkeypatch.delenv("PLUGIN_ROOT", raising=False)

    monkeypatch.setattr(hook_module.sys, "stdin", io.StringIO(json.dumps(payload)))
    captured = io.StringIO()
    monkeypatch.setattr(hook_module.sys, "stdout", captured)

    assert hook_module._session_start() == 0
    return captured.getvalue()


@pytest.mark.parametrize("runtime", ["claude", "codex"])
def test_session_start_includes_authoring_entrypoint_index(
    hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runtime: str
) -> None:
    (tmp_path / "a4").mkdir()

    out = _run_session_start(
        hook_module, monkeypatch, tmp_path, runtime=runtime
    )

    payload = json.loads(out)
    context = payload["hookSpecificOutput"]["additionalContext"]
    plugin_root = Path(__file__).resolve().parent.parent
    authoring_dir = plugin_root / "authoring"
    assert "## a4/ workspace — type → file location" in context
    assert "**a4 authoring entrypoints**" in context
    assert f"Authoring directory: `{authoring_dir}`" in context
    assert "from the authoring directory above" in context
    assert "Before committing a4-related changes" in context
    assert "`commit-message-convention.md`" in context
    assert str(authoring_dir / "commit-message-convention.md") not in context
    assert "`task` →" in context
    assert "`task` → `task-authoring.md`" in context
    assert str(authoring_dir / "task-authoring.md") not in context
    assert "frontmatter-common.md" not in context
    assert "frontmatter-issue.md" not in context
    assert "issue-family-lifecycle.md" not in context
    assert "`domain` →" in context
    assert "`domain` → `domain-authoring.md`" in context
    assert str(authoring_dir / "domain-authoring.md") not in context
