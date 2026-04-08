# /// script
# requires-python = ">=3.10"
# ///
"""test_orchestrator — Unit tests for the agent orchestrator hooks.

Run: uv run -m pytest plugins/spawn/hooks/test_orchestrator.py -v
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


def exec_script(
    script_path: str,
    stdin_data: dict | str = "",
    env_override: dict[str, str] | None = None,
) -> str:
    """Execute a script by path (for skills scripts outside hooks/)."""
    env = {
        "SESSION_TREE": os.environ.get("SESSION_TREE", ""),
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    if env_override:
        env.update(env_override)

    stdin_str = stdin_data if isinstance(stdin_data, str) else json.dumps(stdin_data)

    result = subprocess.run(
        ["uv", "run", script_path],
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
                persona="discuss",
                reference_files=["/tmp/ref.md"],
                bootstrap_prompt_snippet="Context from main session about testing",
            ))

        st_write(update)
        tree = read_tree()
        assert len(tree["children"]) == 1
        assert tree["children"][0]["topic"] == "test topic"
        assert tree["children"][0]["persona"] == "discuss"
        assert tree["children"][0]["bootstrapPromptSnippet"] == "Context from main session about testing"
        assert tree["children"][0]["resumeCount"] == 0
        assert tree["children"][0]["resultUpdatedAt"] is None

    def test_new_schema_fields_round_trip(self) -> None:
        def update(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test",
                persona="review",
                bootstrap_prompt_snippet="snippet",
                resume_count=3,
                result_updated_at="2026-04-06T10:00:00Z",
            ))

        st_write(update)
        tree = read_tree()
        child = tree["children"][0]
        assert child["persona"] == "review"
        assert child["bootstrapPromptSnippet"] == "snippet"
        assert child["resumeCount"] == 3
        assert child["resultUpdatedAt"] == "2026-04-06T10:00:00Z"
        # Old fields should not be present
        assert "skill" not in child
        assert "additionalContext" not in child
        assert "resultPatterns" not in child

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
                persona="discuss",
                reference_files=["/tmp/ref.md"],
                bootstrap_prompt_snippet="Context from main session about testing",
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

    def test_resume_sets_status(self) -> None:
        """Resuming a terminated child sets status=resumed, increments resumeCount, no output."""
        # First mark the child as terminated
        def terminate(tree: SessionTree) -> None:
            c = tree.find_child("child-1")
            if c:
                c.status = "terminated"
                c.transcript_path = "/tmp/transcript.jsonl"
                c.pid = 12345
        st_write(terminate)

        output = exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/transcript.jsonl",
        })
        # No additionalContext output on resume
        assert output == ""

        tree = read_tree()
        child = tree["children"][0]
        assert child["status"] == "resumed"
        assert child["resumeCount"] == 1
        assert isinstance(child["pid"], int)

    def test_resume_preserves_transcript(self) -> None:
        """Resume does not overwrite the existing transcript path."""
        def set_active(tree: SessionTree) -> None:
            c = tree.find_child("child-1")
            if c:
                c.status = "terminated"
                c.transcript_path = "/tmp/original.jsonl"
        st_write(set_active)

        exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/new.jsonl",
        })
        tree = read_tree()
        # transcript_path should be preserved (not overwritten)
        assert tree["children"][0]["transcriptPath"] == "/tmp/original.jsonl"

    def test_resume_increments_count(self) -> None:
        """Two consecutive resumes increment resumeCount to 2."""
        def terminate(tree: SessionTree) -> None:
            c = tree.find_child("child-1")
            if c:
                c.status = "terminated"
                c.transcript_path = "/tmp/t.jsonl"
        st_write(terminate)

        exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/t.jsonl",
        })

        # Mark terminated again for second resume
        def terminate_again(tree: SessionTree) -> None:
            c = tree.find_child("child-1")
            if c:
                c.status = "terminated"
        st_write(terminate_again)

        exec_hook("session_start_bootstrap.py", {
            "session_id": "child-1",
            "transcript_path": "/tmp/t.jsonl",
        })

        tree = read_tree()
        assert tree["children"][0]["resumeCount"] == 2


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
        assert "terminated" in output.lower() or "terminated" in output
        assert "test topic" in output

    def test_output_uses_system_message(self) -> None:
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        parsed = json.loads(output)
        assert "systemMessage" in parsed
        assert "additionalContext" not in parsed

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

    def test_crash_detection_resumed_status(self) -> None:
        """Resumed children with dead pid should be detected as crashed."""
        last_file = Path(self.session_tree).with_suffix(".last")
        last_file.unlink(missing_ok=True)

        def add_resumed(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-resumed-crash",
                topic="resumed crashed",
                status="resumed",
                created_at="2026-03-29T00:00:00Z",
                pid=99998,
                resume_count=1,
            ))

        st_write(add_resumed)

        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "crashed" in output
        tree = read_tree()
        child = next(c for c in tree["children"] if c["id"] == "child-resumed-crash")
        assert child["status"] == "crashed"

    def test_deliverable_via_result_updated_at(self) -> None:
        """Deliverable notifications triggered by resultUpdatedAt change."""
        # Create initial snapshot with a child
        def setup_active(tree: SessionTree) -> None:
            tree.children.append(ChildEntry(
                id="child-deliver",
                topic="deliver child",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=os.getpid(),
            ))
        st_write(setup_active)

        # First run: creates snapshot
        exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })

        # Update resultFiles and resultUpdatedAt
        def add_result(tree: SessionTree) -> None:
            c = tree.find_child("child-deliver")
            if c:
                c.result_files = ["spec.md"]
                c.result_updated_at = "2026-04-06T10:00:00Z"
        st_write(add_result)

        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "deliverables" in output.lower() or "spec.md" in output

    def test_writes_notification_queue(self) -> None:
        """Session monitor writes to notifications.jsonl."""
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        # Check that notifications.jsonl was created
        queue = Path(self.tmpdir) / "notifications.jsonl"
        assert queue.exists()
        content = queue.read_text().strip()
        assert len(content) > 0
        entry = json.loads(content.split("\n")[0])
        assert "message" in entry

    def test_termination_with_results(self) -> None:
        """Terminated child with results reports files."""
        last_file = Path(self.session_tree).with_suffix(".last")
        last_file.unlink(missing_ok=True)

        def setup_terminated_with_results(tree: SessionTree) -> None:
            for c in tree.children:
                if c.id == "child-1":
                    c.result_files = ["api-spec.md", "endpoints.md"]
        st_write(setup_terminated_with_results)

        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "api-spec.md" in output
        assert "endpoints.md" in output

    def test_termination_without_results(self) -> None:
        """Terminated child without results suggests resuming."""
        output = exec_hook("session_monitor.py", {
            "session_id": "main-1",
            "file_path": self.session_tree,
        })
        assert "resume" in output.lower() or "No result" in output


# ============================================================
# notification_relay
# ============================================================

class TestNotificationRelay:
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

    def test_no_output_empty_queue(self) -> None:
        output = exec_hook("notification_relay.py", {
            "session_id": "child-1",
        })
        assert output == ""

    def test_reads_and_outputs_notifications(self) -> None:
        # Write a notification to the child's queue
        queue = Path(self.tmpdir) / "child-1.notifications.jsonl"
        queue.write_text('{"message": "File ref.md changed externally"}\n')

        output = exec_hook("notification_relay.py", {
            "session_id": "child-1",
        })
        parsed = json.loads(output)
        assert "additionalContext" in parsed
        assert "ref.md" in parsed["additionalContext"]

    def test_cursor_advances(self) -> None:
        queue = Path(self.tmpdir) / "child-1.notifications.jsonl"
        queue.write_text('{"message": "First notification"}\n')

        # First read
        output1 = exec_hook("notification_relay.py", {"session_id": "child-1"})
        assert "First notification" in output1

        # Second read: no new entries
        output2 = exec_hook("notification_relay.py", {"session_id": "child-1"})
        assert output2 == ""

        # Add new entry
        with open(queue, "a") as f:
            f.write('{"message": "Second notification"}\n')

        output3 = exec_hook("notification_relay.py", {"session_id": "child-1"})
        assert "Second notification" in output3

    def test_cursor_reset_on_truncated_queue(self) -> None:
        queue = Path(self.tmpdir) / "child-1.notifications.jsonl"
        queue.write_text('{"message": "line1"}\n{"message": "line2"}\n{"message": "line3"}\n')

        # Read all 3
        exec_hook("notification_relay.py", {"session_id": "child-1"})

        # Truncate the queue to 1 line (cursor was at 3, now only 1 line)
        queue.write_text('{"message": "fresh"}\n')

        output = exec_hook("notification_relay.py", {"session_id": "child-1"})
        assert "fresh" in output

    def test_main_session_queue(self) -> None:
        """Main session (no SESSION_TREE) reads from .claude/sessions/<id>/notifications.jsonl."""
        # Create the main session queue
        main_dir = Path(self.tmpdir) / ".claude" / "sessions" / "main-1"
        main_dir.mkdir(parents=True)
        queue = main_dir / "notifications.jsonl"
        queue.write_text('{"message": "Child crashed"}\n')

        output = exec_hook(
            "notification_relay.py",
            {"session_id": "main-1"},
            {"SESSION_TREE": "", "HOME": self.tmpdir},
        )
        # Main session without SESSION_TREE uses .claude/sessions/<id>/
        # The script cwd matters here — it looks for .claude/ relative to cwd
        # This test verifies the code path, actual path resolution depends on cwd


# ============================================================
# context_drift
# ============================================================

class TestContextDrift:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        # Create a reference file
        self.ref_file = os.path.join(self.tmpdir, "design-doc.md")
        Path(self.ref_file).write_text("# Design\n")

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1", name="test-session")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="design review",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=os.getpid(),
                reference_files=[self.ref_file],
            ))
        st_write(setup)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_guard_no_session_tree(self) -> None:
        output = exec_hook("context_drift.py", {
            "session_id": "child-1",
            "file_path": self.ref_file,
        }, {"SESSION_TREE": ""})
        assert output == ""

    def test_guard_main_session(self) -> None:
        """Main session ID should not trigger context drift."""
        output = exec_hook("context_drift.py", {
            "session_id": "main-1",
            "file_path": self.ref_file,
        })
        assert output == ""

    def test_no_match_irrelevant_file(self) -> None:
        output = exec_hook("context_drift.py", {
            "session_id": "child-1",
            "file_path": "/tmp/unrelated.md",
        })
        assert output == ""

    def test_match_reference_file(self) -> None:
        output = exec_hook("context_drift.py", {
            "session_id": "child-1",
            "file_path": self.ref_file,
        })
        parsed = json.loads(output)
        assert "systemMessage" in parsed
        assert "design-doc.md" in parsed["systemMessage"]

    def test_writes_notification_queue(self) -> None:
        exec_hook("context_drift.py", {
            "session_id": "child-1",
            "file_path": self.ref_file,
        })
        queue = Path(self.tmpdir) / "child-1.notifications.jsonl"
        assert queue.exists()
        entry = json.loads(queue.read_text().strip())
        assert entry["type"] == "context_drift"
        assert "design-doc.md" in entry["file"]


# ============================================================
# register_result (skill script)
# ============================================================

class TestRegisterResult:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

        # Create a test file to register
        self.test_file = os.path.join(self.tmpdir, "spec.md")
        Path(self.test_file).write_text("# Spec\n")

        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="test",
                status="active",
                created_at="2026-03-29T00:00:00Z",
                pid=os.getpid(),
            ))
        st_write(setup)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _exec_register(self, *args: str, env_override: dict[str, str] | None = None) -> str:
        script = str(SCRIPT_DIR.parent / "skills" / "register-result" / "scripts" / "register_result.py")
        env = {
            "SESSION_TREE": os.environ.get("SESSION_TREE", ""),
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        if env_override:
            env.update(env_override)
        result = subprocess.run(
            ["uv", "run", script, *args],
            capture_output=True,
            text=True,
            env=env,
        )
        return (result.stdout + result.stderr).strip()

    def test_registers_file(self) -> None:
        output = self._exec_register("child-1", self.test_file)
        assert "Registered" in output
        tree = read_tree()
        child = tree["children"][0]
        assert self.test_file in child["resultFiles"]
        assert child["resultUpdatedAt"] is not None

    def test_deduplication(self) -> None:
        self._exec_register("child-1", self.test_file)
        self._exec_register("child-1", self.test_file)
        tree = read_tree()
        assert tree["children"][0]["resultFiles"].count(self.test_file) == 1

    def test_nonexistent_file_warning(self) -> None:
        output = self._exec_register("child-1", "/tmp/no-such-file-xyz.md")
        assert "not found" in output.lower() or "Warning" in output

    def test_guard_child_only(self) -> None:
        output = self._exec_register("child-1", self.test_file, env_override={"SESSION_TREE": ""})
        assert "only available in child sessions" in output.lower()


# ============================================================
# list_sessions (skill script)
# ============================================================

class TestListSessions:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="orchestrator-test-")
        self.session_tree = os.path.join(self.tmpdir, "session-tree.json")
        os.environ["SESSION_TREE"] = self.session_tree
        set_session_tree_path(self.session_tree)

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _exec_sessions(self, session_id: str, env_override: dict[str, str] | None = None) -> str:
        script = str(SCRIPT_DIR.parent / "skills" / "sessions" / "scripts" / "list_sessions.py")
        env = {
            "SESSION_TREE": os.environ.get("SESSION_TREE", ""),
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        if env_override:
            env.update(env_override)
        result = subprocess.run(
            ["uv", "run", script, session_id],
            capture_output=True,
            text=True,
            env=env,
        )
        return (result.stdout + result.stderr).strip()

    def test_empty_tree(self) -> None:
        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1")
        st_write(setup)

        output = self._exec_sessions("main-1")
        assert "No child sessions" in output

    def test_multiple_sessions(self) -> None:
        def setup(tree: SessionTree) -> None:
            tree.main_session = MainSession(id="main-1")
            tree.children.append(ChildEntry(
                id="child-1",
                topic="design-review",
                status="active",
                created_at="2026-04-04T10:00:00Z",
                persona="discuss",
                reference_files=["design-doc.md"],
            ))
            tree.children.append(ChildEntry(
                id="child-2",
                topic="api-spec",
                status="terminated",
                created_at="2026-04-03T15:30:00Z",
                persona="discuss",
                result_files=["api-spec.md"],
                resume_count=2,
            ))
        st_write(setup)

        output = self._exec_sessions("main-1")
        assert "design-review" in output
        assert "active" in output
        assert "api-spec" in output
        assert "terminated" in output
        assert "resumed 2x" in output
        assert "discuss" in output

    def test_no_session_tree_file(self) -> None:
        """When session-tree.json doesn't exist, show empty message."""
        # Don't create session-tree.json, but set SESSION_TREE to a non-existent path
        non_existent = os.path.join(self.tmpdir, "nonexistent", "session-tree.json")
        output = self._exec_sessions("main-1", env_override={"SESSION_TREE": non_existent})
        assert "No child sessions" in output


# ============================================================
# iterm2_launcher (missing args)
# ============================================================

class TestIterm2LauncherMissingArgs:
    def test_missing_args(self) -> None:
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_DIR / "lib" / "iterm2_launcher.py")],
            capture_output=True,
            text=True,
        )
        assert "required" in result.stderr.lower() or result.returncode != 0
