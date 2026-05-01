"""Test harness for the a4 plugin's validator scripts.

Scripts under ``plugins/a4/scripts/`` import each other as flat modules
(``from common import ...``) rather than as a package. The unified CLI
``validate.py`` injects its parent directory into ``sys.path`` at run
time; the test harness mirrors that injection so tests can import
``markdown_validator``, ``common``, ``markdown``, etc., directly.

A workspace-builder fixture (``a4_workspace``) writes minimal but valid
frontmatter into a ``tmp_path / "a4" / <folder> / <file>.md`` tree so
each test can shape only the fields it cares about.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PLUGIN_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _write_md(
    path: Path,
    fm: dict[str, Any],
    body: str,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm_text = yaml.safe_dump(fm, sort_keys=False).strip()
    path.write_text(f"---\n{fm_text}\n---\n\n{body}\n", encoding="utf-8")
    return path


_DEFAULT_BODY: dict[str, str] = {
    "task": (
        "## Description\nx\n\n"
        "## Files\n- none\n\n"
        "## Unit Test Strategy\nnone\n\n"
        "## Acceptance Criteria\n- x\n"
    ),
    "bug": (
        "## Description\nx\n\n"
        "## Files\n- none\n\n"
        "## Unit Test Strategy\nnone\n\n"
        "## Acceptance Criteria\n- x\n"
    ),
    "spike": (
        "## Description\nx\n\n"
        "## Hypothesis\nx\n\n"
        "## Files\n- none\n"
    ),
    "research": (
        "## Description\nx\n\n"
        "## Question\nx\n\n"
        "## Findings\nnone\n"
    ),
    "usecase": (
        "## Description\nx\n\n"
        "## Acceptance Criteria\n- x\n"
    ),
    "spec": (
        "## Description\nx\n\n"
        "## Decision\nx\n"
    ),
    "umbrella": (
        "## Description\nx\n\n"
        "## Children\n- (none yet)\n\n"
        "## Log\n- ok\n"
    ),
}


class A4Workspace:
    """Helper bound to a single ``a4/`` directory under tmp_path.

    Each call writes one file. The default body shape is enough to keep
    the body-shape rules quiet; tests that need a specific body pass
    ``body=`` explicitly.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        for folder in (
            "task",
            "bug",
            "spike",
            "research",
            "umbrella",
            "usecase",
            "spec",
        ):
            (root / folder).mkdir(parents=True, exist_ok=True)

    def write(
        self,
        folder: str,
        id_: int,
        slug: str,
        *,
        title: str = "Title",
        status: str = "open",
        body: str | None = None,
        type_override: str | None = None,
        **extra_fm: Any,
    ) -> Path:
        ftype = type_override or folder
        fm: dict[str, Any] = {
            "type": ftype,
            "id": id_,
            "title": title,
            "status": status,
            "created": "2026-05-01",
            "updated": "2026-05-01",
        }
        for k, v in extra_fm.items():
            fm[k] = v
        if folder == "research" and "mode" not in fm:
            fm["mode"] = "single"
        path = self.root / folder / f"{id_}-{slug}.md"
        return _write_md(path, fm, body if body is not None else _DEFAULT_BODY[ftype])


@pytest.fixture
def a4_workspace(tmp_path: Path) -> A4Workspace:
    return A4Workspace(tmp_path / "a4")
