"""Tests for workflow artifact metadata extraction."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_artifact_metadata import extract_metadata_values, infer_artifact_metadata  # noqa: E402
from workflow_edit_target import EditTarget  # noqa: E402


def test_extract_metadata_values_uses_yaml_frontmatter() -> None:
    values = extract_metadata_values(
        """---
type: task
role: issue
provider: github
labels:
  - workflow
---

# Body
"""
    )

    assert values == {"type": "task", "role": "issue", "provider": "github"}


def test_extract_metadata_values_keeps_non_frontmatter_fallback() -> None:
    values = extract_metadata_values(
        """type: usecase
role: knowledge

# Body
"""
    )

    assert values == {"type": "usecase", "role": "knowledge"}


def test_infer_artifact_metadata_uses_single_workflow_type_label() -> None:
    metadata = infer_artifact_metadata(
        EditTarget(
            path=Path("issue.md"),
            content="""---
schema_version: 1
title: Cached issue
state: open
labels:
  - task
  - workflow
source_updated_at: 2026-05-14T00:00:00Z
---

Issue body.
""",
        )
    )

    assert metadata is not None
    assert metadata.artifact_type == "task"
    assert metadata.role is None
    assert metadata.provider is None
