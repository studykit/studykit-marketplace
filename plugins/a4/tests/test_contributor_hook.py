"""Tests for the repository-local a4 contributor hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _PLUGIN_ROOT / "dev" / "scripts" / "contributor_hook.py"


def _run_hook(
    subcommand: str,
    payload: dict,
    *,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), subcommand],
        input=json.dumps(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        check=False,
    )


def _env_for(runtime: str, project_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["A4_HOOK_RUNTIME"] = runtime
    if runtime == "claude":
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    else:
        env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def test_claude_pre_read_injects_layer_map_and_file_note(tmp_path: Path) -> None:
    project_dir = tmp_path
    target = project_dir / "plugins" / "a4" / "dev" / "notes.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Notes\n", encoding="utf-8")

    proc = _run_hook(
        "pre-read",
        {
            "session_id": "claude-session",
            "cwd": str(project_dir),
            "tool_name": "Read",
            "tool_input": {"file_path": str(target)},
        },
        env=_env_for("claude", project_dir),
    )

    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "**a4 plugin layer map**" in context
    assert "**a4 (read)** `plugins/a4/dev/notes.md`" in context
    assert "plugins/a4/dev/CLAUDE.md" in context


def test_guardrail_files_are_plugin_contributor_audience_regardless_of_layer(
    tmp_path: Path,
) -> None:
    cases = [
        ("root-agents", tmp_path / "plugins" / "a4" / "AGENTS.md"),
        (
            "authoring-agents",
            tmp_path / "plugins" / "a4" / "authoring" / "AGENTS.md",
        ),
        (
            "authoring-claude",
            tmp_path / "plugins" / "a4" / "authoring" / "CLAUDE.md",
        ),
    ]

    for session_id, target in cases:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Guardrail\n", encoding="utf-8")

        proc = _run_hook(
            "pre-read",
            {
                "session_id": session_id,
                "cwd": str(tmp_path),
                "tool_name": "Read",
                "tool_input": {"file_path": str(target)},
            },
            env=_env_for("claude", tmp_path),
        )

        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)
        context = out["hookSpecificOutput"]["additionalContext"]
        assert (
            "— audience: plugin contributors editing this directory's guardrails."
            in context
        )
        assert "— audience: workspace authors and skill runtime" not in context


def test_codex_pre_edit_is_silent_because_context_is_unsupported(
    tmp_path: Path,
) -> None:
    proc = _run_hook(
        "pre-edit",
        {
            "session_id": "codex-session",
            "turn_id": "turn-1",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "command": (
                    "*** Begin Patch\n"
                    "*** Update File: plugins/a4/dev/notes.md\n"
                    "+# Notes\n"
                    "*** End Patch\n"
                )
            },
        },
        env=_env_for("codex", tmp_path),
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""


def test_codex_post_edit_aggregates_apply_patch_guidance(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "a4" / "dev" / "notes.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Notes\n", encoding="utf-8")
    payload = {
        "session_id": "codex-session",
        "turn_id": "turn-1",
        "cwd": str(tmp_path),
        "hook_event_name": "PostToolUse",
        "tool_name": "apply_patch",
        "tool_input": {
            "command": (
                "*** Begin Patch\n"
                "*** Update File: plugins/a4/dev/notes.md\n"
                "-# Notes\n"
                "+# Notes\n"
                "*** End Patch\n"
            )
        },
    }

    proc = _run_hook("post-edit", payload, env=_env_for("codex", tmp_path))

    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "**a4 plugin layer map**" in context
    assert "**a4 (edit)** `plugins/a4/dev/notes.md`" in context
    assert "plugins/a4/dev/CLAUDE.md" in context

    second = _run_hook("post-edit", payload, env=_env_for("codex", tmp_path))
    assert second.returncode == 0, second.stderr
    assert second.stdout == ""


def test_codex_session_start_sweeps_stale_contributor_sentinels(
    tmp_path: Path,
) -> None:
    record_dir = tmp_path / ".claude" / "tmp" / "a4-edited"
    record_dir.mkdir(parents=True)
    stale = record_dir / "a4-contributor-files-old-session.txt"
    fresh = record_dir / "a4-contributor-map-fresh-session.flag"
    stale.write_text("x\n", encoding="utf-8")
    fresh.write_text("x\n", encoding="utf-8")
    old_time = time.time() - (25 * 60 * 60)
    os.utime(stale, (old_time, old_time))

    proc = _run_hook(
        "session-start",
        {
            "session_id": "codex-session",
            "cwd": str(tmp_path),
            "hook_event_name": "SessionStart",
            "source": "startup",
        },
        env=_env_for("codex", tmp_path),
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""
    assert not stale.exists()
    assert fresh.exists()
