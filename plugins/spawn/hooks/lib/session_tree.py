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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

_override: str | None = None


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------

@dataclass
class MainSession:
    id: str
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MainSession:
        return cls(id=d["id"], name=d.get("name"))


@dataclass
class ChildEntry:
    id: str
    topic: str
    status: str = "pending"
    # Status values: pending | active | terminated | crashed | failed_to_start | resumed
    created_at: str = ""
    pid: int | None = None
    persona: str | None = None
    transcript_path: str | None = None
    result_files: list[str] = field(default_factory=list)
    result_updated_at: str | None = None
    reference_files: list[str] = field(default_factory=list)
    bootstrap_prompt_snippet: str | None = None
    resume_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "status": self.status,
            "createdAt": self.created_at,
            "pid": self.pid,
            "persona": self.persona,
            "transcriptPath": self.transcript_path,
            "resultFiles": self.result_files,
            "resultUpdatedAt": self.result_updated_at,
            "referenceFiles": self.reference_files,
            "bootstrapPromptSnippet": self.bootstrap_prompt_snippet,
            "resumeCount": self.resume_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ChildEntry:
        return cls(
            id=d.get("id", ""),
            topic=d.get("topic", ""),
            status=d.get("status", "pending"),
            created_at=d.get("createdAt", ""),
            pid=d.get("pid"),
            persona=d.get("persona"),
            transcript_path=d.get("transcriptPath"),
            result_files=d.get("resultFiles") or [],
            result_updated_at=d.get("resultUpdatedAt"),
            reference_files=d.get("referenceFiles") or [],
            bootstrap_prompt_snippet=d.get("bootstrapPromptSnippet"),
            resume_count=d.get("resumeCount", 0),
        )


@dataclass
class SessionTree:
    main_session: MainSession | None = None
    children: list[ChildEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mainSession": self.main_session.to_dict() if self.main_session else None,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SessionTree:
        ms = d.get("mainSession")
        return cls(
            main_session=MainSession.from_dict(ms) if ms else None,
            children=[ChildEntry.from_dict(c) for c in d.get("children") or []],
        )

    def find_child(self, child_id: str) -> ChildEntry | None:
        if not child_id:
            return None
        for child in self.children:
            if child.id == child_id:
                return child
        return None


# ------------------------------------------------------------------
# Path management
# ------------------------------------------------------------------

def set_session_tree_path(path: str) -> None:
    """Override for SESSION_TREE path. Takes precedence over the env var."""
    global _override
    _override = path


def _tree_path() -> Path | None:
    p = _override or os.environ.get("SESSION_TREE", "")
    return Path(p) if p else None


def _lock_path() -> Path | None:
    p = _tree_path()
    return p.with_suffix(".lock") if p else None


# ------------------------------------------------------------------
# Read / write / find
# ------------------------------------------------------------------

def st_read() -> SessionTree:
    """Read session-tree.json, returning a SessionTree.

    Returns an empty SessionTree if the file doesn't exist or
    SESSION_TREE is unset.
    """
    p = _tree_path()
    if not p or not p.exists():
        return SessionTree()

    lock = _lock_path()
    assert lock is not None
    lock.touch(exist_ok=True)
    with open(lock) as lf:
        fcntl.flock(lf, fcntl.LOCK_SH)
        try:
            return SessionTree.from_dict(json.loads(p.read_text()))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def st_write(transform: Callable[[SessionTree], None]) -> None:
    """Atomically apply a transformation to session-tree.json.

    *transform* is a callable that receives the current SessionTree and
    should mutate it in place (return value is ignored).
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
                tree = SessionTree.from_dict(json.loads(p.read_text()))
            else:
                tree = SessionTree()
            transform(tree)
            p.write_text(json.dumps(tree.to_dict(), ensure_ascii=False, indent=2) + "\n")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def st_find_child(child_id: str) -> ChildEntry | None:
    """Find a child entry by id. Returns the ChildEntry or None."""
    return st_read().find_child(child_id)


def read_stdin_json() -> dict[str, Any]:
    """Read and parse JSON from stdin. Returns {} on failure."""
    try:
        return json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return {}
