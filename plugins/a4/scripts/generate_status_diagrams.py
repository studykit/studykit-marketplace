# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate status transition diagrams from status_model.py.

The schema doc at plugins/a4/references/frontmatter-schema.md mirrors
the per-family transition tables in plain ASCII for human readers. This
script emits those blocks from the canonical model and provides a
--check mode that flags drift between doc and code.

Format per block (all blocks normalized to the same shape):

    <src>  → <target> | <target> | ...
    <terminal-src>  → (terminal)

  - Source rows ordered by FAMILY_TRANSITIONS dict insertion order, then
    terminal sources (states in STATUS_BY_FOLDER but absent from the
    transition table) sorted alphabetically.
  - Target sets sorted alphabetically (frozensets have no intrinsic order).
  - Source column padded to the longest source name in the block.

Usage:
    uv run generate_status_diagrams.py
    uv run generate_status_diagrams.py --check
    uv run generate_status_diagrams.py --write
    uv run generate_status_diagrams.py --family usecase
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import status_model as sm


# Families that have an ASCII block in the schema doc today.
# After a4 v12.0.0 the four task families share TASK_TRANSITIONS, so
# the "Task lifecycle" block is rendered from any one family key
# (``feature`` is the canonical pick — all four produce the same
# transitions table).
DOC_FAMILIES: tuple[str, ...] = ("usecase", "feature", "spec")

# Family key → heading text used in the schema doc.
FAMILY_HEADING: dict[str, str] = {
    "usecase": "UC lifecycle",
    "feature": "Task lifecycle",
    "spec": "Spec lifecycle",
}

SCHEMA_DOC: Path = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "frontmatter-schema.md"
)


def generate_block(family: str) -> str:
    """Return the ASCII transition block for one family."""
    transitions = sm.FAMILY_TRANSITIONS[family]
    all_states = sm.STATUS_BY_FOLDER[family]
    terminal_sources = sorted(all_states - transitions.keys())
    sources = list(transitions.keys()) + terminal_sources
    pad = max(len(s) for s in sources)
    lines: list[str] = []
    for src in sources:
        if src in transitions:
            targets = " | ".join(sorted(transitions[src]))
            lines.append(f"{src.ljust(pad)} → {targets}")
        else:
            lines.append(f"{src.ljust(pad)} → (terminal)")
    return "\n".join(lines)


def _block_pattern(heading: str) -> re.Pattern[str]:
    # Anchor at `### <heading>`, then capture the first ``` ... ``` fenced
    # block following it. Three groups: prefix (heading + intro through
    # opening fence), payload (inner text), suffix (closing fence).
    return re.compile(
        rf"(^### {re.escape(heading)}\b[\s\S]*?^```\n)"
        r"([\s\S]*?)"
        r"(\n```$)",
        re.MULTILINE,
    )


def parse_doc_blocks(text: str, families: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for fam in families:
        m = _block_pattern(FAMILY_HEADING[fam]).search(text)
        if m is None:
            raise SystemExit(
                f"Could not locate diagram block for {fam} "
                f"(### {FAMILY_HEADING[fam]}) in {SCHEMA_DOC}"
            )
        out[fam] = m.group(2)
    return out


def write_doc_blocks(text: str, blocks: dict[str, str]) -> str:
    for fam, new_block in blocks.items():
        pat = _block_pattern(FAMILY_HEADING[fam])
        m = pat.search(text)
        if m is None:
            raise SystemExit(
                f"Could not locate diagram block for {fam} "
                f"(### {FAMILY_HEADING[fam]}) in {SCHEMA_DOC}"
            )
        text = text[: m.start(2)] + new_block + text[m.end(2) :]
    return text


def find_drifts(families: list[str] | None = None) -> list[tuple[str, str, str]]:
    """Return [(family, doc_block, generated_block), ...] for any drifting blocks.

    Used by hooks. Empty list means doc and code agree.
    """
    fams = families if families else list(DOC_FAMILIES)
    text = SCHEMA_DOC.read_text(encoding="utf-8")
    existing = parse_doc_blocks(text, fams)
    drifts: list[tuple[str, str, str]] = []
    for fam in fams:
        gen = generate_block(fam)
        if existing[fam] != gen:
            drifts.append((fam, existing[fam], gen))
    return drifts


def cmd_emit(families: list[str]) -> int:
    for i, fam in enumerate(families):
        if i:
            print()
        print(f"# {fam}")
        print(generate_block(fam))
    return 0


def cmd_check(families: list[str]) -> int:
    drifts = find_drifts(families)
    if not drifts:
        print(f"OK — {len(families)} block(s) match status_model.py.")
        return 0
    for fam, doc_block, gen_block in drifts:
        sys.stderr.write(f"--- DRIFT in {fam} ---\n")
        sys.stderr.write("Doc has:\n")
        sys.stderr.write(doc_block + "\n")
        sys.stderr.write("Generated:\n")
        sys.stderr.write(gen_block + "\n\n")
    sys.stderr.write(
        f"{len(drifts)} drift(s). Run "
        "`uv run generate_status_diagrams.py --write` to sync the doc.\n"
    )
    return 2


def cmd_write(families: list[str]) -> int:
    text = SCHEMA_DOC.read_text(encoding="utf-8")
    blocks = {fam: generate_block(fam) for fam in families}
    new_text = write_doc_blocks(text, blocks)
    if new_text == text:
        print("No changes — doc already in sync.")
        return 0
    SCHEMA_DOC.write_text(new_text, encoding="utf-8")
    print(f"Updated {len(families)} block(s) in {SCHEMA_DOC}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or check the status transition diagrams in "
            "plugins/a4/references/frontmatter-schema.md against "
            "scripts/status_model.py."
        )
    )
    parser.add_argument(
        "--family",
        choices=DOC_FAMILIES,
        help="limit to one family (default: all)",
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        "--check",
        action="store_true",
        help="exit 2 if the doc differs from generated output",
    )
    grp.add_argument(
        "--write",
        action="store_true",
        help="rewrite the schema doc's blocks with generated content",
    )
    args = parser.parse_args()

    families = [args.family] if args.family else list(DOC_FAMILIES)

    if args.check:
        return cmd_check(families)
    if args.write:
        return cmd_write(families)
    return cmd_emit(families)


if __name__ == "__main__":
    sys.exit(main())
