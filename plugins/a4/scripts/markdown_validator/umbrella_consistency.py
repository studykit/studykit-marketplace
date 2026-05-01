"""Umbrella consistency + drift validator (library).

`umbrella-authoring.md` declares the validator's reverse-`parent:`
resolver as authoritative for membership; the umbrella body's
`## Children` section is the human-readable mirror. Drift between the
two surfaces — and the soft signal that an umbrella's children are all
terminal while the umbrella itself is still `open` — is silent without
this check.

Three signals are surfaced:

  - ``umbrella-child-not-listed`` *(error)* — a file's frontmatter
    ``parent:`` resolves to this umbrella but the umbrella body's
    ``## Children`` section does not list it. The doc names this as a
    common mistake ("Children listed only via reverse-`parent:`").
  - ``umbrella-stale-listing`` *(error)* — the umbrella body's
    ``## Children`` section lists a child (without an annotation
    suffix) but no file's frontmatter ``parent:`` resolves to this
    umbrella. Annotated bullets (``— moved to umbrella/22-...``,
    ``— discarded 2026-05-08``) are explicitly historical per the
    authoring doc and are excluded from this check.
  - ``umbrella-children-all-terminal`` *(warning)* — the umbrella is
    at ``status: open`` but every child reached a terminal status
    (``complete`` / ``discarded``) for its family. The doc explicitly
    declares this state "mildly inconsistent but not an error" — the
    author may have intentionally kept the umbrella open for follow-up
    children. Surfaced as a warning so authors can review and either
    flip the umbrella to ``complete`` or knowingly leave it open.

The check is workspace-only — file-scope mode is not supported in v1
because the relationship is inherently cross-file (an umbrella's
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
_BULLET_LINK_RE = re.compile(
    r"^\s*[-*]\s+\[(?P<text>[^\]]*)\]\((?P<path>[^)]+)\)(?P<rest>.*)$"
)


def _normalize_body_link_path(raw: str) -> str:
    """Normalize a body markdown-link target into a workspace reference.

    Body links from inside ``a4/umbrella/<file>.md`` use relative paths
    (``../task/<id>-<slug>.md``); the workspace ``RefIndex`` expects the
    bare ``<folder>/<id>-<slug>`` (or ``<folder>/<id>-<slug>.md``) form.
    Strip leading ``./`` and ``../`` segments so the resolver can match.
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
    EOF), and extracts markdown-link bullets. A bullet is "annotated"
    when there is non-whitespace text after the link's closing ``)`` —
    matching the doc's pattern of ``— moved to ...`` / ``— discarded
    YYYY-MM-DD`` historical markers. Annotated entries record former
    membership and are excluded from the stale-listing check.
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
        m_bullet = _BULLET_LINK_RE.match(line)
        if not m_bullet:
            continue
        raw_path = m_bullet.group("path").strip()
        rest = m_bullet.group("rest").strip()
        entries.append(_ChildEntry(raw_path=raw_path, annotated=bool(rest)))
    return entries


def _collect_umbrellas(a4_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, canonical) pairs for every `umbrella/*.md` file."""
    out: list[tuple[Path, str]] = []
    for p in iter_issue_files(a4_dir, "umbrella"):
        out.append((p, f"umbrella/{p.stem}"))
    return out


def _collect_parent_pointers(
    a4_dir: Path, index: RefIndex
) -> dict[str, list[tuple[str, str, str]]]:
    """Build {umbrella-canonical → list of (canonical, folder, status)} from `parent:`.

    Walks all issue-family folders (task / bug / spike / research / and
    others that may grow ``parent:`` later) and collects every file
    whose ``parent:`` resolves to an umbrella. Status is captured
    alongside the canonical so the drift detector can evaluate
    terminal-set membership without a second pass.
    """
    out: dict[str, list[tuple[str, str, str]]] = {}
    for folder in ISSUE_FOLDERS:
        if folder == "umbrella":
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
            if resolved is None or resolved.folder != "umbrella":
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
    umbrellas = _collect_umbrellas(a4_dir)
    parent_map = _collect_parent_pointers(a4_dir, index)

    mismatches: list[Mismatch] = []
    for path, canonical in umbrellas:
        body = extract_body(path).content
        entries = _extract_children_entries(body)

        listed_all: set[str] = set()
        listed_active: set[str] = set()
        for entry in entries:
            resolved = index.resolve(_normalize_body_link_path(entry.raw_path))
            if resolved is None:
                # Unresolved link is either a typo or a legacy reference;
                # do not double-report — the markdown-link check is out
                # of scope here. Skip silently.
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
                    rule="umbrella-child-not-listed",
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
                    rule="umbrella-stale-listing",
                    field="Children",
                    message=(
                        f"`{listed_canonical}` is listed in `## Children` "
                        f"but no file declares `parent: {canonical}` "
                        "(annotate the bullet to record former membership "
                        "if intentional)"
                    ),
                )
            )

        umbrella_fm = read_fm(path) or {}
        if (
            umbrella_fm.get("status") == "open"
            and children
            and all(
                status in TERMINAL_STATUSES.get(folder, frozenset())
                for _, folder, status in children
            )
        ):
            mismatches.append(
                Mismatch(
                    path=rel,
                    rule="umbrella-children-all-terminal",
                    field="status",
                    message=(
                        "umbrella `status: open` but every child has reached "
                        "a terminal status (`complete` / `discarded`); "
                        "consider flipping the umbrella to `complete`, or "
                        "leave open intentionally for follow-up children"
                    ),
                    severity="warning",
                )
            )

    return mismatches
