"""Workflow-mode state manager for the a4 plugin.

Single entry point for hooks, skills, and agents to read or transition the
session-scoped workflow mode (`conversational` | `autonomous`).

Per-session state lives at `<project-root>/a4/.workflow-state/<session-id>.json`
so concurrent Claude Code sessions in the same workspace do not race.

See `plugins/a4/references/workflow-mode.md` for the full spec.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, NoReturn

Mode = Literal["conversational", "autonomous"]
VALID_MODES: tuple[Mode, ...] = ("conversational", "autonomous")

STATE_DIRNAME = ".workflow-state"
SWEEP_AGE_DAYS = 1


# --- session resolution ----------------------------------------------------


def resolve_session_id(explicit: str | None) -> str:
    """Pick a session id with the documented fallback order.

    1. Explicit `--session` argument.
    2. `$CLAUDE_SESSION_ID` environment variable.
    3. SHA256(`$CLAUDE_TRANSCRIPT_PATH`) truncated to 16 hex chars.
    4. PID-anchored last-resort fallback.
    """
    if explicit:
        return explicit
    env_id = os.environ.get("CLAUDE_SESSION_ID")
    if env_id:
        return env_id
    transcript = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if transcript:
        return hashlib.sha256(transcript.encode("utf-8")).hexdigest()[:16]
    return f"pid-{os.getpid()}-{int(time.time())}"


# --- state location --------------------------------------------------------


def project_root() -> Path:
    import subprocess

    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        die("not inside a git worktree", code=1)
    return Path(out.stdout.strip())


def state_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "a4" / STATE_DIRNAME


def state_path(session_id: str, root: Path | None = None) -> Path:
    return state_dir(root) / f"{session_id}.json"


# --- model -----------------------------------------------------------------


@dataclass
class State:
    session_id: str
    current_mode: Mode
    entered_at: str
    entered_by: str
    trigger: str
    history: list[dict] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "session_id": self.session_id,
                "current_mode": self.current_mode,
                "entered_at": self.entered_at,
                "entered_by": self.entered_by,
                "trigger": self.trigger,
                "history": self.history,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> State:
        data = json.loads(text)
        return cls(
            session_id=data["session_id"],
            current_mode=data["current_mode"],
            entered_at=data["entered_at"],
            entered_by=data["entered_by"],
            trigger=data["trigger"],
            history=list(data.get("history", [])),
        )


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state(session_id: str) -> State | None:
    path = state_path(session_id)
    if not path.exists():
        return None
    return State.from_json(path.read_text(encoding="utf-8"))


def save_state(state: State) -> None:
    path = state_path(state.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(state.to_json(), encoding="utf-8")
    tmp.replace(path)


# --- commands --------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    session_id = resolve_session_id(args.session)
    if load_state(session_id) is not None:
        die(f"state already exists for session {session_id}", code=2)
    mode: Mode = args.mode or "conversational"
    require_valid_mode(mode)
    state = State(
        session_id=session_id,
        current_mode=mode,
        entered_at=now(),
        entered_by=args.by or "session-start",
        trigger=args.trigger or "session-start init",
        history=[],
    )
    save_state(state)
    print(state.to_json())
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    session_id = resolve_session_id(args.session)
    state = load_state(session_id)
    if state is None:
        die(f"no state for session {session_id}", code=2)
    print(state.to_json())
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    session_id = resolve_session_id(args.session)
    require_valid_mode(args.mode)
    state = load_state(session_id)
    if state is None:
        die(f"no state for session {session_id}; run init first", code=2)
    if state.current_mode == args.mode and not args.force:
        die(
            f"already in {args.mode}; pass --force to record a no-op transition",
            code=2,
        )
    state.history.append(
        {
            "mode": state.current_mode,
            "at": state.entered_at,
            "by": state.entered_by,
            "trigger": state.trigger,
        }
    )
    state.current_mode = args.mode
    state.entered_at = now()
    state.entered_by = args.by or "unspecified"
    state.trigger = args.trigger
    save_state(state)
    print(state.to_json())
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    session_id = resolve_session_id(args.session)
    state = load_state(session_id)
    if state is None:
        die(f"no state for session {session_id}", code=2)
    payload = list(state.history)
    payload.append(
        {
            "mode": state.current_mode,
            "at": state.entered_at,
            "by": state.entered_by,
            "trigger": state.trigger,
        }
    )
    print(json.dumps({"session_id": session_id, "history": payload}, indent=2))
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    session_id = resolve_session_id(args.session)
    path = state_path(session_id)
    if path.exists():
        path.unlink()
    return 0


def cmd_sweep(_: argparse.Namespace) -> int:
    sd = state_dir()
    if not sd.exists():
        return 0
    cutoff = time.time() - SWEEP_AGE_DAYS * 86400
    for f in sd.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            continue
    return 0


# --- helpers ---------------------------------------------------------------


def require_valid_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        die(f"invalid mode {mode!r}; expected one of {VALID_MODES}", code=1)


def die(msg: str, code: int) -> NoReturn:
    print(f"workflow_mode: {msg}", file=sys.stderr)
    sys.exit(code)


# --- argparse --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="workflow_mode")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize session state")
    p_init.add_argument("--session")
    p_init.add_argument("--mode", choices=VALID_MODES)
    p_init.add_argument("--by")
    p_init.add_argument("--trigger")
    p_init.set_defaults(func=cmd_init)

    p_get = sub.add_parser("get", help="print current state")
    p_get.add_argument("--session")
    p_get.set_defaults(func=cmd_get)

    p_set = sub.add_parser("set", help="transition mode")
    p_set.add_argument("mode", choices=VALID_MODES)
    p_set.add_argument("--trigger", required=True)
    p_set.add_argument("--by")
    p_set.add_argument("--session")
    p_set.add_argument("--force", action="store_true")
    p_set.set_defaults(func=cmd_set)

    p_hist = sub.add_parser("history", help="print full transition history")
    p_hist.add_argument("--session")
    p_hist.set_defaults(func=cmd_history)

    p_clean = sub.add_parser("cleanup", help="delete this session's state file")
    p_clean.add_argument("--session")
    p_clean.set_defaults(func=cmd_cleanup)

    p_sweep = sub.add_parser(
        "sweep", help=f"delete state files older than {SWEEP_AGE_DAYS} day"
    )
    p_sweep.set_defaults(func=cmd_sweep)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
