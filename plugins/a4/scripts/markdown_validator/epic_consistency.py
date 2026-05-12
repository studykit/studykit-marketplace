"""Epic consistency + drift validator (library).

`epic-authoring.md` declares the validator's reverse-`parent:`
resolver as authoritative for membership; the epic body's
`## Children` section is the human-readable mirror. Drift between the
two surfaces — and the soft signal that an epic's children are all
terminal while the epic itself is still `open` — is silent without
this check.

Three signals are surfaced:

  - ``epic-child-not-listed`` *(error)* — a file's frontmatter
    ``parent:`` resolves to this epic but the epic body's
    ``## Children`` section does not list it. The doc names this as a
    common mistake ("Children listed only via reverse-`parent:`").
  - ``epic-stale-listing`` *(error)* — the epic body's
    ``## Children`` section lists a child (without an annotation
    suffix) but no file's frontmatter ``parent:`` resolves to this
    epic. Annotated bullets (``— moved to epic/22-...``,
    ``— discarded 2026-05-08``) are explicitly historical per the
    authoring doc and are excluded from this check.
  - ``epic-children-all-terminal`` *(warning)* — the epic is
    at ``status: open`` but every child reached a terminal status
    (``done`` / ``discarded``) for its family. The doc explicitly
    declares this state "mildly inconsistent but not an error" — the
    author may have intentionally kept the epic open for follow-up
    children. Surfaced as a warning so authors can review and either
    flip the epic to ``done`` or knowingly leave it open.

The check is workspace-only — file-scope mode is not supported in v1
because the relationship is inherently cross-file (an epic's
membership state can only be derived from every issue-family file's
``parent:`` field). Pure library — no stdout / stderr / exit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from common import ISSUE_FOLDERS, iter_issue_files
from markdown import extract_body, read_fm
from status_model import TERMINAL_STATUSES

from .refs import RefIndex


@dataclass(frozen=True)
class Mismatch:
    path: str
    rule: str
    message: str
    field: str | None = None
    severity: str = "error"


_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_BULLET_BACKLINK_RE = re.compile(
    r"^\s*[-*]\s+"
    r"(?:\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+)?"
    r"`(?P<path>[^`]+\.md)`"
    r"(?P<rest>.*)$"
)


def _normalize_body_link_path(raw: str) -> str:
    """Normalize a body backlink target into a workspace reference.

    Body backlinks are backtick-wrapped relative paths (e.g.,
    ``../task/2-foo.md``, ``architecture.md``); the workspace
    ``RefIndex`` expects the bare ``<folder>/<id>-<slug>`` (or
    ``<folder>/<id>-<slug>.md``) form. Strip leading ``./`` and ``../``
    segments so the resolver can match.
    """
    s = raw.strip()
    while s.startswith("./"):
        s = s[2:]
    while s.startswith("../"):
        s = s[3:]
    return s


@dataclass(frozen=True)
class _ChildEntry:
    raw_path: str
    annotated: bool


def _extract_children_entries(body_text: str) -> list[_ChildEntry]:
    """Parse a `## Children` H2 section into bullet entries.

    Walks lines after the ``## Children`` heading until the next H2 (or
    EOF), and extracts backtick-wrapped backlink bullets. A bullet
    starts with a list marker (``-`` / ``*``), an optional
    ``YYYY-MM-DD HH:mm`` timestamp, and a backtick-wrapped ``.md`` path
    (relative or basename). Trailing whitespace and prose after the
    closing backtick mark the bullet as "annotated" — matching the
    doc's pattern of ``— moved to ...`` / ``— discarded ...``
    historical markers. Annotated entries record former membership and
    are excluded from the stale-listing check.
    """
    entries: list[_ChildEntry] = []
    in_section = False
    fence: str | None = None
    for line in body_text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```"):
            fence = "```"
            continue
        if stripped.startswith("~~~"):
            fence = "~~~"
            continue
        m_h2 = _H2_RE.match(line)
        if m_h2:
            heading_text = m_h2.group(1).strip()
            in_section = heading_text == "Children"
            continue
        if not in_section:
            continue
        m_bullet = _BULLET_BACKLINK_RE.match(line)
        if not m_bullet:
            continue
        raw_path = m_bullet.group("path").strip()
        rest = m_bullet.group("rest").strip()
        entries.append(_ChildEntry(raw_path=raw_path, annotated=bool(rest)))
    return entries


def _collect_epics(a4_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, canonical) pairs for every `epic/*.md` file."""
    out: list[tuple[Path, str]] = []
    for p in iter_issue_files(a4_dir, "epic"):
        out.append((p, f"epic/{p.stem}"))
    return out


def _collect_parent_pointers(
    a4_dir: Path, index: RefIndex
) -> dict[str, list[tuple[str, str, str]]]:
    """Build {epic-canonical → list of (canonical, folder, status)} from `parent:`.

    Walks all issue-family folders (task / bug / spike / research / and
    others that may grow ``parent:`` later) and collects every file
    whose ``parent:`` resolves to an epic. Status is captured
    alongside the canonical so the drift detector can evaluate
    terminal-set membership without a second pass.
    """
    out: dict[str, list[tuple[str, str, str]]] = {}
    for folder in ISSUE_FOLDERS:
        if folder == "epic":
            continue
        for p in iter_issue_files(a4_dir, folder):
            fm = read_fm(p)
            if not fm:
                continue
            raw = fm.get("parent")
            if raw is None:
                continue
            if isinstance(raw, str) and not raw.strip():
                continue
            resolved = index.resolve(raw)
            if resolved is None or resolved.folder != "epic":
                continue
            status = fm.get("status")
            status_str = status if isinstance(status, str) else ""
            out.setdefault(resolved.canonical, []).append(
                (f"{folder}/{p.stem}", folder, status_str)
            )
    return out


def run(a4_dir: Path, _file: Path | None = None) -> list[Mismatch]:
    """Workspace scan only. ``_file`` is accepted for registry parity but
    ignored — the relationship is inherently cross-file and a single-file
    scope would produce a partial view."""
    index = RefIndex(a4_dir)
    epics = _collect_epics(a4_dir)
    parent_map = _collect_parent_pointers(a4_dir, index)

    mismatches: list[Mismatch] = []
    for path, canonical in epics:
        body = extract_body(path).content
        entries = _extract_children_entries(body)

        listed_all: set[str] = set()
        listed_active: set[str] = set()
        for entry in entries:
            resolved = index.resolve(_normalize_body_link_path(entry.raw_path))
            if resolved is None:
                # Unresolved backlink is either a typo or a legacy
                # reference; do not double-report — backlink form
                # validation is out of scope here. Skip silently.
                continue
            listed_all.add(resolved.canonical)
            if not entry.annotated:
                listed_active.add(resolved.canonical)

        children = parent_map.get(canonical, [])
        children_via_parent = {c[0] for c in children}

        rel = str(path.relative_to(a4_dir))

        for child_canonical in sorted(children_via_parent - listed_all):
            mismatches.append(
                Mismatch(
                    path=rel,
                    rule="epic-child-not-listed",
                    field="Children",
                    message=(
                        f"`{child_canonical}` declares "
                        f"`parent: {canonical}` but is not listed in "
                        "the `## Children` body section"
                    ),
                )
            )

        for listed_canonical in sorted(listed_active - children_via_parent):
            mismatches.append(
                Mismatch(
                    path=rel,
                    rule="epic-stale-listing",
                    field="Children",
                    message=(
                        f"`{listed_canonical}` is listed in `## Children` "
                        f"but no file declares `parent: {canonical}` "
                        "(annotate the bullet to record former membership "
                        "if intentional)"
                    ),
                )
            )

        epic_fm = read_fm(path) or {}
        if (
            epic_fm.get("status") == "open"
            and children
            and all(
                status in TERMINAL_STATUSES.get(folder, frozenset())
                for _, folder, status in children
            )
        ):
            mismatches.append(
                Mismatch(
                    path=rel,
                    rule="epic-children-all-terminal",
                    field="status",
                    message=(
                        "epic `status: open` but every child has reached "
                        "a terminal status (`done` / `discarded`); "
                        "consider flipping the epic to `done`, or "
                        "leave open intentionally for follow-up children"
                    ),
                    severity="warning",
                )
            )

    return mismatches
