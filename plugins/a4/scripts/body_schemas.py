# /// script
# requires-python = ">=3.11"
# ///
"""Registry helpers for the body XSDs under ``body_schemas/``.

The XSDs themselves are the single source of truth — one file per
frontmatter ``type:`` value, named ``<type>.xsd``. This module provides
the thin lookup other a4 scripts use to resolve a frontmatter ``type``
to the schema file that validates that body.

Consumers should pass the returned path to ``xmlschema.XMLSchema11`` (or
equivalent) — this module deliberately stays free of an XML parser
dependency so importing it is cheap.
"""

from __future__ import annotations

from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent / "body_schemas"


def schema_path(type_: str) -> Path | None:
    """Return the XSD path for ``type_``, or ``None`` if no schema exists."""
    if not type_ or "/" in type_ or "\\" in type_:
        return None
    candidate = SCHEMAS_DIR / f"{type_}.xsd"
    return candidate if candidate.is_file() else None


def all_types() -> tuple[str, ...]:
    """Every ``type:`` value with a schema, sorted by name."""
    return tuple(sorted(p.stem for p in SCHEMAS_DIR.glob("*.xsd")))
