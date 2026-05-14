#!/usr/bin/env python3
# /// script
# dependencies = ["PyYAML"]
# ///
"""Session ledger for workflow authoring file reads.

The ledger records absolute authoring contract paths that an agent has read in
the current session. Write guards can compare resolver output against this
ledger before allowing provider or projection writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from workflow_env import workflow_project_dir_from_env, workflow_session_id_from_env
from workflow_config import CONFIG_NAME, find_workflow_config

STATE_ROOT_NAME = "workflow-plugin"
LEDGER_DIR_NAME = "authoring-ledger"


class LedgerError(ValueError):
    """Raised when ledger operation is unsafe or invalid."""


@dataclass(frozen=True)
class Ledger:
    """In-memory representation of a session authoring read ledger."""

    session_id: str
    project: Path
    path: Path
    read_authoring_files: tuple[Path, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project": str(self.project),
            "path": str(self.path),
            "read_authoring_files": [str(path) for path in self.read_authoring_files],
        }


def find_config(project: Path) -> Path | None:
    return find_workflow_config(project)


def default_session_id() -> str:
    try:
        return workflow_session_id_from_env()
    except ValueError as exc:
        raise LedgerError(str(exc)) from exc


def normalize_path(path: Path) -> Path:
    return path.expanduser().resolve()


def project_key(project: Path) -> str:
    digest = hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()
    return digest[:16]


def ledger_path(project: Path, session_id: str, state_dir: Path | None = None) -> Path:
    root = state_dir or Path(tempfile.gettempdir()) / STATE_ROOT_NAME
    safe_session = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
    return root / LEDGER_DIR_NAME / project_key(project) / f"{safe_session}.json"


def read_ledger(project: Path, session_id: str, state_dir: Path | None = None) -> Ledger:
    project = project.resolve()
    path = ledger_path(project, session_id, state_dir)
    if not path.exists():
        return Ledger(session_id=session_id, project=project, path=path, read_authoring_files=())

    data = json.loads(path.read_text(encoding="utf-8"))
    files = tuple(normalize_path(Path(value)) for value in data.get("read_authoring_files", []))
    return Ledger(session_id=session_id, project=project, path=path, read_authoring_files=files)


def write_ledger(ledger: Ledger) -> Ledger:
    ledger.path.parent.mkdir(parents=True, exist_ok=True)
    unique_files = tuple(dict.fromkeys(ledger.read_authoring_files))
    saved = Ledger(
        session_id=ledger.session_id,
        project=ledger.project,
        path=ledger.path,
        read_authoring_files=unique_files,
    )
    ledger.path.write_text(json.dumps(saved.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return saved


def record_reads(
    paths: Iterable[Path],
    *,
    project: Path,
    session_id: str,
    state_dir: Path | None = None,
    require_config: bool = False,
) -> Ledger:
    project = project.resolve()
    if require_config and find_config(project) is None:
        raise LedgerError(f"{CONFIG_NAME} was not found for {project}")

    current = read_ledger(project, session_id, state_dir)
    additions = tuple(normalize_path(path) for path in paths)
    return write_ledger(
        Ledger(
            session_id=session_id,
            project=project,
            path=current.path,
            read_authoring_files=current.read_authoring_files + additions,
        )
    )


def missing_reads(
    required_paths: Iterable[Path],
    *,
    project: Path,
    session_id: str,
    state_dir: Path | None = None,
) -> tuple[Path, ...]:
    ledger = read_ledger(project.resolve(), session_id, state_dir)
    read_set = {normalize_path(path) for path in ledger.read_authoring_files}
    missing = [normalize_path(path) for path in required_paths if normalize_path(path) not in read_set]
    return tuple(missing)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=workflow_project_dir_from_env(), help="project path")
    parser.add_argument("--session", help="session id; defaults to WORKFLOW_SESSION_ID")
    parser.add_argument("--state-dir", type=Path, help="override ledger state root")
    parser.add_argument("--json", action="store_true", help="emit JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="record authoring files as read")
    record.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit JSON")
    record.add_argument("paths", nargs="+", type=Path, help="authoring file paths that were read")
    record.add_argument("--require-config", action="store_true", help="fail when .workflow/config.yml is absent")

    check = subparsers.add_parser("check", help="check that required authoring files were read")
    check.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit JSON")
    check.add_argument("paths", nargs="+", type=Path, help="required authoring file paths")

    show = subparsers.add_parser("show", help="show current ledger")
    show.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        session_id = args.session or default_session_id()
        state_dir = args.state_dir.resolve() if args.state_dir else None

        if args.command == "record":
            ledger = record_reads(
                args.paths,
                project=args.project,
                session_id=session_id,
                state_dir=state_dir,
                require_config=args.require_config,
            )
            if args.json:
                print(json.dumps(ledger.to_json(), indent=2, sort_keys=False))
            else:
                print(ledger.path)
            return 0

        if args.command == "check":
            missing = missing_reads(
                args.paths,
                project=args.project,
                session_id=session_id,
                state_dir=state_dir,
            )
            if args.json:
                print(json.dumps({"ok": not missing, "missing": [str(path) for path in missing]}, indent=2))
            elif missing:
                for path in missing:
                    print(path)
            return 3 if missing else 0

        if args.command == "show":
            ledger = read_ledger(args.project.resolve(), session_id, state_dir)
            print(json.dumps(ledger.to_json(), indent=2, sort_keys=False))
            return 0

    except LedgerError as exc:
        print(f"authoring ledger error: {exc}", file=sys.stderr)
        return 2

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
