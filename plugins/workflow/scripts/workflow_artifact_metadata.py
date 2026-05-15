#!/usr/bin/env python3
"""Workflow artifact metadata inference for local projection writes.

The ``pre_write`` hook runs before any Markdown edit and asks: is this file a
workflow artifact, and if so which type/role/provider? The answer steers the
authoring guard preflight. This module owns the small parser that pulls those
three scalars out of the file's YAML frontmatter (or the first non-header
section when no frontmatter is present).

Keeping the parser separate from the hook dispatcher keeps the dispatcher's
job clear — orchestrating runtimes and entrypoints — and gives the metadata
contract a single home that ``authoring_resolver`` callers can grow without
touching unrelated hook logic.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import frontmatter as frontmatter_lib

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from authoring_resolver import ALL_TYPES, DUAL_TYPES  # noqa: E402
from workflow_edit_target import EditTarget  # noqa: E402

_METADATA_KEYS = {"type", "role", "provider"}
_HEADER_SCAN_LIMIT = 80
_FRONTMATTER_HANDLER = frontmatter_lib.YAMLHandler()


@dataclass(frozen=True)
class ArtifactMetadata:
    """Workflow artifact metadata inferred from local projection content."""

    artifact_type: str
    role: str | None = None
    provider: str | None = None


def infer_artifact_metadata(target: EditTarget) -> ArtifactMetadata | None:
    """Return artifact metadata for ``target`` or ``None`` when not a workflow artifact."""

    content = target.content
    if content is None:
        try:
            content = target.path.read_text(encoding="utf-8")
        except OSError:
            content = ""

    values = extract_metadata_values(content)
    raw_type = values.get("type")
    if raw_type is None:
        artifact_type = _artifact_type_from_labels(content)
        if artifact_type is None:
            return None
    else:
        artifact_type = _normalize_artifact_type(raw_type)
        if artifact_type not in ALL_TYPES:
            return None

    raw_role = values.get("role")
    if artifact_type in DUAL_TYPES and not raw_role:
        return None

    return ArtifactMetadata(
        artifact_type=artifact_type,
        role=_normalize_token(raw_role) if raw_role else None,
        provider=_normalize_token(values.get("provider")) if values.get("provider") else None,
    )


def extract_metadata_values(content: str) -> dict[str, str]:
    """Extract type/role/provider scalars from Markdown frontmatter or leading content."""

    frontmatter_values = _extract_frontmatter_metadata_values(content)
    if frontmatter_values is not None:
        return frontmatter_values
    return _extract_line_metadata_values(_collect_metadata_lines(content))


def _load_frontmatter_mapping(content: str) -> dict[object, object] | None:
    if not _FRONTMATTER_HANDLER.detect(content):
        return None
    try:
        frontmatter_text, _body = _FRONTMATTER_HANDLER.split(content)
        data = _FRONTMATTER_HANDLER.load(frontmatter_text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _artifact_type_from_labels(content: str) -> str | None:
    data = _load_frontmatter_mapping(content)
    if not data:
        return None
    labels = data.get("labels")
    if not isinstance(labels, list):
        return None

    candidates: list[str] = []
    for item in labels:
        if isinstance(item, dict):
            raw = item.get("name") or item.get("label")
        else:
            raw = item
        if raw is None:
            continue
        artifact_type = _normalize_artifact_type(str(raw))
        if artifact_type in ALL_TYPES and artifact_type not in candidates:
            candidates.append(artifact_type)
    return candidates[0] if len(candidates) == 1 else None


def _normalize_artifact_type(value: str) -> str:
    artifact_type = _normalize_token(value)
    return "usecase" if artifact_type == "use-case" else artifact_type


def _extract_frontmatter_metadata_values(content: str) -> dict[str, str] | None:
    data = _load_frontmatter_mapping(content)
    if data is None:
        return None

    values: dict[str, str] = {}
    for raw_key, raw_value in data.items():
        key = str(raw_key).strip().lower().replace("-", "_")
        if key not in _METADATA_KEYS or isinstance(raw_value, (dict, list)):
            continue
        value = str(raw_value).strip()
        if value:
            values[key] = value
    return values


def _extract_line_metadata_values(metadata_lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in metadata_lines:
        if ":" not in line:
            continue
        raw_key, raw_value = line.split(":", 1)
        key = raw_key.strip().lower().replace("-", "_")
        if key not in _METADATA_KEYS:
            continue
        value = raw_value.strip().strip("\"'")
        if value:
            values[key] = value
    return values


def _collect_metadata_lines(content: str) -> list[str]:
    lines = content.splitlines()
    collected = []
    for line in lines[:_HEADER_SCAN_LIMIT]:
        if line.strip().startswith("#"):
            break
        collected.append(line)
    return collected


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("_", "-")
