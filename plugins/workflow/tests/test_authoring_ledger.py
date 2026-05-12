"""Tests for workflow authoring read ledger."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from authoring_ledger import LedgerError, missing_reads, read_ledger, record_reads  # noqa: E402


def test_record_reads_and_missing_reads(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state_dir = tmp_path / "state"
    first = tmp_path / "authoring" / "one.md"
    second = tmp_path / "authoring" / "two.md"
    first.parent.mkdir()
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")

    ledger = record_reads([first], project=project, session_id="s1", state_dir=state_dir)

    assert ledger.path.exists()
    assert missing_reads([first, second], project=project, session_id="s1", state_dir=state_dir) == (
        second.resolve(),
    )

    record_reads([second], project=project, session_id="s1", state_dir=state_dir)
    assert missing_reads([first, second], project=project, session_id="s1", state_dir=state_dir) == ()


def test_ledgers_are_session_scoped(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state_dir = tmp_path / "state"
    authoring_file = tmp_path / "contract.md"
    authoring_file.write_text("contract", encoding="utf-8")

    record_reads([authoring_file], project=project, session_id="s1", state_dir=state_dir)

    assert read_ledger(project, "s1", state_dir).read_authoring_files == (authoring_file.resolve(),)
    assert read_ledger(project, "s2", state_dir).read_authoring_files == ()


def test_require_config_fails_when_missing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(LedgerError, match="workflow.config.yml was not found"):
        record_reads([tmp_path / "contract.md"], project=project, session_id="s1", require_config=True)
