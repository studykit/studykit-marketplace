"""Frontmatter schema validator (library).

Enforces the per-type schemas defined in
``plugins/a4/authoring/<type>-authoring.md`` (per-type field tables) and
the cross-cutting rules in
``plugins/a4/authoring/frontmatter-universals.md`` and
``plugins/a4/authoring/validator-rules.md``:

  - Required fields are present and non-empty.
  - Enum values are in their allowed set.
  - Field types are correct (int, date, list, string).
  - Path references use plain string form (no wikilink brackets, no
    ``.md`` extension).
  - ``type:`` on wiki pages matches the file basename.
  - Ids are unique across all issue folders in the workspace.
  - Post-draft authoring invariants: UC at ``status >= ready`` has
    non-empty ``actors:``; ``title:`` is free of placeholder tokens
    (``TBD``, ``???``, ``<placeholder>``, ``<todo>``, ``TODO:``) once UC
    reaches ``ready`` or spec reaches ``active``.

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
from status_model import KIND_BY_FOLDER, STATUS_BY_FOLDER, ISSUE_FAMILY_TYPES

from .refs import RefIndex

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Statuses past the initial draft phase. Once a file reaches one of these
# values, post-draft authoring invariants apply continuously (not only at
# the transition moment).
POST_DRAFT_STATUSES: dict[str, frozenset[str]] = {
    "usecase": frozenset({"ready", "implementing", "shipped", "superseded"}),
    "spec": frozenset({"active", "deprecated", "superseded"}),
}

PLACEHOLDER_TOKENS: tuple[str, ...] = (
    "TBD",
    "???",
    "<placeholder>",
    "<todo>",
    "TODO:",
)


def _placeholder_token(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    upper = value.upper()
    for token in PLACEHOLDER_TOKENS:
        if token.upper() in upper:
            return token
    return None


def _is_non_empty_str_list(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(x, str) and x.strip() for x in value
    )


@dataclass(frozen=True)
class Schema:
    name: str
    required: frozenset[str]
    enums: dict[str, frozenset[str]] = field(default_factory=dict)
    int_fields: frozenset[str] = frozenset()
    date_fields: frozenset[str] = frozenset()
    path_list_fields: frozenset[str] = frozenset()
    path_scalar_fields: frozenset[str] = frozenset()
    # Fields that must not appear (or must be empty) for this schema. Used
    # by ``spike`` / ``research`` to forbid ``implements`` / ``spec`` /
    # ``cycle`` — what was previously a kind-conditional check is now a
    # structural per-type rule.
    forbidden_fields: frozenset[str] = frozenset()


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
            {"type", "id", "title", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"task"}),
            "status": STATUS_BY_FOLDER["task"],
        },
        int_fields=frozenset({"id", "cycle"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"implements", "depends_on", "spec"}),
    ),
    "bug": Schema(
        name="bug",
        required=frozenset(
            {"type", "id", "title", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"bug"}),
            "status": STATUS_BY_FOLDER["bug"],
        },
        int_fields=frozenset({"id", "cycle"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"implements", "depends_on", "spec"}),
    ),
    "spike": Schema(
        name="spike",
        required=frozenset(
            {"type", "id", "title", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"spike"}),
            "status": STATUS_BY_FOLDER["spike"],
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"depends_on"}),
        forbidden_fields=frozenset({"implements", "spec", "cycle"}),
    ),
    "research": Schema(
        name="research",
        required=frozenset(
            {"type", "id", "title", "status", "mode", "created", "updated"}
        ),
        enums={
            "type": frozenset({"research"}),
            "status": STATUS_BY_FOLDER["research"],
            "mode": frozenset({"comparative", "single"}),
        },
        int_fields=frozenset({"id"}),
        date_fields=frozenset({"created", "updated"}),
        path_list_fields=frozenset({"depends_on", "related"}),
        forbidden_fields=frozenset({"implements", "spec", "cycle"}),
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
    "brainstorm": Schema(
        name="brainstorm",
        required=frozenset(
            {"type", "id", "title", "topic", "status", "created", "updated"}
        ),
        enums={
            "type": frozenset({"brainstorm"}),
            "status": STATUS_BY_FOLDER["brainstorm"],
        },
        int_fields=frozenset({"id"}),
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
    return None


def _validate_path_ref(value: Any) -> str | None:
    """Format-only check; existence is checked separately via RefIndex.

    Accepted forms (post-strip, sans `.md`):

      - ``<id>`` (positive YAML integer) — id-only short form
      - ``<folder>/<id>`` or ``<folder>/<id>-<slug>``
      - bare ``<id>-<slug>`` (id is workspace-globally unique)
      - wiki basename

    The legacy ``#<id>`` string short form was removed in a4 v11.0.0;
    write the bare integer id instead.
    """
    if isinstance(value, bool):
        return f"expected string or positive integer, got {type(value).__name__}"
    if isinstance(value, int):
        if value <= 0:
            return f"id-only short form must be a positive integer, got {value!r}"
        return None
    if not isinstance(value, str):
        return f"expected string or positive integer, got {type(value).__name__}"
    if value.startswith("[[") or value.endswith("]]"):
        return "wikilink brackets not allowed in frontmatter path references"
    if value.endswith(".md"):
        return ".md extension not allowed in frontmatter path references"
    s = value.strip()
    if s == "":
        return "empty path reference"
    if s.startswith("#"):
        return (
            f"legacy `#<id>` short form removed in a4 v11.0.0; "
            f"write the bare integer id instead, got {value!r}"
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

    for fld in sorted(schema.forbidden_fields):
        val = fm.get(fld)
        if val is None:
            continue
        # Empty list is treated as absent — authors may keep the field
        # explicitly empty for shape parity with other types. Any list
        # with at least one element (string id ref, integer id ref, etc.)
        # is a populated value and triggers the forbidden-field
        # violation; entry-level shape errors are surfaced separately by
        # path-format / unresolved-ref rules.
        if isinstance(val, list) and len(val) == 0:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        violations.append(
            Violation(
                rel_str,
                "type-field-forbidden",
                fld,
                f"`{fld}:` is not allowed on `type: {ftype}` (a4 v12.0.0).",
            )
        )

    if ftype == "research":
        mode = fm.get("mode")
        opts = fm.get("options")
        if mode == "comparative":
            if not _is_non_empty_str_list(opts):
                violations.append(
                    Violation(
                        rel_str,
                        "missing-required",
                        "options",
                        "`options:` must be a non-empty list of strings when "
                        "`mode: comparative`.",
                    )
                )
        elif mode == "single":
            if isinstance(opts, list) and any(
                isinstance(x, str) and x.strip() for x in opts
            ):
                violations.append(
                    Violation(
                        rel_str,
                        "type-field-forbidden",
                        "options",
                        "`options:` is not allowed when `mode: single`.",
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

    if ftype in ISSUE_FOLDERS:
        m = re.match(r"^(\d+)-", path.stem)
        raw_id = fm.get("id")
        if m and _is_int(raw_id):
            head = int(m.group(1))
            if head != raw_id:
                violations.append(
                    Violation(
                        rel_str,
                        "id-filename-mismatch",
                        "id",
                        f"filename leading id `{head}` does not match `id: {raw_id}`",
                    )
                )

    if ftype in POST_DRAFT_STATUSES:
        status = fm.get("status")
        if isinstance(status, str) and status in POST_DRAFT_STATUSES[ftype]:
            if ftype == "usecase" and not _is_non_empty_str_list(fm.get("actors")):
                violations.append(
                    Violation(
                        rel_str,
                        "missing-actors-post-draft",
                        "actors",
                        f"status={status!r} requires non-empty `actors:` "
                        "(post-draft authoring invariant)",
                    )
                )
            placeholder = _placeholder_token(fm.get("title"))
            if placeholder:
                violations.append(
                    Violation(
                        rel_str,
                        "placeholder-in-title",
                        "title",
                        f"status={status!r} but `title:` contains placeholder "
                        f"{placeholder!r}",
                    )
                )

    if ftype in ISSUE_FAMILY_TYPES:
        violations.extend(_validate_task_artifacts(rel_str, fm, path, ftype))
        violations.extend(
            _validate_complete_artifacts_present(rel_str, fm, path, a4_dir, ftype)
        )

    return violations


def _validate_task_artifacts(
    rel_str: str, fm: dict, path: Path, ftype: str
) -> list[Violation]:
    """Enforce the artifact-only contract on ``<task>.artifacts:``.

    Every entry must start with ``artifacts/<type>/<id>-<slug>/`` — and
    for ``type: spike`` only, ``artifacts/spike/archive/<id>-<slug>/``
    is also accepted (post-archive paths). Empty list is fine for any
    type. The check skips when ``id`` / filename's ``<id>-<slug>`` are
    malformed — those drift modes are surfaced by other rules.
    """
    artifacts = fm.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return []

    raw_id = fm.get("id")
    if not _is_int(raw_id):
        return []
    m = re.match(r"^(\d+)-(.+)$", path.stem)
    if not m or int(m.group(1)) != raw_id:
        return []
    id_slug = path.stem

    expected_prefix = f"artifacts/{ftype}/{id_slug}/"
    spike_archive_prefix = f"artifacts/spike/archive/{id_slug}/"
    accepted = (
        (expected_prefix, spike_archive_prefix)
        if ftype == "spike"
        else (expected_prefix,)
    )

    violations: list[Violation] = []
    for i, entry in enumerate(artifacts):
        if not isinstance(entry, str):
            continue
        e = entry.strip()
        if not e:
            continue
        if any(e.startswith(p) for p in accepted):
            continue
        suffix = (
            f" or {spike_archive_prefix!r}" if ftype == "spike" else ""
        )
        violations.append(
            Violation(
                rel_str,
                "artifacts-bad-path",
                "artifacts",
                f"artifacts[{i}]: {entry!r} must start with "
                f"{expected_prefix!r}{suffix}",
            )
        )
    return violations


_COMPLETE_ARTIFACT_TYPES: frozenset[str] = frozenset({"research", "task", "bug"})


def _validate_complete_artifacts_present(
    rel_str: str, fm: dict, path: Path, a4_dir: Path, ftype: str
) -> list[Violation]:
    """Preflight: ``research`` / ``task`` / ``bug`` issues at
    ``status: complete`` must have their listed artifacts present on disk.

    Layered on top of the static ``artifacts-bad-path`` rule —
    this one assumes the prefix is well-formed and only checks the
    filesystem. Entries that do not start with the expected
    ``artifacts/<type>/<id>-<slug>/`` prefix are skipped so the shape
    rule remains the single source of truth for that error. Malformed
    ``id`` / filename id-slug also defers as in the shape rule.
    ``artifacts/`` lives at project root (``a4_dir.parent``) per
    ``authoring/artifacts.md``.

    ``type: spike`` is intentionally excluded: at ``status: complete``
    the directory may still live at the original prefix until the user
    `git mv`s it to ``artifacts/spike/archive/<id>-<slug>/`` and rewrites
    ``artifacts:``, so an existence check would race the archive
    transition.
    """
    if ftype not in _COMPLETE_ARTIFACT_TYPES:
        return []
    if fm.get("status") != "complete":
        return []
    artifacts = fm.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return []

    raw_id = fm.get("id")
    if not _is_int(raw_id):
        return []
    m = re.match(r"^(\d+)-(.+)$", path.stem)
    if not m or int(m.group(1)) != raw_id:
        return []
    id_slug = path.stem

    expected_prefix = f"artifacts/{ftype}/{id_slug}/"
    project_root = a4_dir.parent

    violations: list[Violation] = []
    for i, entry in enumerate(artifacts):
        if not isinstance(entry, str):
            continue
        e = entry.strip()
        if not e:
            continue
        if not e.startswith(expected_prefix):
            continue
        full = project_root / e
        if not full.is_file():
            violations.append(
                Violation(
                    rel_str,
                    "artifacts-missing-file",
                    "artifacts",
                    f"artifacts[{i}]: artifact {entry!r} does not exist on disk "
                    f"(type={ftype} at status=complete must have all listed "
                    "artifact files present)",
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
    if len(rel.parts) >= 2 and rel.parts[0] in ISSUE_FOLDERS:
        return Violation(
            str(rel),
            "missing-frontmatter",
            None,
            "file in an issue folder has no frontmatter",
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
