# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate frontmatter across an a4/ workspace.

Enforces the per-type schema defined in plugins/a4/references/frontmatter-schema.md:

  - Required fields are present and non-empty.
  - Enum values are in their allowed set.
  - Field types are correct (int, date, list, string).
  - Path references use plain string form (no wikilink brackets, no .md extension).
  - `kind:` on wiki pages matches the file basename.
  - `wiki_impact` entries name a known wiki kind.
  - Ids are unique across all issue folders in the workspace.

Unknown frontmatter fields are ignored — validation is strict on known rules
and lenient about extension. All violations are errors; exit code is 2 if any
violation is found, else 0.

Usage:
    uv run validate_frontmatter.py <a4-dir>              # scan whole workspace
    uv run validate_frontmatter.py <a4-dir> <file>       # validate one file
    uv run validate_frontmatter.py <a4-dir> --json       # structured JSON output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from common import (
    ISSUE_FOLDERS,
    WIKI_KINDS,
    discover_files,
    is_empty as _is_empty,
    is_int as _is_int,
)
from markdown import extract_preamble

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Schema:
    name: str
    required: frozenset[str]
    enums: dict[str, frozenset[str]] = field(default_factory=dict)
    int_fields: frozenset[str] = frozenset()
    date_fields: frozenset[str] = frozenset()
    path_list_fields: frozenset[str] = frozenset()
    path_scalar_fields: frozenset[str] = frozenset()
    wiki_ref_list_fields: frozenset[str] = frozenset()


SCHEMAS: dict[str, Schema] = {
    "wiki": Schema(
        name="wiki",
        required=frozenset({"kind", "updated"}),
        enums={"kind": WIKI_KINDS},
        date_fields=frozenset({"updated"}),
    ),
    "usecase": Schema(
        name="usecase",
        required=frozenset({"id", "title", "status", "created", "updated"}),
        enums={
            "status": frozenset(
                {
                    "draft", "ready", "implementing", "revising",
                    "shipped", "superseded", "discarded", "blocked",
                }
            )
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset(
            {"depends_on", "justified_by", "related", "supersedes", "implemented_by"}
        ),
    ),
    "task": Schema(
        name="task",
        required=frozenset({"id", "title", "kind", "status", "created", "updated"}),
        enums={
            "kind": frozenset({"feature", "spike", "bug"}),
            "status": frozenset(
                {"open", "pending", "progress", "complete", "failing", "discarded"}
            ),
        },
        int_fields=frozenset({"id", "cycle"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"implements", "depends_on", "justified_by"}),
    ),
    "review": Schema(
        name="review",
        required=frozenset({"id", "kind", "status", "source", "created", "updated"}),
        enums={
            "kind": frozenset({"finding", "gap", "question"}),
            "status": frozenset({"open", "in-progress", "resolved", "discarded"}),
            "priority": frozenset({"high", "medium", "low"}),
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_scalar_fields=frozenset({"target"}),
        wiki_ref_list_fields=frozenset({"wiki_impact"}),
    ),
    "decision": Schema(
        name="decision",
        required=frozenset({"id", "title", "status", "created"}),
        enums={"status": frozenset({"draft", "final", "superseded"})},
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"supersedes", "related"}),
    ),
    "idea": Schema(
        name="idea",
        required=frozenset({"id", "title", "status", "created", "updated"}),
        enums={"status": frozenset({"open", "promoted", "discarded"})},
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"promoted", "related"}),
    ),
    "spark_brainstorm": Schema(
        name="spark_brainstorm",
        required=frozenset(
            {"type", "pipeline", "topic", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"brainstorm"}),
            "pipeline": frozenset({"spark"}),
            "status": frozenset({"open", "promoted", "discarded"}),
        },
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"promoted"}),
    ),
}


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str
    field: str | None
    message: str


def detect_type(rel: Path, fm: dict) -> str | None:
    if len(rel.parts) < 2:
        kind = fm.get("kind")
        if isinstance(kind, str) and kind in WIKI_KINDS:
            return "wiki"
        return None
    folder = rel.parts[0]
    if folder in ISSUE_FOLDERS:
        return folder
    if folder == "spark":
        t = fm.get("type")
        if t == "brainstorm":
            return "spark_brainstorm"
    return None


def _validate_path_ref(value: Any) -> str | None:
    if not isinstance(value, str):
        return f"expected string, got {type(value).__name__}"
    if value.startswith("[[") or value.endswith("]]"):
        return "wikilink brackets not allowed in frontmatter path references"
    if value.endswith(".md"):
        return ".md extension not allowed in frontmatter path references"
    if value.strip() == "":
        return "empty path reference"
    return None


def _validate_date(value: Any) -> str | None:
    if isinstance(value, date) and not isinstance(value, bool):
        return None
    if isinstance(value, str) and DATE_RE.match(value):
        return None
    return f"expected YYYY-MM-DD date, got {value!r}"


def validate_file(path: Path, a4_dir: Path, fm: dict) -> list[Violation]:
    violations: list[Violation] = []
    rel = path.relative_to(a4_dir)
    rel_str = str(rel)

    ftype = detect_type(rel, fm)
    if ftype is None:
        return violations

    schema = SCHEMAS[ftype]

    for fld in sorted(schema.required):
        if fld not in fm or _is_empty(fm[fld]):
            violations.append(
                Violation(
                    rel_str,
                    "missing-required",
                    fld,
                    f"required field `{fld}` is missing or empty",
                )
            )

    for fld, allowed in schema.enums.items():
        if fld in fm and not _is_empty(fm[fld]):
            val = fm[fld]
            if not isinstance(val, str) or val not in allowed:
                violations.append(
                    Violation(
                        rel_str,
                        "enum-violation",
                        fld,
                        f"`{fld}: {val!r}` not in {sorted(allowed)}",
                    )
                )

    for fld in schema.int_fields:
        if fld in fm and fm[fld] is not None and not _is_int(fm[fld]):
            violations.append(
                Violation(
                    rel_str,
                    "type-mismatch",
                    fld,
                    f"`{fld}` must be int, got {type(fm[fld]).__name__}",
                )
            )

    for fld in schema.date_fields:
        if fld in fm and fm[fld] is not None:
            err = _validate_date(fm[fld])
            if err:
                violations.append(
                    Violation(rel_str, "type-mismatch", fld, f"{fld}: {err}")
                )

    for fld in schema.path_scalar_fields:
        if fld in fm and fm[fld] is not None:
            err = _validate_path_ref(fm[fld])
            if err:
                violations.append(
                    Violation(rel_str, "path-format", fld, f"{fld}: {err}")
                )

    for fld in schema.path_list_fields:
        if fld in fm and fm[fld] is not None:
            val = fm[fld]
            if not isinstance(val, list):
                violations.append(
                    Violation(
                        rel_str,
                        "type-mismatch",
                        fld,
                        f"`{fld}` must be a list, got {type(val).__name__}",
                    )
                )
                continue
            for i, item in enumerate(val):
                err = _validate_path_ref(item)
                if err:
                    violations.append(
                        Violation(rel_str, "path-format", fld, f"{fld}[{i}]: {err}")
                    )

    for fld in schema.wiki_ref_list_fields:
        if fld in fm and fm[fld] is not None:
            val = fm[fld]
            if not isinstance(val, list):
                violations.append(
                    Violation(
                        rel_str,
                        "type-mismatch",
                        fld,
                        f"`{fld}` must be a list, got {type(val).__name__}",
                    )
                )
                continue
            for i, item in enumerate(val):
                if not isinstance(item, str):
                    violations.append(
                        Violation(
                            rel_str,
                            "type-mismatch",
                            fld,
                            f"{fld}[{i}]: expected string, got {type(item).__name__}",
                        )
                    )
                    continue
                if item not in WIKI_KINDS:
                    violations.append(
                        Violation(
                            rel_str,
                            "wiki-ref-unknown",
                            fld,
                            f"{fld}[{i}]: `{item}` is not a known wiki kind "
                            f"(expected one of {sorted(WIKI_KINDS)})",
                        )
                    )

    if ftype == "wiki":
        declared = fm.get("kind")
        expected = path.stem
        if isinstance(declared, str) and declared != expected:
            violations.append(
                Violation(
                    rel_str,
                    "kind-filename-mismatch",
                    "kind",
                    f"kind `{declared}` does not match filename `{expected}.md`",
                )
            )

    return violations


def validate_id_uniqueness(a4_dir: Path) -> list[Violation]:
    seen: dict[int, list[Path]] = {}
    for folder in ISSUE_FOLDERS:
        sub = a4_dir / folder
        if not sub.is_dir():
            continue
        for p in sorted(sub.glob("*.md")):
            preamble = extract_preamble(p)
            if not preamble.fm:
                continue
            raw = preamble.fm.get("id")
            if _is_int(raw):
                seen.setdefault(raw, []).append(p)

    violations: list[Violation] = []
    for id_value, paths in sorted(seen.items()):
        if len(paths) > 1:
            joined = ", ".join(str(p.relative_to(a4_dir)) for p in paths)
            for p in paths:
                violations.append(
                    Violation(
                        str(p.relative_to(a4_dir)),
                        "id-collision",
                        "id",
                        f"id {id_value} is shared across: {joined}",
                    )
                )
    return violations


def check_missing_frontmatter(path: Path, a4_dir: Path) -> Violation | None:
    try:
        rel = path.relative_to(a4_dir)
    except ValueError:
        return None
    if len(rel.parts) >= 2 and rel.parts[0] in (*ISSUE_FOLDERS, "spark"):
        return Violation(
            str(rel),
            "missing-frontmatter",
            None,
            "file in an issue/spark folder has no frontmatter",
        )
    return None


def run(
    a4_dir: Path, file: Path | None = None
) -> tuple[list[Violation], list[Path]]:
    """Library API: scan the workspace (or a single file) and return
    violations plus the files scanned.

    Pure — no stdout/stderr/exit. Callers (main, validate.py aggregator)
    own presentation and exit codes. `a4_dir` must be a resolved
    directory; `file`, if given, must be a resolved path inside `a4_dir`
    (caller-enforced).
    """
    files = [file] if file else discover_files(a4_dir)

    violations: list[Violation] = []
    for path in files:
        preamble = extract_preamble(path)
        if preamble.fm is None:
            missing = check_missing_frontmatter(path, a4_dir)
            if missing:
                violations.append(missing)
            continue
        violations.extend(validate_file(path, a4_dir, preamble.fm))

    if file is None:
        violations.extend(validate_id_uniqueness(a4_dir))

    return violations, files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate frontmatter across an a4/ workspace."
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "file", type=Path, nargs="?", help="validate a single file only"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit structured JSON to stdout"
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    target: Path | None = None
    if args.file:
        resolved = args.file.resolve()
        try:
            resolved.relative_to(a4_dir)
        except ValueError:
            print(
                f"Error: {resolved} is not inside {a4_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        target = resolved

    violations, files = run(a4_dir, target)

    if args.json:
        out = {
            "a4_dir": str(a4_dir),
            "scanned": [str(p.relative_to(a4_dir)) for p in files],
            "violations": [asdict(v) for v in violations],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(2 if violations else 0)

    if not violations:
        print(f"OK — {len(files)} file(s) scanned, no violations.")
        sys.exit(0)

    file_count = len({v.path for v in violations})
    print(
        f"{len(violations)} violation(s) across {file_count} file(s):",
        file=sys.stderr,
    )
    for v in violations:
        loc = v.path + (f" [{v.field}]" if v.field else "")
        print(f"  {loc} ({v.rule}): {v.message}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
