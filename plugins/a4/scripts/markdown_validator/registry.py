"""Check registry for the unified ``validate.py`` entrypoint.

Each ``Check`` adapts a category-specific validator module to a uniform
``Issue`` shape so the CLI can run any subset by name (``--only`` /
``--skip``) and emit a single normalized report. New categories are
added by registering one more entry in ``CHECKS``.

Two scope helpers:

  - **workspace** — scan the whole ``a4/`` workspace. Always available.
  - **file** — scan a single file's neighborhood (frontmatter: just the
    file; status: the connected component reached via ``supersedes:``).
    A check that does not support file mode skips silently when files
    are supplied.

The CLI dedupes ``Issue`` tuples that file-scope checks may emit when
multiple files share a connected component (e.g. two adjacent specs in
a supersedes chain).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Issue:
    """Normalized output across all checks.

    ``severity`` is reserved for future use (warning / error split); all
    current checks emit ``error``. ``field`` is populated by frontmatter
    violations and ``None`` for status mismatches.
    """

    category: str
    path: str
    rule: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class Check:
    name: str
    description: str
    supports_file_scope: bool
    run_workspace: Callable[[Path], list[Issue]]
    run_file: Callable[[Path, Path], list[Issue]]


def _frontmatter_workspace(a4_dir: Path) -> list[Issue]:
    from . import frontmatter as vfm

    violations, _ = vfm.run(a4_dir, None)
    return [_from_violation(v) for v in violations]


def _frontmatter_file(a4_dir: Path, file: Path) -> list[Issue]:
    from . import frontmatter as vfm

    violations, _ = vfm.run(a4_dir, file)
    return [_from_violation(v) for v in violations]


def _from_violation(v) -> Issue:
    return Issue(
        category="frontmatter",
        path=v.path,
        rule=v.rule,
        message=v.message,
        field=v.field,
    )


def _status_workspace(a4_dir: Path) -> list[Issue]:
    from . import status_consistency as vsc

    return [_from_mismatch(m) for m in vsc.run(a4_dir, None)]


def _status_file(a4_dir: Path, file: Path) -> list[Issue]:
    from . import status_consistency as vsc

    rel = str(file.relative_to(a4_dir))
    return [_from_mismatch(m) for m in vsc.run(a4_dir, rel)]


def _from_mismatch(m) -> Issue:
    return Issue(
        category="status",
        path=m.path,
        rule=m.rule,
        message=m.message,
    )


def _transitions_workspace(a4_dir: Path) -> list[Issue]:
    from . import transitions as vtr

    return [_from_transition(v) for v in vtr.run_workspace(a4_dir)]


def _transitions_file(a4_dir: Path, file: Path) -> list[Issue]:
    from . import transitions as vtr

    return [_from_transition(v) for v in vtr.run_file(a4_dir, file)]


def _from_transition(v) -> Issue:
    return Issue(
        category="transitions",
        path=v.path,
        rule=v.rule,
        message=v.message,
        field=v.field,
    )


def _umbrella_workspace(a4_dir: Path) -> list[Issue]:
    from . import umbrella_consistency as vuc

    return [_from_umbrella(m) for m in vuc.run(a4_dir, None)]


def _umbrella_file(a4_dir: Path, file: Path) -> list[Issue]:
    from . import umbrella_consistency as vuc

    return [_from_umbrella(m) for m in vuc.run(a4_dir, file)]


def _from_umbrella(m) -> Issue:
    return Issue(
        category="umbrella",
        path=m.path,
        rule=m.rule,
        message=m.message,
        field=m.field,
        severity=m.severity,
    )


CHECKS: dict[str, Check] = {
    "frontmatter": Check(
        name="frontmatter",
        description=(
            "YAML schema (required fields, enums, types), path-reference "
            "format, wiki `type:` matches filename, id uniqueness."
        ),
        supports_file_scope=True,
        run_workspace=_frontmatter_workspace,
        run_file=_frontmatter_file,
    ),
    "status": Check(
        name="status",
        description=(
            "Cross-file status consistency — `supersedes` ↔ status, "
            "`promoted` ↔ status, UC discard cascades to task / review."
        ),
        supports_file_scope=True,
        run_workspace=_status_workspace,
        run_file=_status_file,
    ),
    "transitions": Check(
        name="transitions",
        description=(
            "Status transition legality — diff working tree against HEAD "
            "via git and reject `status:` jumps not allowed by the "
            "family transition table. Safety net for hand edits the "
            "cascade hook silently skipped (illegal-jump branch)."
        ),
        supports_file_scope=True,
        run_workspace=_transitions_workspace,
        run_file=_transitions_file,
    ),
    "umbrella": Check(
        name="umbrella",
        description=(
            "Umbrella `## Children` body list ↔ reverse-`parent:` "
            "consistency. Catches children present in the body but not "
            "via `parent:`, and children via `parent:` not listed in "
            "the body. Workspace-only (relationship is cross-file)."
        ),
        supports_file_scope=False,
        run_workspace=_umbrella_workspace,
        run_file=_umbrella_file,
    ),
}
