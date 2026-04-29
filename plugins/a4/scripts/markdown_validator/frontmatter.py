"""Frontmatter schema validator (library).

Enforces the per-type schema defined in
``plugins/a4/references/frontmatter-schema.md``:

  - Required fields are present and non-empty.
  - Enum values are in their allowed set.
  - Field types are correct (int, date, list, string).
  - Path references use plain string form (no wikilink brackets, no
    ``.md`` extension).
  - ``type:`` on wiki pages matches the file basename.
  - Ids are unique across all issue folders in the workspace.

Unknown frontmatter fields are ignored — validation is strict on known
rules and lenient about extension. Pure library — no stdout / stderr /
exit. The unified CLI ``scripts/validate.py`` adapts ``run`` output to
``Issue`` via ``markdown_validator.registry`` and owns presentation /
exit codes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from common import (
    ISSUE_FOLDERS,
    WIKI_TYPES,
    discover_files,
    is_empty as _is_empty,
    is_int as _is_int,
    iter_issue_files,
)
from markdown import extract_preamble
from status_model import KIND_BY_FOLDER, STATUS_BY_FOLDER

from .refs import RefIndex

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


SCHEMAS: dict[str, Schema] = {
    "wiki": Schema(
        name="wiki",
        required=frozenset({"type", "updated"}),
        enums={"type": WIKI_TYPES},
        date_fields=frozenset({"updated"}),
    ),
    "usecase": Schema(
        name="usecase",
        required=frozenset({"type", "id", "title", "status", "created", "updated"}),
        enums={
            "type": frozenset({"usecase"}),
            "status": STATUS_BY_FOLDER["usecase"],
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"related", "supersedes"}),
    ),
    "task": Schema(
        name="task",
        required=frozenset(
            {"type", "id", "title", "kind", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"task"}),
            "kind": KIND_BY_FOLDER["task"],
            "status": STATUS_BY_FOLDER["task"],
        },
        int_fields=frozenset({"id", "cycle"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"implements", "depends_on", "spec"}),
    ),
    "review": Schema(
        name="review",
        required=frozenset(
            {"type", "id", "kind", "status", "source", "created", "updated"}
        ),
        enums={
            "type": frozenset({"review"}),
            "kind": KIND_BY_FOLDER["review"],
            "status": STATUS_BY_FOLDER["review"],
            "priority": frozenset({"high", "medium", "low"}),
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"target"}),
    ),
    "spec": Schema(
        name="spec",
        required=frozenset({"type", "id", "title", "status", "created"}),
        enums={
            "type": frozenset({"spec"}),
            "status": STATUS_BY_FOLDER["spec"],
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"supersedes", "related"}),
    ),
    "idea": Schema(
        name="idea",
        required=frozenset({"type", "id", "title", "status", "created", "updated"}),
        enums={
            "type": frozenset({"idea"}),
            "status": STATUS_BY_FOLDER["idea"],
        },
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
            "status": STATUS_BY_FOLDER["spark"],
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
        # Top-level files are wiki pages iff their basename is a known
        # wiki type. Dispatching on the basename (rather than peeking at
        # `type:`) ensures legacy files missing `type:` still surface as
        # missing-required rather than being silently skipped.
        if rel.stem in WIKI_TYPES:
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
    """Format-only check; existence is checked separately via RefIndex.

    Accepted forms (post-strip, sans `.md`):

      - ``#<int>`` short form
      - ``<folder>/<id>`` or ``<folder>/<id>-<slug>``
      - bare ``<id>-<slug>`` (id is workspace-globally unique)
      - wiki basename, spark stem
    """
    if not isinstance(value, str):
        return f"expected string, got {type(value).__name__}"
    if value.startswith("[[") or value.endswith("]]"):
        return "wikilink brackets not allowed in frontmatter path references"
    if value.endswith(".md"):
        return ".md extension not allowed in frontmatter path references"
    s = value.strip()
    if s == "":
        return "empty path reference"
    if s.startswith("#"):
        tail = s[1:]
        if not tail or not tail.isdigit():
            return (
                f"`#<id>` short form requires a positive integer id, "
                f"got {value!r}"
            )
    return None


def _validate_date(value: Any) -> str | None:
    if isinstance(value, date) and not isinstance(value, bool):
        return None
    if isinstance(value, str) and DATE_RE.match(value):
        return None
    return f"expected YYYY-MM-DD date, got {value!r}"


def validate_file(
    path: Path,
    a4_dir: Path,
    fm: dict,
    index: RefIndex | None = None,
) -> list[Violation]:
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
            elif index is not None and index.resolve(fm[fld]) is None:
                violations.append(
                    Violation(
                        rel_str,
                        "unresolved-ref",
                        fld,
                        f"{fld}: reference {fm[fld]!r} does not resolve to "
                        "any file in the workspace",
                    )
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
                    continue
                if index is not None and index.resolve(item) is None:
                    violations.append(
                        Violation(
                            rel_str,
                            "unresolved-ref",
                            fld,
                            f"{fld}[{i}]: reference {item!r} does not resolve "
                            "to any file in the workspace",
                        )
                    )

    if ftype == "task":
        kind = fm.get("kind")
        if kind == "spike":
            impl = fm.get("implements")
            if isinstance(impl, list) and any(
                isinstance(x, str) and x.strip() for x in impl
            ):
                violations.append(
                    Violation(
                        rel_str,
                        "kind-field-forbidden",
                        "implements",
                        "`implements:` is forbidden on `kind: spike` (a4 v6.0.0).",
                    )
                )
        if kind in {"spike", "research"} and fm.get("cycle") is not None:
            violations.append(
                Violation(
                    rel_str,
                    "kind-field-forbidden",
                    "cycle",
                    f"`cycle:` is forbidden on `kind: {kind}` (a4 v6.0.0).",
                )
            )
        if kind in {"spike", "research"}:
            spec_val = fm.get("spec")
            if isinstance(spec_val, list) and any(
                isinstance(x, str) and x.strip() for x in spec_val
            ):
                violations.append(
                    Violation(
                        rel_str,
                        "kind-field-forbidden",
                        "spec",
                        f"`spec:` is forbidden on `kind: {kind}` (a4 v6.0.0); cite via body markdown link.",
                    )
                )

    if ftype == "wiki":
        declared = fm.get("type")
        expected = path.stem
        if isinstance(declared, str) and declared != expected:
            violations.append(
                Violation(
                    rel_str,
                    "type-filename-mismatch",
                    "type",
                    f"type `{declared}` does not match filename `{expected}.md`",
                )
            )

    return violations


def validate_id_uniqueness(a4_dir: Path) -> list[Violation]:
    seen: dict[int, list[Path]] = {}
    for folder in ISSUE_FOLDERS:
        for p in iter_issue_files(a4_dir, folder):
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

    Pure — no stdout/stderr/exit. Callers (registry adapter, hook
    dispatcher) own presentation and exit codes. ``a4_dir`` must be a
    resolved directory; ``file``, if given, must be a resolved path
    inside ``a4_dir`` (caller-enforced).

    A workspace-wide ``RefIndex`` is built once per call so each file's
    path-reference fields can be checked for existence in addition to
    format. File-scope mode still scans the entire workspace to build
    the index (the resolution check needs the global id map), so callers
    that want raw format-only checks should not rely on file-scope mode
    for hot paths.
    """
    files = [file] if file else discover_files(a4_dir)

    index = RefIndex(a4_dir)

    violations: list[Violation] = []
    for path in files:
        preamble = extract_preamble(path)
        if preamble.fm is None:
            missing = check_missing_frontmatter(path, a4_dir)
            if missing:
                violations.append(missing)
            continue
        violations.extend(validate_file(path, a4_dir, preamble.fm, index))

    if file is None:
        violations.extend(validate_id_uniqueness(a4_dir))

    return violations, files
