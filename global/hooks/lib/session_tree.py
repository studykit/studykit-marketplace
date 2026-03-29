"""session_tree — atomic read-modify-write for session-tree.json.

Import this module from hook scripts. Requires the SESSION_TREE
environment variable to point at the manifest file.

All public functions are no-ops when SESSION_TREE is unset or empty.
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_SESSION_TREE: str = os.environ.get("SESSION_TREE", "")

_DEFAULT_TREE: dict[str, Any] = {"mainSession": None, "children": []}


def _tree_path() -> Path | None:
    if not _SESSION_TREE:
        return None
    return Path(_SESSION_TREE)


def _lock_path() -> Path | None:
    p = _tree_path()
    return p.with_suffix(".lock") if p else None


def st_read() -> dict[str, Any]:
    """Read session-tree.json, returning parsed JSON.

    Returns the default empty tree if the file doesn't exist or
    SESSION_TREE is unset.
    """
    p = _tree_path()
    if not p or not p.exists():
        return json.loads(json.dumps(_DEFAULT_TREE))

    lock = _lock_path()
    assert lock is not None
    lock.touch(exist_ok=True)
    with open(lock) as lf:
        fcntl.flock(lf, fcntl.LOCK_SH)
        try:
            return json.loads(p.read_text())
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def st_write(transform: Any) -> None:
    """Atomically apply a transformation to session-tree.json.

    *transform* is a callable that receives the current tree dict and
    should mutate it in place (return value is ignored).

    Example::

        def add_child(tree):
            tree["children"].append({"id": "abc", ...})

        st_write(add_child)
    """
    p = _tree_path()
    if not p:
        return

    lock = _lock_path()
    assert lock is not None
    p.parent.mkdir(parents=True, exist_ok=True)
    lock.touch(exist_ok=True)

    with open(lock) as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            if p.exists():
                tree = json.loads(p.read_text())
            else:
                tree = json.loads(json.dumps(_DEFAULT_TREE))
            transform(tree)
            p.write_text(json.dumps(tree, ensure_ascii=False, indent=2) + "\n")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def st_find_child(child_id: str) -> dict[str, Any] | None:
    """Find a child entry by id. Returns the dict or None."""
    if not child_id:
        return None
    tree = st_read()
    for child in tree.get("children", []):
        if child.get("id") == child_id:
            return child
    return None


def read_stdin_json() -> dict[str, Any]:
    """Read and parse JSON from stdin. Returns {} on failure."""
    try:
        return json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return {}
