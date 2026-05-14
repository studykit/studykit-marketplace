"""Tests for provider-specific workflow relationship context renderers."""

from __future__ import annotations

import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workflow_relationship_renderers import render_github_relationship_summary  # noqa: E402


def test_renders_full_normalized_github_projection() -> None:
    relationships = {
        "schema_version": 1,
        "parent": {"number": 28},
        "children": [{"number": 41}, {"number": 42}],
        "dependencies": {
            "blocked_by": [{"number": 33}],
            "blocking": [{"number": 45}],
        },
        "related": [{"number": 50}],
    }

    assert render_github_relationship_summary(relationships) == (
        "parent #28; children #41,#42; blocked_by #33; blocking #45; related #50"
    )


def test_omits_groups_with_no_numbers() -> None:
    relationships = {
        "parent": {"number": 28},
        "children": [],
        "dependencies": {"blocked_by": [], "blocking": []},
        "related": None,
    }

    assert render_github_relationship_summary(relationships) == "parent #28"


def test_empty_relationships_produce_no_suffix() -> None:
    assert render_github_relationship_summary({}) == ""


def test_non_mapping_input_produces_no_suffix() -> None:
    assert render_github_relationship_summary(None) == ""  # type: ignore[arg-type]


def test_missing_dependencies_block_is_safe() -> None:
    relationships = {"parent": {"number": 28}}

    assert render_github_relationship_summary(relationships) == "parent #28"


def test_rejects_pending_authoring_aliases() -> None:
    """Aliases like `blocked`, `blocks`, `blockedBy`, `depends_on` must be ignored at render time."""

    relationships = {
        "parent": {"number": 28},
        "blocked": [{"number": 100}],
        "blocks": [{"number": 101}],
        "blockedBy": [{"number": 102}],
        "depends_on": [{"number": 103}],
    }

    assert render_github_relationship_summary(relationships) == "parent #28"


def test_dependencies_only_reads_normalized_keys() -> None:
    """Inside `dependencies`, only `blocked_by` and `blocking` are read."""

    relationships = {
        "dependencies": {
            "blocked_by": [{"number": 33}],
            "blocked": [{"number": 200}],
            "blocks": [{"number": 201}],
            "depends_on": [{"number": 202}],
        },
    }

    assert render_github_relationship_summary(relationships) == "blocked_by #33"


def test_accepts_issue_field_in_addition_to_number() -> None:
    relationships = {"parent": {"issue": 28}}

    assert render_github_relationship_summary(relationships) == "parent #28"


def test_accepts_bare_numbers_and_strings() -> None:
    relationships = {
        "children": [41, "42", "#43"],
    }

    assert render_github_relationship_summary(relationships) == "children #41,#42,#43"


def test_deduplicates_repeated_numbers_within_group() -> None:
    relationships = {"children": [{"number": 41}, 41, "#41"]}

    assert render_github_relationship_summary(relationships) == "children #41"


def test_truncates_long_groups_with_overflow_marker() -> None:
    relationships = {
        "children": [{"number": n} for n in range(1, 9)],
    }

    assert render_github_relationship_summary(relationships) == "children #1,#2,#3,#4,#5,+3"


def test_handles_connection_nodes_shape() -> None:
    relationships = {
        "children": {"nodes": [{"number": 41}, {"number": 42}]},
    }

    assert render_github_relationship_summary(relationships) == "children #41,#42"


def test_unparseable_values_are_skipped() -> None:
    relationships = {
        "parent": {"number": 28},
        "children": ["not-a-number", None, {"number": "abc"}, {"number": 41}],
    }

    assert render_github_relationship_summary(relationships) == "parent #28; children #41"
