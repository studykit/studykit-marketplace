# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Render a4/ workspace state as a markdown report.

Single source of truth for the workspace dashboard view. Two callers:

  /a4:dashboard skill — surfaces the full report to the user as the
                        on-demand workspace summary (no file is written).
  /a4:compass   Step 3.2 — pulls only the sections its layered gap diagnosis
                needs (`skills/compass/references/gap-diagnosis.md`).

The per-item frontmatter under `a4/` is the source of truth; this report
is a fresh snapshot computed each run. Output is markdown so the LLM
consumer parses it cheaply and a human reading stdout sees a tidy
summary at the same time.

Sections (kebab-case identifier on the left):

  wiki-pages          presence + last-updated for the 7 canonical wiki kinds.
  stage-progress      mixed-axis view of usecase/arch/bootstrap/roadmap/impl.
  issue-counts        per folder × {active, in_progress, terminal, total}
                      plus by-kind for review/task.
  usecases-by-source  UC `source:` distribution (Reverse-only detection).
  drift-alerts        open / in-progress reviews with `source: drift-detector`,
                      sorted by priority then id desc.
  open-reviews        open / in-progress non-drift reviews, sorted by
                      priority then created then id.
  active-tasks        tasks with status in {pending, progress, failing}.
  blocked-items       any issue with status: blocked, with depends_on chain.
  milestones          per active milestone — tasks complete/total + open reviews.
  recent-activity     top 10 issue items by `updated:` desc.
  open-ideas          non-terminal `idea/*.md`.
  open-sparks         non-terminal `spark/*.md`.

Status vocabularies follow the spec ADRs (terminal / in-progress sets
documented inline below).

Usage:
    uv run workspace_state.py <a4-dir>                      # full dashboard (all sections, with header)
    uv run workspace_state.py <a4-dir> drift-alerts         # one section, no header
    uv run workspace_state.py <a4-dir> drift-alerts active-tasks blocked-items
                                                            # multiple sections, in the order requested
    uv run workspace_state.py --list-sections               # print section identifiers and exit

Section names are validated; an unknown name aborts with exit code 2 and
the available identifiers on stderr.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from common import ISSUE_FOLDERS
from markdown import extract_preamble
from status_model import (
    ACTIVE_TASK_STATUSES,
    BLOCKED_STATUSES,
    IN_PROGRESS_STATUSES,
    TERMINAL_STATUSES,
)

# Local ordered tuple — drives the Wiki-pages table rendering.
# `common.WIKI_KINDS` is a frozenset (membership-test only).
WIKI_KINDS: tuple[str, ...] = (
    "context",
    "domain",
    "architecture",
    "actors",
    "nfr",
    "roadmap",
    "bootstrap",
)

# Spark flavor → terminal set. Distinct from TERMINAL_STATUSES["spark"]
# because the file-flavor key (`brainstorm`) does not equal the folder
# key (`spark`).
SPARK_TERMINAL: dict[str, frozenset[str]] = {
    "brainstorm": TERMINAL_STATUSES["spark"],
}

PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
RECENT_ACTIVITY_LIMIT = 10


@dataclass
class IssueItem:
    folder: str
    path: Path
    id_: int | None
    title: str
    status: str
    kind: str | None
    source: str | None
    priority: str | None
    target: str | None
    milestone: str | None
    updated: str | None
    created: str | None = None
    depends_on: list[str] = field(default_factory=list)
    wiki_impact: list[str] = field(default_factory=list)

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def ref(self) -> str:
        return f"{self.folder}/{self.stem}"


@dataclass
class WikiPage:
    kind: str
    path: Path | None
    updated: str | None = None


@dataclass
class SparkItem:
    path: Path
    status: str
    updated: str | None

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def flavor(self) -> str:
        # Only `.brainstorm` is supported in spark/ today.
        if self.path.stem.endswith(".brainstorm"):
            return "brainstorm"
        return ""


def _fm(path: Path) -> dict:
    return extract_preamble(path).fm or {}


def _display_date(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (date, datetime)):
        return raw.isoformat()[:10]
    s = str(raw).strip()
    return s or None


def _str_field(fm: dict, key: str) -> str | None:
    raw = fm.get(key)
    return str(raw).strip() if isinstance(raw, str) else None


def _str_list(fm: dict, key: str) -> list[str]:
    raw = fm.get(key)
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if isinstance(x, str) and str(x).strip()]


def discover_wikis(a4_dir: Path) -> list[WikiPage]:
    pages: list[WikiPage] = []
    for kind in WIKI_KINDS:
        path = a4_dir / f"{kind}.md"
        if not path.is_file():
            pages.append(WikiPage(kind=kind, path=None))
            continue
        fm = _fm(path)
        pages.append(
            WikiPage(kind=kind, path=path, updated=_display_date(fm.get("updated")))
        )
    return pages


def discover_issues(a4_dir: Path) -> dict[str, list[IssueItem]]:
    out: dict[str, list[IssueItem]] = {folder: [] for folder in ISSUE_FOLDERS}
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for md in sorted(sub.glob("*.md")):
            fm = _fm(md)
            raw_id = fm.get("id")
            out[folder].append(
                IssueItem(
                    folder=folder,
                    path=md,
                    id_=raw_id if isinstance(raw_id, int) else None,
                    title=str(fm.get("title") or md.stem).strip(),
                    status=str(fm.get("status") or "").strip(),
                    kind=_str_field(fm, "kind"),
                    source=_str_field(fm, "source"),
                    priority=_str_field(fm, "priority"),
                    target=_str_field(fm, "target"),
                    milestone=_str_field(fm, "milestone"),
                    updated=_display_date(fm.get("updated")),
                    created=_display_date(fm.get("created")),
                    depends_on=_str_list(fm, "depends_on"),
                    wiki_impact=_str_list(fm, "wiki_impact"),
                )
            )
    return out


def discover_sparks(a4_dir: Path) -> list[SparkItem]:
    sub = a4_dir / "spark"
    if not sub.is_dir():
        return []
    items: list[SparkItem] = []
    for md in sorted(sub.glob("*.md")):
        fm = _fm(md)
        items.append(
            SparkItem(
                path=md,
                status=str(fm.get("status") or "open").strip() or "open",
                updated=_display_date(fm.get("updated") or fm.get("date")),
            )
        )
    return items


# ---------- Section renderers ----------------------------------------------


def render_wiki_pages(pages: list[WikiPage]) -> str:
    lines = ["## Wiki pages", "", "| Page | Present | Updated |", "|------|---------|---------|"]
    for p in pages:
        present = "yes" if p.path is not None else "—"
        lines.append(f"| {p.kind} | {present} | {p.updated or '—'} |")
    return "\n".join(lines)


def render_stage_progress(
    pages_by_kind: dict[str, WikiPage],
    usecases: list[IssueItem],
    tasks: list[IssueItem],
) -> str:
    def status_summary(folder: str, items: list[IssueItem]) -> str:
        if not items:
            return "no items"
        counts: Counter[str] = Counter()
        for i in items:
            counts[i.status or "(missing)"] += 1
        terminal = TERMINAL_STATUSES.get(folder, set())
        in_prog = IN_PROGRESS_STATUSES.get(folder, set())
        ordered: list[str] = []
        for s in sorted(terminal):
            if s in counts:
                ordered.append(s)
        for s in sorted(in_prog):
            if s in counts:
                ordered.append(s)
        for s in sorted(BLOCKED_STATUSES):
            if s in counts:
                ordered.append(s)
        for s in sorted(counts):
            if s not in terminal and s not in in_prog and s not in BLOCKED_STATUSES:
                ordered.append(s)
        parts = [f"{counts[s]} {s}" for s in ordered]
        return " · ".join(parts) + f" ({sum(counts.values())} total)"

    def wiki_row(kind: str) -> str:
        page = pages_by_kind.get(kind)
        if page is None or page.path is None:
            return "not created"
        return f"present · updated {page.updated or '—'}"

    milestones = sorted({t.milestone for t in tasks if t.milestone})
    roadmap = pages_by_kind.get("roadmap")
    if roadmap is None or roadmap.path is None:
        roadmap_row = "not created"
    else:
        roadmap_row = (
            f"present · updated {roadmap.updated or '—'} · "
            f"{len(milestones)} milestone(s)"
        )

    lines = [
        "## Stage progress",
        "",
        "| Stage | State |",
        "|-------|-------|",
        f"| Usecase | {status_summary('usecase', usecases)} |",
        f"| Arch | {wiki_row('architecture')} |",
        f"| Bootstrap | {wiki_row('bootstrap')} |",
        f"| Roadmap | {roadmap_row} |",
        f"| Impl | {status_summary('task', tasks)} |",
    ]
    return "\n".join(lines)


def render_issue_counts(issues: dict[str, list[IssueItem]]) -> str:
    lines = [
        "## Issue counts",
        "",
        "| Folder | Active | In-progress | Terminal | Total |",
        "|--------|--------|-------------|----------|-------|",
    ]

    def row(label: str, items: list[IssueItem], folder: str) -> str:
        terminal = sum(1 for i in items if i.status in TERMINAL_STATUSES.get(folder, set()))
        in_prog = sum(1 for i in items if i.status in IN_PROGRESS_STATUSES.get(folder, set()))
        total = len(items)
        active = total - terminal - in_prog
        return f"| {label} | {active} | {in_prog} | {terminal} | {total} |"

    lines.append(row("usecase", issues["usecase"], "usecase"))
    lines.append(row("task", issues["task"], "task"))

    reviews = issues["review"]
    for kind in ("finding", "gap", "question"):
        kind_items = [i for i in reviews if i.kind == kind]
        if kind_items:
            lines.append(row(f"review ({kind})", kind_items, "review"))
    review_other = [i for i in reviews if i.kind not in {"finding", "gap", "question"}]
    if review_other:
        lines.append(row("review (other)", review_other, "review"))

    lines.append(row("adr", issues["adr"], "adr"))
    lines.append(row("idea", issues["idea"], "idea"))

    tasks = issues["task"]
    task_kinds = sorted({t.kind for t in tasks if t.kind})
    if task_kinds:
        lines.append("")
        lines.append("Task by kind:")
        for kind in task_kinds:
            kind_items = [t for t in tasks if t.kind == kind]
            terminal = sum(1 for i in kind_items if i.status in TERMINAL_STATUSES["task"])
            in_prog = sum(1 for i in kind_items if i.status in IN_PROGRESS_STATUSES["task"])
            total = len(kind_items)
            active = total - terminal - in_prog
            lines.append(
                f"- {kind}: {active} active · {in_prog} in-progress · {terminal} terminal · {total} total"
            )
    return "\n".join(lines)


def render_usecases_by_source(usecases: list[IssueItem]) -> str:
    if not usecases:
        return "## Use cases by source\n\n*No use cases yet.*"
    by_source = Counter(u.source or "(unset)" for u in usecases)
    parts = [f"{by_source[s]} {s}" for s in sorted(by_source)]
    return "## Use cases by source\n\n" + " · ".join(parts)


def render_drift_alerts(reviews: list[IssueItem]) -> str:
    alerts = [
        r
        for r in reviews
        if r.source == "drift-detector" and r.status in {"open", "in-progress"}
    ]
    heading = f"## Drift alerts ({len(alerts)})"
    if not alerts:
        return f"{heading}\n\n*No open drift alerts.*"
    alerts.sort(
        key=lambda r: (PRIORITY_ORDER.get(r.priority or "", 3), -(r.id_ or 0))
    )
    lines = [heading, ""]
    for r in alerts:
        target = r.target or "—"
        lines.append(
            f"- {r.ref} — {r.priority or '—'} {r.kind or '—'} — {r.title} (target=`{target}`)"
        )
    return "\n".join(lines)


def render_open_reviews(reviews: list[IssueItem]) -> str:
    open_items = [
        r
        for r in reviews
        if r.source != "drift-detector" and r.status in {"open", "in-progress"}
    ]
    heading = f"## Open reviews ({len(open_items)})"
    if not open_items:
        return f"{heading}\n\n*No open non-drift reviews.*"
    open_items.sort(
        key=lambda r: (
            PRIORITY_ORDER.get(r.priority or "", 3),
            r.created or "",
            r.id_ or 0,
        )
    )
    lines = [heading, ""]
    for r in open_items:
        target = f" (target=`{r.target}`)" if r.target else ""
        ms = f" [milestone={r.milestone}]" if r.milestone else ""
        created = f" · created {r.created}" if r.created else ""
        lines.append(
            f"- {r.ref} — {r.priority or '—'} {r.kind or '—'}{created} — {r.title}{target}{ms}"
        )
    return "\n".join(lines)


def render_active_tasks(tasks: list[IssueItem]) -> str:
    active = [t for t in tasks if t.status in ACTIVE_TASK_STATUSES]
    heading = f"## Active tasks ({len(active)})"
    if not active:
        return f"{heading}\n\n*No tasks pending / progress / failing.*"
    active.sort(key=lambda t: (t.status, t.id_ or 0))
    lines = [heading, ""]
    for t in active:
        deps = f" depends_on={t.depends_on}" if t.depends_on else ""
        ms = f" [milestone={t.milestone}]" if t.milestone else ""
        kind = f" {t.kind}" if t.kind else ""
        lines.append(f"- {t.ref} — {t.status}{kind} — {t.title}{ms}{deps}")
    return "\n".join(lines)


def render_blocked_items(issues: dict[str, list[IssueItem]]) -> str:
    blocked: list[IssueItem] = []
    for folder in ISSUE_FOLDERS:
        blocked.extend(i for i in issues[folder] if i.status == "blocked")
    heading = f"## Blocked items ({len(blocked)})"
    if not blocked:
        return f"{heading}\n\n*No blocked items.*"
    lines = [heading, ""]
    for i in blocked:
        deps = f" depends_on={i.depends_on}" if i.depends_on else ""
        lines.append(f"- {i.ref} — {i.title}{deps}")
    return "\n".join(lines)


def render_milestones(tasks: list[IssueItem], reviews: list[IssueItem]) -> str:
    buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "complete": 0, "open_reviews": 0}
    )
    for t in tasks:
        if not t.milestone:
            continue
        buckets[t.milestone]["total"] += 1
        if t.status in TERMINAL_STATUSES["task"]:
            buckets[t.milestone]["complete"] += 1
    for r in reviews:
        if not r.milestone:
            continue
        if r.status in TERMINAL_STATUSES["review"]:
            continue
        buckets[r.milestone]["open_reviews"] += 1

    if not buckets:
        return "## Milestones\n\n*No milestones declared.*"

    lines = [
        "## Milestones",
        "",
        "| Milestone | Tasks complete / total | Open reviews |",
        "|-----------|------------------------|--------------|",
    ]
    for name in sorted(buckets):
        b = buckets[name]
        lines.append(f"| {name} | {b['complete']} / {b['total']} | {b['open_reviews']} |")
    return "\n".join(lines)


def render_recent_activity(issues: dict[str, list[IssueItem]]) -> str:
    flat: list[IssueItem] = []
    for folder in ISSUE_FOLDERS:
        flat.extend(issues[folder])
    dated = [i for i in flat if i.updated]
    dated.sort(key=lambda i: (i.updated or "", i.id_ or 0), reverse=True)
    top = dated[:RECENT_ACTIVITY_LIMIT]
    if not top:
        return "## Recent activity\n\n*No items with `updated:` frontmatter yet.*"
    lines = [
        "## Recent activity",
        "",
        "| Item | Folder | Status | Updated |",
        "|------|--------|--------|---------|",
    ]
    for i in top:
        lines.append(f"| {i.ref} | {i.folder} | {i.status or '—'} | {i.updated} |")
    return "\n".join(lines)


def render_open_ideas(ideas: list[IssueItem]) -> str:
    open_ideas = [i for i in ideas if i.status not in TERMINAL_STATUSES["idea"]]
    heading = f"## Open ideas ({len(open_ideas)})"
    if not open_ideas:
        return f"{heading}\n\n*No open ideas.*"
    open_ideas.sort(key=lambda i: (i.updated or "", i.id_ or 0), reverse=True)
    lines = [heading, ""]
    for i in open_ideas:
        updated = f" · updated {i.updated}" if i.updated else ""
        lines.append(f"- {i.ref} — {i.title}{updated}")
    return "\n".join(lines)


def render_open_sparks(sparks: list[SparkItem]) -> str:
    open_sparks = [
        s for s in sparks if s.status not in SPARK_TERMINAL.get(s.flavor, set())
    ]
    heading = f"## Open sparks ({len(open_sparks)})"
    if not open_sparks:
        return f"{heading}\n\n*No open sparks.*"
    open_sparks.sort(key=lambda s: s.stem)
    lines = [heading, ""]
    for s in open_sparks:
        flavor = f" · {s.flavor}" if s.flavor else ""
        updated = f" · updated {s.updated}" if s.updated else ""
        lines.append(f"- spark/{s.stem}{flavor}{updated}")
    return "\n".join(lines)


# Section registry — `dict` preserves insertion order, which doubles as the
# canonical full-dashboard ordering when no specific sections are requested.
# Each entry maps a kebab-case identifier to a callable that takes the
# pre-built context dict and returns the rendered markdown for that section.
SECTION_RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "wiki-pages": lambda ctx: render_wiki_pages(ctx["pages"]),
    "stage-progress": lambda ctx: render_stage_progress(
        ctx["pages_by_kind"], ctx["issues"]["usecase"], ctx["issues"]["task"]
    ),
    "issue-counts": lambda ctx: render_issue_counts(ctx["issues"]),
    "usecases-by-source": lambda ctx: render_usecases_by_source(
        ctx["issues"]["usecase"]
    ),
    "drift-alerts": lambda ctx: render_drift_alerts(ctx["issues"]["review"]),
    "open-reviews": lambda ctx: render_open_reviews(ctx["issues"]["review"]),
    "active-tasks": lambda ctx: render_active_tasks(ctx["issues"]["task"]),
    "blocked-items": lambda ctx: render_blocked_items(ctx["issues"]),
    "milestones": lambda ctx: render_milestones(
        ctx["issues"]["task"], ctx["issues"]["review"]
    ),
    "recent-activity": lambda ctx: render_recent_activity(ctx["issues"]),
    "open-ideas": lambda ctx: render_open_ideas(ctx["issues"]["idea"]),
    "open-sparks": lambda ctx: render_open_sparks(ctx["sparks"]),
}

SECTION_NAMES: tuple[str, ...] = tuple(SECTION_RENDERERS.keys())


def _build_context(a4_dir: Path) -> dict[str, Any]:
    pages = discover_wikis(a4_dir)
    return {
        "pages": pages,
        "pages_by_kind": {p.kind: p for p in pages},
        "issues": discover_issues(a4_dir),
        "sparks": discover_sparks(a4_dir),
    }


def render_state(a4_dir: Path, sections: list[str] | None = None) -> str:
    """Render the workspace state.

    `sections=None` produces the full dashboard with the top-level header.
    A non-empty list produces only those sections (in the order given) and
    omits the header — useful for compass and other targeted callers.
    """
    ctx = _build_context(a4_dir)

    if sections is None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = (
            f"# Workspace state\n\n"
            f"*Generated {ts} — fresh snapshot, no file written. "
            "Source of truth is per-item frontmatter under `a4/`.*"
        )
        parts = [header] + [SECTION_RENDERERS[name](ctx) for name in SECTION_NAMES]
    else:
        parts = [SECTION_RENDERERS[name](ctx) for name in sections]

    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a4/ workspace state as a markdown report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Section identifiers (in canonical full-dashboard order):\n  "
            + "\n  ".join(SECTION_NAMES)
        ),
    )
    parser.add_argument(
        "--list-sections",
        action="store_true",
        help="print section identifiers (one per line) and exit",
    )
    parser.add_argument(
        "a4_dir",
        type=Path,
        nargs="?",
        help="path to the a4/ workspace",
    )
    parser.add_argument(
        "sections",
        nargs="*",
        help=(
            "section identifiers to render; omit for the full dashboard. "
            "Use --list-sections to see available names."
        ),
    )
    args = parser.parse_args()

    if args.list_sections:
        for name in SECTION_NAMES:
            print(name)
        return 0

    if args.a4_dir is None:
        parser.error("a4_dir is required (unless --list-sections is given)")

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        return 1

    if args.sections:
        unknown = [s for s in args.sections if s not in SECTION_RENDERERS]
        if unknown:
            print(
                "Error: unknown section(s): " + ", ".join(unknown),
                file=sys.stderr,
            )
            print(
                "Available: " + ", ".join(SECTION_NAMES),
                file=sys.stderr,
            )
            return 2
        sys.stdout.write(render_state(a4_dir, sections=args.sections))
    else:
        sys.stdout.write(render_state(a4_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
