# /// script
# requires-python = ">=3.10"
# ///
"""test_orchestrator — Unit tests for the agent orchestrator hooks.

Run: uv run -m pytest plugins/workflow/hooks/test_orchestrator.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from session_tree import ChildEntry, MainSession, SessionTree, set_session_tree_path, st_find_child, st_read, st_write

SCRIPT_DIR = Path(__file__).parent


def read_tree() -> dict:
    return json.loads(Path(os.environ["SESSION_TREE"]).read_text())


def exec_hook(
    script_name: str,
    stdin_data: dict | str,
    env_override: dict[str, str] | None = None,
) -> str:
    env = {
        "SESSION_TREE": os.environ.get("SESSION_TREE", ""),
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    if env_override:
        env.update(env_override)

    stdin_str = stdin_data if isinstance(stdin_data, str) else json.dumps(stdin_data)

    result = subprocess.run(
        ["uv", "run", str(SCRIPT_DIR / script_name)],
        input=stdin_str,
        capture_output=True,
        text=True,
        env=env,
    )
    return (result.stdout + result.stderr).strip()


# ============================================================
# session-tree library
# ============================================================

class TestSessionTreeLibrary:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_st_read_default_on_missing(self) -> None:
        result = st_read()
        assert len(result.children) == 0
        assert result.main_session is None

    def test_st_write_creates_and_updates(self) -> None:
        def update(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")

        st_write(update)
        tree = read_tree()
        assert tree["mainSession"]["name"] == "test-session"

    def test_st_write_adds_child(self) -> None:
        def update(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test topic",
                created_at="2026-03-29T00:00:00Z",
                skill="co-think-domain",
                result_patterns=["docs/*.md", "A4/**/*.requirement.md"],
                reference_files=["/tmp/ref.md"],
                additional_context="Context from main session about testing",
            ))

        st_write(update)
        tree = read_tree()
        assert len(tree["children"]) == 1
        assert tree["children"][0]["topic"] == "test topic"

    def test_st_find_child_existing(self) -> None:
        def setup(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(id="child-1", topic="test"))

        st_write(setup)
        found = st_find_child("child-1")
        assert found is not None
        assert found.id == "child-1"
        assert found.status == "pending"

    def test_st_find_child_missing(self) -> None:
        assert st_find_child("nonexistent") is None

    def test_st_find_child_empty_id(self) -> None:
        assert st_find_child("") is None


# ============================================================
# session_start_bootstrap
# ============================================================

class TestSessionStartBootstrap:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test topic",
                created_at="2026-03-29T00:00:00Z",
                skill="co-think-domain",
                result_patterns=["docs/*.md", "A4/**/*.requirement.md"],
                reference_files=["/tmp/ref.md"],
                additional_context="Context from main session about testing",
            ))

        st_write(setup)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_guard_on_session_tree(self) -> None:
        output = exec_hook("session_start_bootstrap.py", "", {"SESSION_TREE": ""})
        assert output == ""

    def test_unknown_session_id(self) -> None:
        output = exec_hook("session_start_bootstrap.py", {
            "session_id": "unknown-999",
            "transcript_path": "/tmp/t.jsonl",
        })
        assert output == ""

    def test_context_injection(self) -> None:
        output = exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/transcript.jsonl",
        })
        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "test topic" in context
        assert "/tmp/ref.md" in context
        assert "Context from main session" in context
        assert "docs/*.md" in context
        assert "co-think-domain" in context

    def test_metadata_writeback(self) -> None:
        exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/transcript.jsonl",
        })
        tree = read_tree()
        assert tree["children"][0]["status"] == "active"
        assert tree["children"][0]["id"] == "child-1"
        assert tree["children"][0]["transcriptPath"] == "/tmp/transcript.jsonl"
        assert isinstance(tree["children"][0]["pid"], int)


# ============================================================
# post_tool_result_collector
# ============================================================

class TestPostToolResultCollector:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test topic",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=os.getpid(),
                result_patterns=["docs/*.md", "A4/**/*.requirement.md"],
            ))

        st_write(setup)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ignores_non_write_tools(self) -> None:
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Read",
            "tool_input": {"file_path": "docs/foo.md"},
        })
        tree = read_tree()
        assert len(tree["children"][0]["resultFiles"]) == 0

    def test_registers_matching_write(self) -> None:
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/result.md"},
        })
        tree = read_tree()
        assert tree["children"][0]["resultFiles"][0] == "docs/result.md"

    def test_no_duplicates(self) -> None:
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/result.md"},
        })
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/result.md"},
        })
        tree = read_tree()
        assert len(tree["children"][0]["resultFiles"]) == 1

    def test_ignores_non_matching_path(self) -> None:
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/code.ts"},
        })
        tree = read_tree()
        assert len(tree["children"][0]["resultFiles"]) == 0

    def test_second_pattern_match(self) -> None:
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/result.md"},
        })
        exec_hook("post_tool_result_collector.py", {
            "session_id": "child-1",
            "tool_name": "Edit",
            "tool_input": {"file_path": "A4/test/foo.requirement.md"},
        })
        tree = read_tree()
        assert len(tree["children"][0]["resultFiles"]) == 2

    def test_guard_on_session_tree(self) -> None:
        output = exec_hook(
            "post_tool_result_collector.py",
            {
                "session_id": "child-1",
                "tool_name": "Write",
                "tool_input": {"file_path": "docs/x.md"},
            },
            {"SESSION_TREE": ""},
        )
        assert output == ""


# ============================================================
# session_end_collector
# ============================================================

class TestSessionEndCollector:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test topic",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=os.getpid(),
            ))

        st_write(setup)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_terminates_child(self) -> None:
        exec_hook("session_end_collector.py", {"session_id": "child-1"})
        tree = read_tree()
        assert tree["children"][0]["status"] == "terminated"

    def test_guard_on_session_tree(self) -> None:
        output = exec_hook(
            "session_end_collector.py",
            {"session_id": "child-1"},
            {"SESSION_TREE": ""},
        )
        assert output == ""

    def test_unknown_session(self) -> None:
        output = exec_hook("session_end_collector.py", {"session_id": "unknown-999"})
        assert output == ""


# ============================================================
# session_monitor
# ============================================================

class TestSessionMonitor:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test topic",
                status="terminated",
                created_at="2026-03-29T00:00:00Z",
            ))

        st_write(setup)

        # Remove leftover snapshot
        last_file = Path(self.session_tree).with_suffix(".last")
        last_file.unlink(missing_ok=True)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detects_termination(self) -> None:
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "terminated" in output
        assert "test topic" in output

    def test_no_output_when_no_changes(self) -> None:
        # First run creates snapshot
        exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        # Second run: no changes
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert output == ""

    def test_ignores_wrong_file_path(self) -> None:
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": "/tmp/other.json",
        })
        assert output == ""

    def test_handshake_timeout(self) -> None:
        last_file = Path(self.session_tree).with_suffix(".last")
        last_file.unlink(missing_ok=True)

        def add_stale(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-timeout",
                topic="stale child",
                created_at="2020-01-01T00:00:00Z",
            ))

        st_write(add_stale)

        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "failed to start" in output
        tree = read_tree()
        timeout_child = next(c for c in tree["children"] if c["id"] == "child-timeout")
        assert timeout_child["status"] == "failed_to_start"

    def test_crash_detection(self) -> None:
        last_file = Path(self.session_tree).with_suffix(".last")
        last_file.unlink(missing_ok=True)

        def add_crashed(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-crash",
                topic="crashed child",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=99999,
            ))

        st_write(add_crashed)

        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "crashed" in output
        tree = read_tree()
        crash_child = next(c for c in tree["children"] if c["id"] == "child-crash")
        assert crash_child["status"] == "crashed"


class TestIterm2LauncherMissingArgs:
    def test_missing_args(self) -> None:
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_DIR / "lib" / "iterm2_launcher.py")],
            capture_output=True,
            text=True,
        )
        assert "required" in result.stderr.lower() or result.returncode != 0
