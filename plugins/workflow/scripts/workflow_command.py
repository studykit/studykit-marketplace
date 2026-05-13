#!/usr/bin/env python3
"""Shared command execution helpers for workflow provider wrappers."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandRequest:
    """A normalized subprocess request."""

    args: tuple[str, ...]
    cwd: Path | None = None
    input_text: str | None = None
    env: Mapping[str, str] | None = None

    def to_json(self) -> dict[str, object]:
        result: dict[str, object] = {"args": list(self.args)}
        if self.cwd is not None:
            result["cwd"] = str(self.cwd)
        if self.input_text is not None:
            result["has_input"] = True
        if self.env:
            result["env_keys"] = sorted(self.env)
        return result


@dataclass(frozen=True)
class CommandResult:
    """A normalized subprocess result."""

    request: CommandRequest
    returncode: int
    stdout: str = ""
    stderr: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "request": self.request.to_json(),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


CommandRunner = Callable[[CommandRequest], CommandResult]


class WorkflowCommandError(RuntimeError):
    """Raised when an external command cannot be executed successfully."""

    def __init__(self, message: str, *, request: CommandRequest, result: CommandResult | None = None):
        super().__init__(message)
        self.request = request
        self.result = result


class MissingCommandError(WorkflowCommandError):
    """Raised when the requested executable is missing."""


def run_command(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    env: Mapping[str, str] | None = None,
    runner: CommandRunner | None = None,
    check: bool = True,
) -> CommandResult:
    """Run a command through the configured runner.

    Tests pass a fake runner. Runtime callers use ``subprocess_runner``.
    """

    request = CommandRequest(
        args=tuple(str(arg) for arg in args),
        cwd=cwd.expanduser().resolve(strict=False) if cwd is not None else None,
        input_text=input_text,
        env=env,
    )
    result = (runner or subprocess_runner)(request)
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        raise WorkflowCommandError(
            f"command failed with exit code {result.returncode}: {request.args[0]}{detail}",
            request=request,
            result=result,
        )
    return result


def subprocess_runner(request: CommandRequest) -> CommandResult:
    """Execute a normalized command request with ``subprocess.run``."""

    merged_env = None
    if request.env:
        merged_env = dict(os.environ)
        merged_env.update(request.env)

    try:
        proc = subprocess.run(
            list(request.args),
            cwd=str(request.cwd) if request.cwd is not None else None,
            input=request.input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=merged_env,
        )
    except FileNotFoundError as exc:
        raise MissingCommandError(
            f"command not found: {request.args[0]}",
            request=request,
        ) from exc
    except OSError as exc:
        raise WorkflowCommandError(
            f"command could not be executed: {request.args[0]}: {exc}",
            request=request,
        ) from exc

    return CommandResult(
        request=request,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )
