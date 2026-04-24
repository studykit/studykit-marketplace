# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Aggregate file references across handoff files, grouped by topic.

Sources of reference data — body scan only; no `references:` frontmatter
field is required:

    1. Obsidian wikilinks in body prose: `[[path]]`, `[[path#heading]]`,
       `![[path]]`, `![[path#heading]]`, `[[path|alias]]` variants.
    2. Injection markers produced by inject_includes.py:
       `<!-- injected: path#heading @ date -->`.

Frontmatter is read only for the `topic:` field — the grouping key.
Handoff bodies are never displayed, only scanned.

Paths are emitted verbatim from the wikilink / injection marker, following
Obsidian convention (trailing `.md` is typically omitted). Both extraction
sources preserve the author's literal path form, so `[[a4/plan]]` and
`<!-- injected: a4/plan#X ... -->` naturally collapse.

Usage:
    uv run topic_references.py <handoff-dir> <topic>
        print unique paths referenced by handoffs with this topic

    uv run topic_references.py <handoff-dir> <topic> --filter <prefix>
        restrict output to paths starting with <prefix>

    uv run topic_references.py <handoff-dir> <topic> --with-handoffs
        inverse listing: per path, which handoffs reference it

    uv run topic_references.py <handoff-dir> --list-topics
        list all distinct topics with their handoff counts
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
INJECTED_RE = re.compile(r"<!--\s*injected:\s*([^\s#]+)(?:#\S+)?\s*@[^>]*-->")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        fm = {}
    body = parts[2]
    return (fm if isinstance(fm, dict) else {}), body


def extract_refs(body: str) -> set[str]:
    refs: set[str] = set()
    for match in WIKILINK_RE.finditer(body):
        refs.add(match.group(1).strip())
    for match in INJECTED_RE.finditer(body):
        refs.add(match.group(1).strip())
    return refs


def collect(handoff_dir: Path) -> list[tuple[Path, dict, set[str]]]:
    results: list[tuple[Path, dict, set[str]]] = []
    for md in sorted(handoff_dir.glob("*.md")):
        if md.name == "INDEX.md":
            continue
        text = md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        results.append((md, fm, extract_refs(body)))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate file references by handoff topic.")
    parser.add_argument("handoff_dir", type=Path)
    parser.add_argument("topic", nargs="?", help="topic slug (omit only with --list-topics)")
    parser.add_argument("--filter", dest="filter_prefix", default=None, help="keep only paths starting with this prefix")
    parser.add_argument("--with-handoffs", action="store_true", help="show which handoffs reference each path")
    parser.add_argument("--list-topics", action="store_true", help="list all topics with handoff counts")
    args = parser.parse_args()

    if not args.handoff_dir.is_dir():
        print(f"Error: {args.handoff_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    collected = collect(args.handoff_dir)

    if args.list_topics:
        counts: dict[str, int] = defaultdict(int)
        for _, fm, _ in collected:
            topic = fm.get("topic")
            if isinstance(topic, str) and topic:
                counts[topic] += 1
        for topic, count in sorted(counts.items()):
            print(f"{count}\t{topic}")
        return

    if args.topic is None:
        parser.error("topic is required unless --list-topics is used")

    matching = [(p, fm, refs) for p, fm, refs in collected if fm.get("topic") == args.topic]
    if not matching:
        print(f"Error: no handoffs found with topic '{args.topic}'", file=sys.stderr)
        sys.exit(1)

    if args.with_handoffs:
        inverse: dict[str, list[str]] = defaultdict(list)
        for p, _, refs in matching:
            for ref in refs:
                if args.filter_prefix and not ref.startswith(args.filter_prefix):
                    continue
                inverse[ref].append(p.name)
        for ref in sorted(inverse):
            handoffs = ", ".join(sorted(inverse[ref]))
            print(f"{ref}\t{handoffs}")
        return

    all_refs: set[str] = set()
    for _, _, refs in matching:
        all_refs.update(refs)
    if args.filter_prefix:
        all_refs = {r for r in all_refs if r.startswith(args.filter_prefix)}
    for ref in sorted(all_refs):
        print(ref)


if __name__ == "__main__":
    main()
