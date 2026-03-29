# /// script
# requires-python = ">=3.10"
# ///
"""test_orchestrator — Unit tests for the agent orchestrator hooks.

Run from project root: uv run global/hooks/test_orchestrator.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# --- Test infrastructure ---

_pass = 0
_fail = 0
_total = 0


def assert_eq(label: str, expected: object, actual: object) -> None:
    global _pass, _fail, _total
    _total += 1
    if expected == actual:
        print(f"  ✓ {label}")
        _pass += 1
    else:
        print(f"  ✗ {label}")
        print(f"    expected: {expected!r}")
        print(f"    actual:   {actual!r}")
        _fail += 1


def assert_contains(label: str, needle: str, haystack: str) -> None:
    global _pass, _fail, _total
    _total += 1
    if needle in haystack:
        print(f"  ✓ {label}")
        _pass += 1
    else:
        print(f"  ✗ {label}")
        print(f"    expected to contain: {needle!r}")
        print(f"    actual: {haystack!r}")
        _fail += 1


def _run_hook(script_name: str, stdin_data: dict | str, env_override: dict | None = None) -> str:
    """Run a hook script via uv run, returning combined stdout+stderr."""
    env = os.environ.copy()
    env["SESSION_TREE"] = os.environ.get("SESSION_TREE", "")
    if env_override:
        env.update(env_override)

    stdin_str = json.dumps(stdin_data) if isinstance(stdin_data, dict) else stdin_data

    result = subprocess.run(
        ["uv", "run", str(SCRIPT_DIR / script_name)],
        input=stdin_str,
        capture_output=True,
        text=True,
        env=env,
    )
    return (result.stdout + result.stderr).strip()


def _read_tree() -> dict:
    return json.loads(Path(os.environ["SESSION_TREE"]).read_text())


def main() -> None:
    global _pass, _fail, _total

    with tempfile.TemporaryDirectory(prefix="orchestrator-test-") as tmpdir:
        session_tree = Path(tmpdir) / "session-tree.json"
        os.environ["SESSION_TREE"] = str(session_tree)

        # Reload session_tree module with new env.
        sys.path.insert(0, str(SCRIPT_DIR / "lib"))
        import session_tree as st_mod
        st_mod._SESSION_TREE = str(session_tree)
        from session_tree import st_find_child, st_read, st_write

        # ============================================================
        print("\n=== 1. session_tree.py library ===\n")

        # 1a. st_read returns default when file doesn't exist.
        print("[st_read] default on missing file")
        result = st_read()
        assert_eq("returns empty children array", 0, len(result["children"]))
        assert_eq("mainSession is None", None, result["mainSession"])

        # 1b. st_write creates and updates the file.
        print("[st_write] create and update")

        def set_main(tree: dict) -> None:
            tree["mainSession"] = {"id": "main-1", "name": "test-session"}

        st_write(set_main)
        tree = _read_tree()
        assert_eq("mainSession.name written", "test-session", tree["mainSession"]["name"])

        # 1c. st_write adds a child entry.
        print("[st_write] add child entry")

        def add_child(tree: dict) -> None:
            tree["children"].append({
                "id": "child-1",
                "topic": "test topic",
                "status": "pending",
                "createdAt": "2026-03-29T00:00:00Z",
                "pid": None,
                "skill": "co-think-domain",
                "transcriptPath": None,
                "resultPatterns": ["docs/*.md", "A4/**/*.requirement.md"],
                "resultFiles": [],
                "referenceFiles": ["/tmp/ref.md"],
                "contextSummary": "Context from main session about testing",
            })

        st_write(add_child)
        tree = _read_tree()
        assert_eq("children count is 1", 1, len(tree["children"]))
        assert_eq("child topic", "test topic", tree["children"][0]["topic"])

        # 1d. st_find_child finds existing child.
        print("[st_find_child] existing child")
        found = st_find_child("child-1")
        assert_eq("found child id", "child-1", found["id"])
        assert_eq("found child status", "pending", found["status"])

        # 1e. st_find_child returns None for missing child.
        print("[st_find_child] missing child")
        assert_eq("returns None for missing", None, st_find_child("nonexistent"))

        # 1f. st_write with None transform (edge case — test no crash).
        print("[st_find_child] empty id")
        assert_eq("returns None for empty id", None, st_find_child(""))

        # ============================================================
        print("\n=== 2. session_start_bootstrap.py ===\n")

        # 2a. Exits silently when SESSION_TREE is unset.
        print("[bootstrap] guard on SESSION_TREE")
        output = _run_hook("session_start_bootstrap.py", "", env_override={"SESSION_TREE": ""})
        assert_eq("no output when SESSION_TREE unset", "", output)

        # 2b. Exits silently when session_id not found.
        print("[bootstrap] unknown session_id")
        output = _run_hook(
            "session_start_bootstrap.py",
            {"session_id": "unknown-999", "transcript_path": "/tmp/t.jsonl"},
        )
        assert_eq("no output for unknown session", "", output)

        # 2c. Injects context for known child.
        print("[bootstrap] context injection")
        output = _run_hook(
            "session_start_bootstrap.py",
            {"session_id": "child-1", "transcript_path": "/tmp/transcript.jsonl"},
        )
        assert_contains("outputs topic", "test topic", output)
        assert_contains("outputs reference file", "/tmp/ref.md", output)
        assert_contains("outputs context summary", "Context from main session", output)
        assert_contains("outputs result patterns", "docs/*.md", output)
        assert_contains("outputs skill invocation", "co-think-domain", output)

        # 2d. Writes back metadata and activates.
        print("[bootstrap] metadata writeback")
        tree = _read_tree()
        assert_eq("status changed to active", "active", tree["children"][0]["status"])
        assert_eq("id written", "child-1", tree["children"][0]["id"])
        assert_eq("transcriptPath written", "/tmp/transcript.jsonl", tree["children"][0]["transcriptPath"])
        assert_eq("pid is a number", True, isinstance(tree["children"][0]["pid"], int))

        # ============================================================
        print("\n=== 3. post_tool_result_collector.py ===\n")

        # 3a. Exits silently for non-Write tools.
        print("[result-collector] ignores non-Write tools")
        _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Read", "tool_input": {"file_path": "docs/foo.md"}},
        )
        tree = _read_tree()
        assert_eq("no files registered for Read tool", 0, len(tree["children"][0]["resultFiles"]))

        # 3b. Registers matching file for Write tool.
        print("[result-collector] registers matching Write")
        _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Write", "tool_input": {"file_path": "docs/result.md"}},
        )
        tree = _read_tree()
        assert_eq("result file registered", "docs/result.md", tree["children"][0]["resultFiles"][0])

        # 3c. Does not duplicate existing file.
        print("[result-collector] no duplicates")
        _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Write", "tool_input": {"file_path": "docs/result.md"}},
        )
        tree = _read_tree()
        assert_eq("no duplicate registration", 1, len(tree["children"][0]["resultFiles"]))

        # 3d. Ignores non-matching file.
        print("[result-collector] ignores non-matching path")
        _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Write", "tool_input": {"file_path": "src/code.ts"}},
        )
        tree = _read_tree()
        assert_eq("non-matching file not registered", 1, len(tree["children"][0]["resultFiles"]))

        # 3e. Registers second matching pattern.
        print("[result-collector] second pattern match")
        _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Edit", "tool_input": {"file_path": "A4/test/foo.requirement.md"}},
        )
        tree = _read_tree()
        assert_eq("second pattern match registered", 2, len(tree["children"][0]["resultFiles"]))

        # 3f. Guard on SESSION_TREE.
        print("[result-collector] guard on SESSION_TREE")
        output = _run_hook(
            "post_tool_result_collector.py",
            {"session_id": "child-1", "tool_name": "Write", "tool_input": {"file_path": "docs/x.md"}},
            env_override={"SESSION_TREE": ""},
        )
        assert_eq("no output when SESSION_TREE unset", "", output)

        # ============================================================
        print("\n=== 4. session_end_collector.py ===\n")

        # 4a. Updates status to terminated.
        print("[session-end] terminates child")
        _run_hook("session_end_collector.py", {"session_id": "child-1"})
        tree = _read_tree()
        assert_eq("status is terminated", "terminated", tree["children"][0]["status"])

        # 4b. Guard on SESSION_TREE.
        print("[session-end] guard on SESSION_TREE")
        output = _run_hook(
            "session_end_collector.py",
            {"session_id": "child-1"},
            env_override={"SESSION_TREE": ""},
        )
        assert_eq("no output when SESSION_TREE unset", "", output)

        # 4c. Ignores unknown session.
        print("[session-end] unknown session")
        output = _run_hook("session_end_collector.py", {"session_id": "unknown-999"})
        assert_eq("no error for unknown session", "", output)

        # ============================================================
        print("\n=== 5. session_monitor.py ===\n")

        # Remove any leftover snapshot.
        last_file = session_tree.with_suffix(".last")
        last_file.unlink(missing_ok=True)

        # 5a. Detects terminated session.
        print("[monitor] detects termination")
        output = _run_hook(
            "session_monitor.py",
            {"session_id": "main-1", "file_path": str(session_tree)},
        )
        assert_contains("reports terminated", "terminated", output)
        assert_contains("includes topic", "test topic", output)

        # 5b. No output on second run (no changes).
        print("[monitor] no output when no changes")
        output = _run_hook(
            "session_monitor.py",
            {"session_id": "main-1", "file_path": str(session_tree)},
        )
        assert_eq("no output on repeat", "", output)

        # 5c. Guard on wrong file_path.
        print("[monitor] ignores wrong file_path")
        output = _run_hook(
            "session_monitor.py",
            {"session_id": "main-1", "file_path": "/tmp/other.json"},
        )
        assert_eq("no output for wrong path", "", output)

        # 5d. Handshake timeout detection.
        print("[monitor] handshake timeout")
        last_file.unlink(missing_ok=True)

        def add_timeout_child(tree: dict) -> None:
            tree["children"].append({
                "id": "child-timeout",
                "topic": "stale child",
                "status": "pending",
                "createdAt": "2020-01-01T00:00:00Z",
                "pid": None,
                "skill": None,
                "transcriptPath": None,
                "resultPatterns": [],
                "resultFiles": [],
                "referenceFiles": [],
                "contextSummary": None,
            })

        st_write(add_timeout_child)
        output = _run_hook(
            "session_monitor.py",
            {"session_id": "main-1", "file_path": str(session_tree)},
        )
        assert_contains("reports failed_to_start", "failed to start", output)
        tree = _read_tree()
        timeout_child = next(c for c in tree["children"] if c["id"] == "child-timeout")
        assert_eq("status updated to failed_to_start", "failed_to_start", timeout_child["status"])

        # 5e. Crash detection (use a known-dead PID).
        print("[monitor] crash detection")
        last_file.unlink(missing_ok=True)

        def add_crash_child(tree: dict) -> None:
            tree["children"].append({
                "id": "child-crash",
                "topic": "crashed child",
                "status": "active",
                "createdAt": "2026-03-29T00:00:00Z",
                "pid": 99999,
                "skill": None,
                "transcriptPath": None,
                "resultPatterns": [],
                "resultFiles": [],
                "referenceFiles": [],
                "contextSummary": None,
            })

        st_write(add_crash_child)
        output = _run_hook(
            "session_monitor.py",
            {"session_id": "main-1", "file_path": str(session_tree)},
        )
        assert_contains("reports crashed", "crashed", output)
        tree = _read_tree()
        crash_child = next(c for c in tree["children"] if c["id"] == "child-crash")
        assert_eq("status updated to crashed", "crashed", crash_child["status"])

        # ============================================================
        print("\n=== 6. iterm2_launcher.py ===\n")

        # 6a. Missing required args.
        print("[iterm2_launcher.py] missing args")
        result = subprocess.run(
            ["uv", "run", str(SCRIPT_DIR / "lib" / "iterm2_launcher.py")],
            capture_output=True,
            text=True,
        )
        assert_contains("requires args", "required", result.stderr)

    # ============================================================
    # Summary
    print()
    print("=========================================")
    print(f"Results: {_pass} passed, {_fail} failed, {_total} total")
    print("=========================================")

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
