"""Tests for workflow shell environment helpers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_env import (  # noqa: E402
    codex_env_file_path,
    detect_shell_runtime,
    render_shell_exports,
    workflow_project_dir_from_env,
    workflow_session_id_from_env,
)


def test_render_shell_exports_quotes_values() -> None:
    rendered = render_shell_exports(
        {
            "WORKFLOW": "/tmp/plugin root/scripts/workflow",
            "WORKFLOW_PLUGIN_ROOT": "/tmp/plugin root",
            "WORKFLOW_PROJECT_DIR": "/tmp/project",
            "WORKFLOW_SESSION_ID": "session-1",
        }
    )

    assert "export WORKFLOW='/tmp/plugin root/scripts/workflow'" in rendered
    assert "export WORKFLOW_PLUGIN_ROOT='/tmp/plugin root'" in rendered
    assert "export WORKFLOW_PROJECT_DIR=/tmp/project" in rendered
    assert "export WORKFLOW_SESSION_ID=session-1" in rendered


def test_detect_shell_runtime_uses_exact_session_markers() -> None:
    assert detect_shell_runtime(environ={"CLAUDE_CODE_SHELL": "zsh"}).name == ""
    assert detect_shell_runtime(environ={"CODEX_THREAD_ID": "codex-1"}).name == "codex"
    assert detect_shell_runtime(environ={"CODEX_THREAD_ID": "codex-1"}).session_id == "codex-1"
    assert detect_shell_runtime(environ={"CLAUDE_CODE_SESSION_ID": "claude-1"}).name == "claude"
    assert detect_shell_runtime(environ={"CLAUDE_CODE_SESSION_ID": "claude-1"}).session_id == "claude-1"


def test_detect_shell_runtime_prefers_claude_when_both_markers_exist() -> None:
    runtime = detect_shell_runtime(
        environ={
            "CODEX_THREAD_ID": "codex-1",
            "CLAUDE_CODE_SESSION_ID": "claude-1",
        }
    )

    assert runtime.name == "claude"
    assert runtime.session_id == "claude-1"


def test_workflow_project_and_session_defaults_from_env(tmp_path: Path) -> None:
    assert workflow_project_dir_from_env(environ={"WORKFLOW_PROJECT_DIR": str(tmp_path)}) == tmp_path.resolve()
    assert workflow_session_id_from_env(environ={"WORKFLOW_SESSION_ID": "workflow-1"}) == "workflow-1"


def test_codex_env_file_path_uses_workflow_hook_state(tmp_path: Path) -> None:
    path = codex_env_file_path(tmp_path, "session/with spaces")

    assert path.parent == tmp_path / ".workflow-cache" / "hook-state"
    assert path.name.startswith("workflow-env-codex-session_with_spaces")
    assert path.suffix == ".sh"


def test_workflow_wrapper_sources_codex_env_file(tmp_path: Path) -> None:
    script = tmp_path / "print_workflow_env.py"
    script.write_text(
        "import json, os\n"
        "print(json.dumps({key: os.environ.get(key) for key in "
        "('WORKFLOW', 'WORKFLOW_PLUGIN_ROOT', 'WORKFLOW_PROJECT_DIR', 'WORKFLOW_SESSION_ID')}))\n",
        encoding="utf-8",
    )
    env_file = codex_env_file_path(tmp_path, "codex-shell")
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "\n".join(
            [
                f"export WORKFLOW={_SCRIPTS_DIR / 'workflow'}",
                f"export WORKFLOW_PLUGIN_ROOT={_PLUGIN_ROOT}",
                f"export WORKFLOW_PROJECT_DIR={tmp_path}",
                "export WORKFLOW_SESSION_ID=parent-shell",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={
            "CODEX_THREAD_ID": "codex-shell",
            "PATH": os.environ.get("PATH", ""),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["WORKFLOW"] == str(_SCRIPTS_DIR / "workflow")
    assert payload["WORKFLOW_PLUGIN_ROOT"] == str(_PLUGIN_ROOT)
    assert payload["WORKFLOW_PROJECT_DIR"] == str(tmp_path)
    assert payload["WORKFLOW_SESSION_ID"] == "parent-shell"


def test_workflow_wrapper_does_not_use_codex_thread_id_as_session_fallback(tmp_path: Path) -> None:
    script = tmp_path / "print_workflow_session.py"
    script.write_text(
        "import os\n"
        "print(os.environ.get('WORKFLOW_SESSION_ID', '<missing>'))\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={
            "CODEX_THREAD_ID": "codex-subagent-thread",
            "PATH": os.environ.get("PATH", ""),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.stdout.strip() == "<missing>"


def test_workflow_wrapper_claude_path_does_not_export_session_from_claude_code_session_id(tmp_path: Path) -> None:
    script = tmp_path / "print_workflow_session.py"
    script.write_text(
        "import os\n"
        "print(os.environ.get('WORKFLOW_SESSION_ID', '<missing>'))\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={
            "CLAUDE_CODE_SESSION_ID": "claude-shell-session",
            "PATH": os.environ.get("PATH", ""),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.stdout.strip() == "<missing>"


def test_workflow_wrapper_prefers_claude_when_both_runtime_markers_exist(tmp_path: Path) -> None:
    script = tmp_path / "print_workflow_session.py"
    script.write_text(
        "import os\n"
        "print(os.environ.get('WORKFLOW_SESSION_ID', '<missing>'))\n",
        encoding="utf-8",
    )
    env_file = codex_env_file_path(tmp_path, "codex-shell")
    env_file.parent.mkdir(parents=True)
    env_file.write_text("export WORKFLOW_SESSION_ID=codex-parent\n", encoding="utf-8")

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={
            "CODEX_THREAD_ID": "codex-shell",
            "CLAUDE_CODE_SESSION_ID": "claude-shell",
            "PATH": os.environ.get("PATH", ""),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.stdout.strip() == "<missing>"


def test_workflow_wrapper_uses_terminal_defaults_without_runtime_marker(tmp_path: Path) -> None:
    script = tmp_path / "print_terminal_defaults.py"
    script.write_text(
        "import json, os\n"
        "print(json.dumps({key: os.environ.get(key) for key in "
        "('WORKFLOW', 'WORKFLOW_PLUGIN_ROOT', 'WORKFLOW_PROJECT_DIR', 'WORKFLOW_SESSION_ID')}))\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={"PATH": os.environ.get("PATH", "")},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["WORKFLOW"] == str(_SCRIPTS_DIR / "workflow")
    assert payload["WORKFLOW_PLUGIN_ROOT"] == str(_PLUGIN_ROOT)
    assert payload["WORKFLOW_PROJECT_DIR"] == str(tmp_path)
    assert payload["WORKFLOW_SESSION_ID"] is None


def test_workflow_wrapper_terminal_defaults_use_launcher_plugin_root(tmp_path: Path) -> None:
    script = tmp_path / "print_terminal_defaults.py"
    script.write_text(
        "import json, os\n"
        "print(json.dumps({key: os.environ.get(key) for key in "
        "('WORKFLOW', 'WORKFLOW_PLUGIN_ROOT', 'WORKFLOW_PROJECT_DIR')}))\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(_SCRIPTS_DIR / "workflow"), str(script)],
        check=True,
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", ""),
            "WORKFLOW": "/tmp/stale/workflow",
            "WORKFLOW_PLUGIN_ROOT": "/tmp/stale/plugin",
            "WORKFLOW_PROJECT_DIR": str(tmp_path / "project-from-env"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["WORKFLOW"] == str(_SCRIPTS_DIR / "workflow")
    assert payload["WORKFLOW_PLUGIN_ROOT"] == str(_PLUGIN_ROOT)
    assert payload["WORKFLOW_PROJECT_DIR"] == str(tmp_path / "project-from-env")
