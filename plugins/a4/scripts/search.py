# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Filter a4/ workspace files by frontmatter fields.

Single-pass scan over the a4/ workspace (wiki pages + issue folders +
spark/), applying the requested filters and printing matching records.

Reverse lookups are computed by back-scanning forward relation fields on
every file. The stored-reverse field `implemented_by` is intentionally
ignored so the result is always consistent with the forward edges, even
when `refresh_implemented_by.py` is stale.

Usage:
    uv run search.py <a4-dir> [filters...]

Filters are AND-combined. Run with no filters to list every record.

Examples:
    # All open review items
    uv run search.py <a4-dir> --folder review --status open

    # Tasks of kind feature in milestone v1.0
    uv run search.py <a4-dir> --folder task --kind feature --milestone v1.0

    # Everything that references usecase/3-search-history
    uv run search.py <a4-dir> --references usecase/3-search-history

    # Tasks implementing usecase/3-search-history
    uv run search.py <a4-dir> --references usecase/3-search-history \\
        --references-via implements

    # Reviews touching the architecture wiki, JSON output
    uv run search.py <a4-dir> --folder review --wiki-impact architecture --json

    # Custom frontmatter field — exact match (NAME=VALUE form)
    uv run search.py <a4-dir> --field source=drift-detector

    # Custom frontmatter field — list membership (any list element matches)
    uv run search.py <a4-dir> --field tags=experimental

    # Just check the field is present (any non-null value)
    uv run search.py <a4-dir> --has-field framework
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from common import ISSUE_FOLDERS, iter_issue_files, normalize_ref
from markdown import extract_preamble
from status_model import (
    KIND_BY_FOLDER as _MODEL_KIND_BY_FOLDER,
    STATUS_BY_FOLDER,
)


WIKI_KINDS_TUPLE: tuple[str, ...] = (
    "context",
    "domain",
    "architecture",
    "actors",
    "nfr",
    "roadmap",
    "bootstrap",
)

# Folder → set of valid `kind:` enum values for the `--kind` filter.
# Issue-folder kinds come from the canonical model. Wiki pages declare
# their identifier in the `type:` field (matching the file basename); the
# `wiki` entry below makes `--kind <basename>` work for the wiki folder
# by routing it through `Record.kind`, which reads `type:` for wiki
# records.
KIND_BY_FOLDER: dict[str, frozenset[str]] = {
    **_MODEL_KIND_BY_FOLDER,
    "wiki": frozenset(WIKI_KINDS_TUPLE),
}

# Forward relation fields that `--references` / `--references-via` can scan.
FORWARD_FIELDS: tuple[str, ...] = (
    "depends_on",
    "implements",
    "spec",
    "target",
    "wiki_impact",
    "supersedes",
    "promoted",
    "parent",
    "related",
)

ALL_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "review",
    "spec",
    "idea",
    "spark",
    "wiki",
    "archive",
)


@dataclass
class Record:
    folder: str
    path: Path
    fm: dict
    archived: bool = False

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def ref(self) -> str:
        if self.folder == "wiki":
            return self.stem
        return f"{self.folder}/{self.stem}"

    @property
    def id_(self) -> int | None:
        raw = self.fm.get("id")
        if isinstance(raw, int) and not isinstance(raw, bool):
            return raw
        return None

    @property
    def status(self) -> str | None:
        return _str(self.fm.get("status"))

    @property
    def kind(self) -> str | None:
        if self.folder == "wiki":
            return _str(self.fm.get("type"))
        return _str(self.fm.get("kind"))

    @property
    def title(self) -> str | None:
        return _str(self.fm.get("title"))

    @property
    def updated(self) -> str | None:
        return _date_str(self.fm.get("updated"))

    @property
    def created(self) -> str | None:
        return _date_str(self.fm.get("created"))

    @property
    def labels(self) -> list[str]:
        # Schema uses `labels:` on usecase/task/review/idea and
        # `tags:` on spec/spark. Treat them as one logical field.
        return _str_list(self.fm.get("labels")) + _str_list(self.fm.get("tags"))

    @property
    def milestone(self) -> str | None:
        return _str(self.fm.get("milestone"))


def _str(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    s = v.strip()
    return s or None


def _str_list(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for x in v:
        if isinstance(x, str):
            s = x.strip()
            if s:
                out.append(s)
    return out


def _date_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    s = str(v).strip()
    return s or None


def _parse_iso(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _bare_ref(ref: str) -> str:
    """Strip a leading `<folder>/` prefix so cross-form comparisons work."""
    if "/" in ref:
        return ref.split("/", 1)[1]
    return ref


def discover(a4_dir: Path, include_archived: bool) -> list[Record]:
    out: list[Record] = []

    for kind in WIKI_KINDS_TUPLE:
        path = a4_dir / f"{kind}.md"
        if path.is_file():
            fm = extract_preamble(path).fm or {}
            out.append(Record(folder="wiki", path=path, fm=fm))

    for folder in ISSUE_FOLDERS:
        for md in iter_issue_files(a4_dir, folder):
            fm = extract_preamble(md).fm or {}
            out.append(Record(folder=folder, path=md, fm=fm))

    spark_dir = a4_dir / "spark"
    if spark_dir.is_dir():
        for md in sorted(spark_dir.glob("*.md")):
            fm = extract_preamble(md).fm or {}
            out.append(Record(folder="spark", path=md, fm=fm))

    if include_archived:
        archive_dir = a4_dir / "archive"
        if archive_dir.is_dir():
            for md in sorted(archive_dir.glob("*.md")):
                fm = extract_preamble(md).fm or {}
                out.append(Record(folder="archive", path=md, fm=fm, archived=True))

    return out


def _matches_references(record: Record, target: str, field_name: str | None) -> bool:
    """True if `record` has a forward-relation field pointing at `target`.

    `target` is a normalized reference. Comparison is tolerant of the
    folder-prefixed (`usecase/3-search-history`) and bare (`3-search-history`)
    forms — both are valid per the path-reference rule, so a back-scan must
    accept either.
    """
    fields = (field_name,) if field_name else FORWARD_FIELDS
    target_bare = _bare_ref(target)

    for f in fields:
        raw = record.fm.get(f)
        entries: list[Any]
        if isinstance(raw, str):
            entries = [raw]
        elif isinstance(raw, list):
            entries = list(raw)
        else:
            continue
        for entry in entries:
            n = normalize_ref(entry)
            if n is None:
                continue
            if n == target or n == target_bare or _bare_ref(n) == target_bare:
                return True
    return False


def _matches_field(fm: dict, name: str, value: str) -> bool:
    """Match an arbitrary frontmatter field by exact value.

    For list-typed fields, any element equal to `value` (after stringify
    + strip) counts. For scalars, the stringified value must match. A
    missing or null field never matches.
    """
    raw = fm.get(name)
    if raw is None:
        return False
    if isinstance(raw, list):
        for x in raw:
            if isinstance(x, str):
                if x.strip() == value:
                    return True
            elif str(x) == value:
                return True
        return False
    if isinstance(raw, str):
        return raw.strip() == value
    return str(raw) == value


def filter_records(
    records: list[Record],
    *,
    folders: list[str] | None,
    statuses: list[str] | None,
    kinds: list[str] | None,
    ids: list[int] | None,
    slug_substr: str | None,
    labels: list[str],
    milestone: str | None,
    updated_since: date | None,
    updated_until: date | None,
    target: str | None,
    wiki_impact: str | None,
    references: str | None,
    references_field: str | None,
    field_filters: list[tuple[str, str]],
    has_fields: list[str],
) -> list[Record]:
    out: list[Record] = []
    for r in records:
        if folders and r.folder not in folders:
            continue
        if statuses and r.status not in statuses:
            continue
        if kinds and r.kind not in kinds:
            continue
        if ids is not None and r.id_ not in ids:
            continue
        if slug_substr and slug_substr not in r.stem:
            continue
        if labels:
            rec_labels = set(r.labels)
            if not all(label in rec_labels for label in labels):
                continue
        if milestone and r.milestone != milestone:
            continue
        if updated_since or updated_until:
            u = r.updated
            if not u:
                continue
            try:
                u_date = _parse_iso(u)
            except ValueError:
                continue
            if updated_since and u_date < updated_since:
                continue
            if updated_until and u_date > updated_until:
                continue
        if target is not None:
            t_raw = r.fm.get("target")
            t_norm = normalize_ref(t_raw) if isinstance(t_raw, str) else None
            if t_norm is None:
                continue
            target_bare = _bare_ref(target)
            t_bare = _bare_ref(t_norm)
            if t_norm != target and t_bare != target_bare:
                continue
        if wiki_impact is not None:
            wi = r.fm.get("wiki_impact")
            if not isinstance(wi, list):
                continue
            wi_norm = {normalize_ref(x) for x in wi if isinstance(x, str)}
            if wiki_impact not in wi_norm:
                continue
        if references is not None:
            if not _matches_references(r, references, references_field):
                continue
        if field_filters:
            if not all(_matches_field(r.fm, n, v) for n, v in field_filters):
                continue
        if has_fields:
            if not all(r.fm.get(n) is not None for n in has_fields):
                continue
        out.append(r)
    return out


def render_text(records: list[Record]) -> str:
    if not records:
        return "(no matches)"
    lines: list[str] = []
    for r in records:
        if r.folder == "wiki":
            lines.append(
                f"{r.stem} | wiki | {r.kind or '—'} | (updated {r.updated or '—'})"
            )
        else:
            status = r.status or "—"
            kind = r.kind or "—"
            title = r.title or r.stem
            ref = r.ref + (" [archived]" if r.archived else "")
            lines.append(f"{ref} | {status} | {kind} | {title}")
    return "\n".join(lines)


PROJECTED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "title",
        "status",
        "kind",
        "updated",
        "created",
        "labels",
        "tags",
        "milestone",
    }
    | set(FORWARD_FIELDS)
)


def render_json(records: list[Record]) -> str:
    out: list[dict] = []
    for r in records:
        item: dict[str, Any] = {
            "ref": r.ref,
            "folder": r.folder,
            "path": str(r.path),
            "id": r.id_,
            "title": r.title,
            "status": r.status,
            "kind": r.kind,
            "updated": r.updated,
            "created": r.created,
            "labels": r.labels,
            "milestone": r.milestone,
            "archived": r.archived,
        }
        for fld in FORWARD_FIELDS:
            v = r.fm.get(fld)
            if isinstance(v, list):
                normalized = [normalize_ref(x) for x in v if isinstance(x, str)]
                normalized = [x for x in normalized if x]
                if normalized:
                    item[fld] = normalized
            elif isinstance(v, str):
                n = normalize_ref(v)
                if n:
                    item[fld] = n
        # Surface any custom / unknown frontmatter fields verbatim so the
        # caller can see fields they searched on (or fields they did not
        # know existed). Date objects are stringified for JSON safety.
        extra: dict[str, Any] = {}
        for k, v in r.fm.items():
            if k in PROJECTED_FIELDS:
                continue
            extra[k] = _json_safe(v)
        if extra:
            item["extra"] = extra
        out.append(item)
    return json.dumps(out, indent=2, ensure_ascii=False)


def _json_safe(v: Any) -> Any:
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10] if isinstance(v, date) and not isinstance(v, datetime) else v.isoformat()
    if isinstance(v, list):
        return [_json_safe(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _json_safe(val) for k, val in v.items()}
    return v


def _validate_status(value: str, allowed_folders: list[str] | None) -> None:
    if allowed_folders:
        permitted: set[str] = set()
        for f in allowed_folders:
            permitted |= STATUS_BY_FOLDER.get(f, set())
        if value not in permitted:
            raise SystemExit(
                f"Error: --status {value!r} is not valid for "
                f"--folder {','.join(allowed_folders)}. "
                f"Allowed: {sorted(permitted)}"
            )
        return
    union: set[str] = set()
    for v in STATUS_BY_FOLDER.values():
        union |= v
    if value not in union:
        raise SystemExit(
            f"Error: --status {value!r} is not a known status value. "
            f"Allowed: {sorted(union)}"
        )


def _validate_kind(value: str, allowed_folders: list[str] | None) -> None:
    if allowed_folders:
        permitted: set[str] = set()
        for f in allowed_folders:
            permitted |= KIND_BY_FOLDER.get(f, set())
        if value not in permitted:
            raise SystemExit(
                f"Error: --kind {value!r} is not valid for "
                f"--folder {','.join(allowed_folders)}. "
                f"Allowed: {sorted(permitted)}"
            )
        return
    union: set[str] = set()
    for v in KIND_BY_FOLDER.values():
        union |= v
    if value not in union:
        raise SystemExit(
            f"Error: --kind {value!r} is not a known kind value. "
            f"Allowed: {sorted(union)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter a4/ workspace files by frontmatter fields.",
    )
    parser.add_argument("a4_dir", type=Path, help="path to the a4/ workspace")
    parser.add_argument(
        "--folder",
        action="append",
        default=[],
        choices=ALL_FOLDERS,
        help="restrict to one or more folders (repeat to OR)",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="restrict to one or more status values (repeat to OR)",
    )
    parser.add_argument(
        "--kind",
        action="append",
        default=[],
        help="restrict to one or more kind values (repeat to OR)",
    )
    parser.add_argument(
        "--id",
        action="append",
        type=int,
        default=[],
        help="restrict to one or more numeric ids (repeat to OR)",
    )
    parser.add_argument(
        "--slug",
        help="case-sensitive substring match on the file stem",
    )
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        help="require this label/tag (repeat → AND across labels; matches both `labels:` and `tags:`)",
    )
    parser.add_argument(
        "--milestone",
        help="exact milestone-name match",
    )
    parser.add_argument(
        "--updated-since",
        help="only items with updated >= YYYY-MM-DD",
    )
    parser.add_argument(
        "--updated-until",
        help="only items with updated <= YYYY-MM-DD",
    )
    parser.add_argument(
        "--target",
        help="match review.target against this reference",
    )
    parser.add_argument(
        "--wiki-impact",
        help="bare wiki basename present in wiki_impact (e.g. architecture)",
    )
    parser.add_argument(
        "--references",
        help="find issues whose forward relation fields point at this target",
    )
    parser.add_argument(
        "--references-via",
        choices=FORWARD_FIELDS,
        help="restrict --references back-scan to a single forward field",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="exact match on any frontmatter field (list values: any element matches; repeat → AND)",
    )
    parser.add_argument(
        "--has-field",
        action="append",
        default=[],
        metavar="NAME",
        help="require this frontmatter field to be present and non-null (repeat → AND)",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="also scan a4/archive/ (auto-enabled when --folder archive is requested)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit structured JSON to stdout (default: one-line text)",
    )
    args = parser.parse_args()

    a4_dir = args.a4_dir.resolve()
    if not a4_dir.is_dir():
        print(f"Error: {a4_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    folders = list(args.folder) or None
    for s in args.status:
        _validate_status(s, folders)
    for k in args.kind:
        _validate_kind(k, folders)

    if args.references_via and not args.references:
        print(
            "Error: --references-via requires --references",
            file=sys.stderr,
        )
        sys.exit(2)

    field_filters: list[tuple[str, str]] = []
    for spec in args.field:
        if "=" not in spec:
            print(
                f"Error: --field expects NAME=VALUE; got {spec!r}",
                file=sys.stderr,
            )
            sys.exit(2)
        name, _, value = spec.partition("=")
        name = name.strip()
        if not name:
            print(f"Error: --field name must be non-empty: {spec!r}", file=sys.stderr)
            sys.exit(2)
        field_filters.append((name, value))

    try:
        updated_since = _parse_iso(args.updated_since) if args.updated_since else None
        updated_until = _parse_iso(args.updated_until) if args.updated_until else None
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    target = normalize_ref(args.target) if args.target else None
    wiki_impact = normalize_ref(args.wiki_impact) if args.wiki_impact else None
    references = normalize_ref(args.references) if args.references else None

    include_archived = args.include_archived or (
        folders is not None and "archive" in folders
    )

    records = discover(a4_dir, include_archived=include_archived)

    matched = filter_records(
        records,
        folders=folders,
        statuses=list(args.status) or None,
        kinds=list(args.kind) or None,
        ids=list(args.id) or None,
        slug_substr=args.slug,
        labels=list(args.label),
        milestone=args.milestone,
        updated_since=updated_since,
        updated_until=updated_until,
        target=target,
        wiki_impact=wiki_impact,
        references=references,
        references_field=args.references_via,
        field_filters=field_filters,
        has_fields=list(args.has_field),
    )

    if args.json:
        print(render_json(matched))
    else:
        print(render_text(matched))


if __name__ == "__main__":
    main()
