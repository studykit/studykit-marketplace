#!/usr/bin/env python3
"""Check whether workflow authoring files were read before a write.

This script combines the authoring resolver with the session read ledger. It is
intended for provider wrappers and future hooks that need a single yes/no guard
before creating or editing workflow artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from authoring_ledger import LedgerError, default_session_id, missing_reads
from authoring_resolver import ResolverError, resolve_authoring


def build_result(required: tuple[Path, ...], missing: tuple[Path, ...]) -> dict[str, Any]:
    return {
        "ok": not missing,
        "required_authoring_files": [str(path) for path in required],
        "missing_authoring_files": [str(path) for path in missing],
    }


def evaluate_authoring_guard(
    artifact_type: str,
    *,
    project: Path,
    session_id: str,
    role: str | None = None,
    provider: str | None = None,
    state_dir: Path | None = None,
    require_config: bool = False,
) -> dict[str, Any]:
    """Resolve required authoring files and compare them with the read ledger.

    This function is transport-neutral. Hook adapters and future provider
    wrappers can call it before any local, native-provider, REST, or MCP write.
    """

    resolution = resolve_authoring(
        artifact_type,
        role=role,
        provider=provider,
        project=project,
        require_config=require_config,
    )
    missing = missing_reads(
        resolution.files,
        project=project,
        session_id=session_id,
        state_dir=state_dir,
    )
    result = build_result(resolution.files, missing)
    result["artifact"] = resolution.to_json()["artifact"]
    result["config_path"] = resolution.to_json()["config_path"]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project path")
    parser.add_argument("--session", help="session id; defaults to WORKFLOW_SESSION_ID or runtime env")
    parser.add_argument("--state-dir", type=Path, help="override ledger state root")
    parser.add_argument("--type", required=True, help="workflow artifact type")
    parser.add_argument("--role", help="issue or knowledge; required for usecase/research")
    parser.add_argument("--provider", help="provider override")
    parser.add_argument("--require-config", action="store_true", help="fail when workflow.config.yml is absent")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        session_id = args.session or default_session_id()
        result = evaluate_authoring_guard(
            args.type,
            project=args.project,
            session_id=session_id,
            role=args.role,
            provider=args.provider,
            state_dir=args.state_dir.resolve() if args.state_dir else None,
            require_config=args.require_config,
        )
    except (ResolverError, LedgerError) as exc:
        print(f"authoring guard error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=False))
    elif result["missing_authoring_files"]:
        print("missing required authoring reads:")
        for path in result["missing_authoring_files"]:
            print(f"- {path}")

    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
