# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Regenerate a4/INDEX.md from the current workspace state.

The workspace index is a dashboard of wiki-page state, stage progress,
open issues, drift alerts, milestone progress, recent activity, and open
sparks. It is a **view** — the per-item frontmatter is the source of
truth. Each section (where feasible) contains an Obsidian dataview block
for live rendering plus a static markdown fallback for non-Obsidian
viewers. Stage progress is static-only because it mixes wiki-page
presence with cross-folder issue aggregates that dataview cannot express
in a single block.

The script regenerates the entire file on each run. Dataview query blocks
are written as fixed literal text; static tables are computed fresh from
workspace state. Static blocks are wrapped with
`<!-- static-fallback-start: <id> -->` / `<!-- static-fallback-end: <id> -->`
markers so future surgical edits are possible if needed.

The canonical dataview query blocks are also documented in
`plugins/a4/references/obsidian-dataview.md` as reference snippets. When
changing a block here, update the reference doc too — the two must stay
in sync.

Usage:
    uv run index_refresh.py <a4-dir>              # write INDEX.md
    uv run index_refresh.py <a4-dir> --dry-run    # render to stdout, do not write
    uv run index_refresh.py <a4-dir> --stdout     # render to stdout and also write
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

WIKI_KINDS: tuple[str, ...] = (
    "context",
    "domain",
    "architecture",
    "actors",
    "nfr",
    "plan",
    "bootstrap",
)
ISSUE_FOLDERS: tuple[str, ...] = ("usecase", "task", "review", "decision", "idea")

# Status vocabularies per the ADR (2026-04-23-spec-as-wiki-and-issues.decide.md
# and 2026-04-24-idea-slot.decide.md for `idea`).
TERMINAL_STATUSES: dict[str, set[str]] = {
    "usecase": {"shipped", "superseded", "discarded"},
    "task": {"complete", "discarded"},
    "review": {"resolved", "discarded"},
    "decision": {"final", "superseded"},
    "idea": {"promoted", "discarded"},
}
IN_PROGRESS_STATUSES: dict[str, set[str]] = {
    "usecase": {"implementing", "revising"},
    "task": {"implementing"},
    "review": {"in-progress"},
    "decision": set(),
    "idea": set(),
}
BLOCKED_STATUSES: set[str] = {"blocked"}

SPARK_TERMINAL: dict[str, set[str]] = {
    "brainstorm": {"promoted", "discarded"},
}

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

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def wikilink(self) -> str:
        return f"[[{self.folder}/{self.stem}]]"


@dataclass
class WikiPage:
    kind: str
    path: Path | None  # None if not present
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
        # Only `.brainstorm` is supported in spark/ today. Decisions are hand-
        # authored at `a4/decision/<id>-<slug>.md`; research lives at project-
        # root `./research/<slug>.md` via `/a4:research`.
        stem = self.path.stem
        if stem.endswith(".brainstorm"):
            return "brainstorm"
        return ""


def split_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}, parts[2]
    return (fm if isinstance(fm, dict) else {}), parts[2]


def display_date(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (date, datetime)):
        return raw.isoformat()[:10]
    s = str(raw).strip()
    return s or None


def discover_wikis(a4_dir: Path) -> list[WikiPage]:
    pages: list[WikiPage] = []
    for kind in WIKI_KINDS:
        path = a4_dir / f"{kind}.md"
        if not path.is_file():
            pages.append(WikiPage(kind=kind, path=None))
            continue
        fm, _ = split_frontmatter(path)
        pages.append(
            WikiPage(
                kind=kind,
                path=path,
                updated=display_date(fm.get("updated")),
            )
        )
    return pages


def discover_issues(a4_dir: Path) -> dict[str, list[IssueItem]]:
    out: dict[str, list[IssueItem]] = {folder: [] for folder in ISSUE_FOLDERS}
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for md in sorted(sub.glob("*.md")):
            fm, _ = split_frontmatter(md)
            raw_id = fm.get("id")
            item = IssueItem(
                folder=folder,
                path=md,
                id_=raw_id if isinstance(raw_id, int) else None,
                title=str(fm.get("title") or md.stem).strip(),
                status=str(fm.get("status") or "").strip(),
                kind=(str(fm["kind"]).strip() if isinstance(fm.get("kind"), str) else None),
                source=(str(fm["source"]).strip() if isinstance(fm.get("source"), str) else None),
                priority=(
                    str(fm["priority"]).strip() if isinstance(fm.get("priority"), str) else None
                ),
                target=(str(fm["target"]).strip() if isinstance(fm.get("target"), str) else None),
                milestone=(
                    str(fm["milestone"]).strip()
                    if isinstance(fm.get("milestone"), str)
                    else None
                ),
                updated=display_date(fm.get("updated")),
            )
            out[folder].append(item)
    return out


def discover_sparks(a4_dir: Path) -> list[SparkItem]:
    sub = a4_dir / "spark"
    if not sub.is_dir():
        return []
    items: list[SparkItem] = []
    for md in sorted(sub.glob("*.md")):
        fm, _ = split_frontmatter(md)
        status = str(fm.get("status") or "open").strip() or "open"
        items.append(
            SparkItem(
                path=md,
                status=status,
                updated=display_date(fm.get("updated") or fm.get("date")),
            )
        )
    return items


# ---------- Section builders ------------------------------------------------


def section_wiki_pages(pages: list[WikiPage]) -> tuple[str, str, str]:
    heading = "## Wiki pages"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID file.link AS "Page", kind AS "Kind", updated AS "Updated"\n'
        'FROM "a4"\n'
        "WHERE kind\n"
        "SORT kind ASC\n"
        "```"
    )
    lines = ["| Page | Present | Updated |", "|------|---------|---------|"]
    for page in pages:
        present = "yes" if page.path is not None else "—"
        updated = page.updated or "—"
        link = f"[[{page.kind}]]" if page.path is not None else page.kind
        lines.append(f"| {link} | {present} | {updated} |")
    return heading, dataview, "\n".join(lines)


def section_stage_progress(
    pages_by_kind: dict[str, WikiPage],
    usecases: list[IssueItem],
    tasks: list[IssueItem],
) -> tuple[str, str | None, str]:
    heading = "## Stage progress"

    def stage_row_for_issues(
        folder: str, items: list[IssueItem]
    ) -> str:
        if not items:
            return "no items"
        counts: Counter[str] = Counter()
        for item in items:
            status = item.status or "(missing)"
            counts[status] += 1
        total = sum(counts.values())
        # List statuses in a stable order: terminal first, then in-progress,
        # then blocked, then everything else alphabetically.
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
        for s in sorted(counts.keys()):
            if s not in terminal and s not in in_prog and s not in BLOCKED_STATUSES:
                ordered.append(s)
        parts = [f"{counts[s]} {s}" for s in ordered]
        return " · ".join(parts) + f" ({total} total)"

    def wiki_row(kind: str) -> str:
        page = pages_by_kind.get(kind)
        if page is None or page.path is None:
            return "not created"
        return f"present · updated {page.updated or '—'}"

    milestones = sorted({t.milestone for t in tasks if t.milestone})
    plan_page = pages_by_kind.get("plan")
    plan_row = (
        f"not created"
        if plan_page is None or plan_page.path is None
        else f"present · updated {plan_page.updated or '—'} · {len(milestones)} milestone(s)"
    )

    lines = [
        "| Stage | State |",
        "|-------|-------|",
        f"| Usecase | {stage_row_for_issues('usecase', usecases)} |",
        f"| Arch | {wiki_row('architecture')} |",
        f"| Bootstrap | {wiki_row('bootstrap')} |",
        f"| Plan | {plan_row} |",
        f"| Impl | {stage_row_for_issues('task', tasks)} |",
    ]
    return heading, None, "\n".join(lines)


def section_open_issues(issues: dict[str, list[IssueItem]]) -> tuple[str, str, str]:
    heading = "## Open issues"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID file.folder AS "Folder", status AS "Status", length(rows) AS "Count"\n'
        'FROM "a4/usecase" OR "a4/task" OR "a4/review" OR "a4/decision" OR "a4/idea"\n'
        "WHERE status\n"
        "GROUP BY file.folder + \" · \" + status\n"
        "SORT file.folder ASC\n"
        "```"
    )

    lines = ["| Type | Open / active | In-progress | Terminal | Total |", "|------|---------------|-------------|----------|-------|"]

    def row(label: str, items: list[IssueItem], folder: str) -> str:
        total = len(items)
        terminal = sum(
            1 for i in items if i.status in TERMINAL_STATUSES.get(folder, set())
        )
        in_prog = sum(
            1 for i in items if i.status in IN_PROGRESS_STATUSES.get(folder, set())
        )
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

    lines.append(row("decision", issues["decision"], "decision"))
    lines.append(row("idea", issues["idea"], "idea"))

    return heading, dataview, "\n".join(lines)


def section_drift_alerts(
    reviews: list[IssueItem],
) -> tuple[str, str, str, int]:
    alerts = [
        r
        for r in reviews
        if r.source == "drift-detector"
        and r.status in {"open", "in-progress"}
    ]
    heading = f"## Drift alerts ({len(alerts)})"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID file.link AS "Review", target AS "Wiki", priority AS "Priority", status AS "Status"\n'
        'FROM "a4/review"\n'
        'WHERE source = "drift-detector" AND (status = "open" OR status = "in-progress")\n'
        "SORT priority ASC, updated DESC\n"
        "```"
    )

    if not alerts:
        static = "*No open drift alerts.*"
        return heading, dataview, static, 0

    priority_order = {"high": 0, "medium": 1, "low": 2}
    alerts_sorted = sorted(
        alerts,
        key=lambda a: (
            priority_order.get(a.priority or "", 3),
            -(int(a.id_) if a.id_ is not None else 0),
        ),
    )

    lines = [
        "| Review | Wiki | Priority | Status |",
        "|--------|------|----------|--------|",
    ]
    for a in alerts_sorted:
        lines.append(
            f"| {a.wikilink} | {a.target or '—'} | {a.priority or '—'} | {a.status} |"
        )
    return heading, dataview, "\n".join(lines), len(alerts)


def section_milestones(tasks: list[IssueItem], reviews: list[IssueItem]) -> tuple[str, str, str]:
    heading = "## Milestones"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID milestone AS "Milestone", length(rows) AS "Tasks"\n'
        'FROM "a4/task"\n'
        "WHERE milestone\n"
        "GROUP BY milestone\n"
        "SORT milestone ASC\n"
        "```"
    )

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
        static = "*No milestones declared.*"
        return heading, dataview, static

    lines = [
        "| Milestone | Tasks complete / total | Open reviews |",
        "|-----------|------------------------|--------------|",
    ]
    for milestone in sorted(buckets.keys()):
        b = buckets[milestone]
        lines.append(
            f"| {milestone} | {b['complete']} / {b['total']} | {b['open_reviews']} |"
        )
    return heading, dataview, "\n".join(lines)


def section_recent_activity(
    issues: dict[str, list[IssueItem]],
) -> tuple[str, str, str]:
    heading = "## Recent activity"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID file.link AS "Item", file.folder AS "Type", status AS "Status", updated AS "Updated"\n'
        'FROM "a4/usecase" OR "a4/task" OR "a4/review" OR "a4/decision" OR "a4/idea"\n'
        "WHERE updated\n"
        "SORT updated DESC\n"
        f"LIMIT {RECENT_ACTIVITY_LIMIT}\n"
        "```"
    )

    flat: list[IssueItem] = []
    for folder in ISSUE_FOLDERS:
        flat.extend(issues[folder])

    dated = [i for i in flat if i.updated]
    dated.sort(key=lambda i: (i.updated or "", i.id_ or 0), reverse=True)
    top = dated[:RECENT_ACTIVITY_LIMIT]

    if not top:
        static = "*No items with `updated:` frontmatter yet.*"
        return heading, dataview, static

    lines = [
        "| Item | Type | Status | Updated |",
        "|------|------|--------|---------|",
    ]
    for i in top:
        lines.append(
            f"| {i.wikilink} | {i.folder} | {i.status or '—'} | {i.updated} |"
        )
    return heading, dataview, "\n".join(lines)


def section_open_ideas(ideas: list[IssueItem]) -> tuple[str, str, str, int]:
    open_ideas = [
        i for i in ideas
        if i.status not in TERMINAL_STATUSES["idea"]
    ]
    heading = f"## Open ideas ({len(open_ideas)})"
    dataview = (
        "```dataview\n"
        'TABLE WITHOUT ID file.link AS "Idea", status AS "Status", updated AS "Updated"\n'
        'FROM "a4/idea"\n'
        'WHERE status = "open"\n'
        "SORT updated DESC\n"
        "```"
    )

    if not open_ideas:
        static = "*No open ideas.*"
        return heading, dataview, static, 0

    ideas_sorted = sorted(
        open_ideas,
        key=lambda i: (i.updated or "", i.id_ or 0),
        reverse=True,
    )
    lines = []
    for i in ideas_sorted:
        updated = f" · updated {i.updated}" if i.updated else ""
        lines.append(f"- {i.wikilink} — {i.title}{updated}")
    return heading, dataview, "\n".join(lines), len(open_ideas)


def section_spark(sparks: list[SparkItem]) -> tuple[str, str, str, int]:
    open_sparks = [
        s for s in sparks
        if s.status not in SPARK_TERMINAL.get(s.flavor, set())
    ]
    heading = f"## Spark (open {len(open_sparks)})"
    dataview = (
        "```dataview\n"
        "LIST\n"
        'FROM "a4/spark"\n'
        'WHERE !status OR status = "open" OR status = "draft"\n'
        "SORT file.name ASC\n"
        "```"
    )

    if not open_sparks:
        static = "*No open sparks.*"
        return heading, dataview, static, 0

    lines = []
    for s in sorted(open_sparks, key=lambda s: s.stem):
        flavor = f" · {s.flavor}" if s.flavor else ""
        updated = f" · updated {s.updated}" if s.updated else ""
        lines.append(f"- [[spark/{s.stem}]]{flavor}{updated}")
    return heading, dataview, "\n".join(lines), len(open_sparks)


# ---------- Rendering -------------------------------------------------------


def render_section(heading: str, dataview: str | None, static: str, marker_id: str) -> str:
    parts = [heading, ""]
    if dataview is not None:
        parts.append(dataview)
        parts.append("")
    parts.append(f"<!-- static-fallback-start: {marker_id} -->")
    parts.append(static)
    parts.append(f"<!-- static-fallback-end: {marker_id} -->")
    return "\n".join(parts)


def render_index(a4_dir: Path, generated_at: datetime) -> str:
    pages = discover_wikis(a4_dir)
    pages_by_kind = {p.kind: p for p in pages}
    issues = discover_issues(a4_dir)
    sparks = discover_sparks(a4_dir)

    ts = generated_at.strftime("%Y-%m-%d %H:%M")
    sections: list[str] = []

    heading, dv, static = section_wiki_pages(pages)
    sections.append(render_section(heading, dv, static, "wiki-pages"))

    heading, dv, static = section_stage_progress(
        pages_by_kind, issues["usecase"], issues["task"]
    )
    sections.append(render_section(heading, dv, static, "stage-progress"))

    heading, dv, static = section_open_issues(issues)
    sections.append(render_section(heading, dv, static, "open-issues"))

    heading, dv, static, _ = section_drift_alerts(issues["review"])
    sections.append(render_section(heading, dv, static, "drift-alerts"))

    heading, dv, static = section_milestones(issues["task"], issues["review"])
    sections.append(render_section(heading, dv, static, "milestones"))

    heading, dv, static = section_recent_activity(issues)
    sections.append(render_section(heading, dv, static, "recent-activity"))

    heading, dv, static, _ = section_open_ideas(issues["idea"])
    sections.append(render_section(heading, dv, static, "open-ideas"))

    heading, dv, static, _ = section_spark(sparks)
    sections.append(render_section(heading, dv, static, "spark"))

    body = "\n\n".join(sections)
    return (
        "# Workspace Index\n"
        "\n"
        f"*Regenerated by compass on {ts}*\n"
        "\n"
        "> This file is a view. The per-item frontmatter in `a4/` is the source of truth.\n"
        "> Obsidian renders the dataview blocks live; the static fallback below each block\n"
        "> is a snapshot refreshed only when `/a4:compass` or `/a4:index` runs.\n"
        "\n"
        f"{body}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate a4/INDEX.md from workspace state."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="render to stdout; do not write INDEX.md",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="also print the rendered content to stdout after writing",
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    generated_at = datetime.now()
    content = render_index(a4_dir, generated_at)

    if args.dry_run:
        sys.stdout.write(content)
        return

    target = a4_dir / "INDEX.md"
    target.write_text(content, encoding="utf-8")
    print(f"Wrote {target}")

    if args.stdout:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
