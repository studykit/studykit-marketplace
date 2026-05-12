"""Tests for workflow authoring write guard."""

from __future__ import annotations

import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from authoring_guard import build_result  # noqa: E402
from authoring_ledger import missing_reads, record_reads  # noqa: E402
from authoring_resolver import resolve_authoring  # noqa: E402


def test_guard_result_is_ok_when_all_resolved_files_were_recorded(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state_dir = tmp_path / "state"
    resolution = resolve_authoring("review", role="issue", provider="github")

    record_reads(resolution.files, project=project, session_id="s1", state_dir=state_dir)
    missing = missing_reads(resolution.files, project=project, session_id="s1", state_dir=state_dir)

    assert build_result(resolution.files, missing)["ok"] is True


def test_guard_result_lists_missing_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state_dir = tmp_path / "state"
    resolution = resolve_authoring("review", role="issue", provider="github")

    record_reads(resolution.files[:1], project=project, session_id="s1", state_dir=state_dir)
    missing = missing_reads(resolution.files, project=project, session_id="s1", state_dir=state_dir)
    result = build_result(resolution.files, missing)

    assert result["ok"] is False
    assert result["missing_authoring_files"] == [str(path) for path in resolution.files[1:]]
