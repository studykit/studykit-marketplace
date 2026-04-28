# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate the per-type section enum block in rules/a4-section-enum.md.

Source of truth is ``body_schemas/<type>.xsd``. Each schema has a root
``<xs:element name="<type>">`` whose ``<xs:all>`` lists the recognized
sections; ``minOccurs="0"`` (or absence of ``minOccurs``) decides whether
the section is optional or required.

The rule file ships a sentinel-bracketed block::

    <!-- BEGIN section-enum -->
    ... generated bullets ...
    <!-- END section-enum -->

This script overwrites only that block; everything else in the rule
file is hand-edited.

Modes (mirroring ``generate_status_diagrams.py``):

    uv run generate_section_enum.py            # emit to stdout
    uv run generate_section_enum.py --check    # exit 2 on drift
    uv run generate_section_enum.py --write    # rewrite the rule file
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import body_schemas

XS_NS = "{http://www.w3.org/2001/XMLSchema}"

RULE_DOC: Path = (
    Path(__file__).resolve().parent.parent
    / "rules"
    / "a4-section-enum.md"
)

BEGIN_MARKER = "<!-- BEGIN section-enum -->"
END_MARKER = "<!-- END section-enum -->"


def _sections_for(type_: str) -> tuple[list[str], list[str]]:
    """Return (required, optional) section names for ``type_``.

    Both lists are sorted alphabetically. Reads
    ``body_schemas/<type>.xsd`` and walks the root element's
    ``xs:complexType/xs:all`` children.
    """
    schema_file = body_schemas.schema_path(type_)
    if schema_file is None:
        raise SystemExit(f"No schema for type: {type_}")
    tree = ET.parse(schema_file)
    root = tree.getroot()
    type_el = root.find(f"{XS_NS}element[@name='{type_}']")
    if type_el is None:
        raise SystemExit(
            f"{schema_file}: no <xs:element name='{type_}'> at schema root"
        )
    all_el = type_el.find(f"./{XS_NS}complexType/{XS_NS}all")
    if all_el is None:
        raise SystemExit(
            f"{schema_file}: no <xs:complexType>/<xs:all> under root element"
        )
    required: list[str] = []
    optional: list[str] = []
    for el in all_el.findall(f"{XS_NS}element"):
        name = el.get("name")
        if not name:
            continue
        if el.get("minOccurs", "1") == "0":
            optional.append(name)
        else:
            required.append(name)
    required.sort()
    optional.sort()
    return required, optional


def _format_bullet(type_: str, required: list[str], optional: list[str], pad: int) -> str:
    req = ", ".join(required)
    opt = ", ".join(optional)
    return f"- {type_.ljust(pad)}  R{{{req}}} O{{{opt}}}"


def generate_block() -> str:
    """Build the bullet list for every type in body_schemas/."""
    types = list(body_schemas.all_types())
    pad = max(len(t) for t in types)
    lines = [_format_bullet(t, *_sections_for(t), pad=pad) for t in types]
    return "\n".join(lines)


# Captures the body between `BEGIN\n` and `\nEND`. The block payload
# (group 2) does NOT include the surrounding newlines, so it round-trips
# cleanly through generate_block() / read.
_BLOCK_RE = re.compile(
    rf"({re.escape(BEGIN_MARKER)}\n)([\s\S]*?)(\n{re.escape(END_MARKER)})",
    re.MULTILINE,
)


def _match_or_die(text: str) -> re.Match[str]:
    m = _BLOCK_RE.search(text)
    if m is None:
        raise SystemExit(
            f"Could not locate `{BEGIN_MARKER}` ... `{END_MARKER}` markers "
            f"in {RULE_DOC}"
        )
    return m


def _splice(text: str, new_block: str) -> str:
    m = _match_or_die(text)
    return text[: m.start(2)] + new_block + text[m.end(2) :]


def _existing_block(text: str) -> str:
    return _match_or_die(text).group(2)


def cmd_emit() -> int:
    print(generate_block())
    return 0


def cmd_check() -> int:
    if not RULE_DOC.is_file():
        sys.stderr.write(
            f"ERROR: {RULE_DOC} does not exist. Run with --write to create "
            "the rule file scaffold first (or hand-write it once).\n"
        )
        return 2
    text = RULE_DOC.read_text(encoding="utf-8")
    existing = _existing_block(text)
    generated = generate_block()
    if existing == generated:
        print(f"OK — section enum in {RULE_DOC.name} matches body_schemas/.")
        return 0
    sys.stderr.write("--- DRIFT in section-enum block ---\n")
    sys.stderr.write("Doc has:\n")
    sys.stderr.write(existing + "\n")
    sys.stderr.write("Generated:\n")
    sys.stderr.write(generated + "\n\n")
    sys.stderr.write(
        "Run `uv run generate_section_enum.py --write` to sync the rule "
        "file.\n"
    )
    return 2


def cmd_write() -> int:
    generated = generate_block()
    if not RULE_DOC.is_file():
        sys.stderr.write(
            f"ERROR: {RULE_DOC} does not exist. Create the scaffold (with "
            f"the {BEGIN_MARKER} ... {END_MARKER} markers in place) before "
            "running --write.\n"
        )
        return 2
    text = RULE_DOC.read_text(encoding="utf-8")
    new_text = _splice(text, generated)
    if new_text == text:
        print("No changes — rule file already in sync.")
        return 0
    RULE_DOC.write_text(new_text, encoding="utf-8")
    print(f"Updated section-enum block in {RULE_DOC}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or check the per-type section enum block in "
            "plugins/a4/rules/a4-section-enum.md against body_schemas/."
        )
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        "--check",
        action="store_true",
        help="exit 2 if the rule file differs from generated output",
    )
    grp.add_argument(
        "--write",
        action="store_true",
        help="rewrite the rule file's enum block with generated content",
    )
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.write:
        return cmd_write()
    return cmd_emit()


if __name__ == "__main__":
    sys.exit(main())
