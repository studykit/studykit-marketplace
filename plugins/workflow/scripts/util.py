#!/usr/bin/env python3
"""Small helpers for runtime hook payload adapters."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SCAN_TEXT_MAX_CHUNKS = 40
_SCAN_TEXT_MAX_DEPTH = 5
_SCAN_TEXT_CHUNK_LIMIT = 4000


def as_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def emit_json(payload: dict[str, Any], *, stdout: Any | None = None) -> None:
    """Emit a JSON payload to stdout."""

    output = stdout or sys.stdout
    json.dump(payload, output, ensure_ascii=False)
    output.write("\n")


def resolve_file_path(raw_path: str, *, base_dir: Path) -> Path:
    """Resolve a raw file path against an already selected base directory."""

    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve(strict=False)
    return (base_dir / path).resolve(strict=False)


def is_markdown_path(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".markdown"}


def is_under_any(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve(strict=False)
    return any(is_under(resolved, root) for root in roots)


def is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_payload_or_stdin(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return an explicit payload, or parse one JSON object from stdin."""

    if payload is None:
        return _read_stdin_json()
    return dict(payload)


def _read_stdin_json() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def scan_text_values(*values: Any) -> str:
    """Collect bounded string content from selected values for issue-ref scans."""

    chunks: list[str] = []

    def visit(value: Any, *, depth: int = 0) -> None:
        if len(chunks) >= _SCAN_TEXT_MAX_CHUNKS or depth > _SCAN_TEXT_MAX_DEPTH:
            return
        if isinstance(value, str):
            if value:
                chunks.append(value[:_SCAN_TEXT_CHUNK_LIMIT])
            return
        if isinstance(value, Mapping):
            for item in value.values():
                visit(item, depth=depth + 1)
            return
        if isinstance(value, (list, tuple)):
            for item in value[:_SCAN_TEXT_MAX_CHUNKS]:
                visit(item, depth=depth + 1)

    for value in values:
        visit(value)
    return "\n".join(chunks)
