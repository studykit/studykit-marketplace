"""Reference resolver for the a4/ workspace.

A frontmatter path reference may take any of these forms:

  - ``<id>`` (YAML integer)           id-only short form (issue families;
                                      a4 v11.0.0+ — replaces ``#<id>``)
  - ``#<id>`` (legacy string)         legacy short form, still accepted
                                      by the resolver for non-FM input
                                      (search, hooks); FM authoring no
                                      longer accepts this form
  - ``<folder>/<id>``                 folder-prefixed, slug omitted
  - ``<folder>/<id>-<slug>``          folder-prefixed, slug present
  - ``<id>-<slug>``                   bare slug-ful (id is global, so unique)
  - ``<wiki-basename>``               wiki page (no id)
  - ``spark/<datetime>-<slug>.brainstorm``  spark file (no id)

All forms are accepted on input. The slug part is a hint — when an id
resolves to a file whose stem differs from the supplied slug, the id
wins and the slug mismatch is silently ignored. This makes references
resilient to slug rename.

Pure library — no stdout / stderr / exit. Builds an in-memory index per
``a4_dir`` and resolves any input form to a single ``ResolvedRef``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common import (
    ISSUE_FOLDERS,
    WIKI_TYPES,
    iter_issue_files,
)
from markdown import extract_preamble


@dataclass(frozen=True)
class ResolvedRef:
    """Canonical resolution of a frontmatter path reference."""

    folder: str         # one of ISSUE_FOLDERS (`usecase`, `task`, `bug`,
                        # `spike`, `research`, `review`, `spec`, `idea`),
                        # or `wiki` / `spark` for the non-issue families
    stem: str           # filename stem without `.md`
    id: int | None      # numeric id when the file has one; None for wiki / spark
    path: Path          # absolute path on disk

    @property
    def canonical(self) -> str:
        """Canonical reference string for comparison.

        Wiki pages use bare basename; everything else uses
        ``<folder>/<stem>``. This matches the schema's preferred forward
        form and is what back-scans compare against.
        """
        if self.folder == "wiki":
            return self.stem
        return f"{self.folder}/{self.stem}"

    @property
    def short(self) -> str | None:
        """Short ``#<id>`` form; None when this entry has no id."""
        return f"#{self.id}" if self.id is not None else None


class RefIndex:
    """In-memory ref → file index for one ``a4_dir`` snapshot.

    Build once per validation pass; resolves are O(1). The index does
    not detect id collisions — that is the frontmatter validator's
    responsibility. When two issue files share an id, ``resolve('#7')``
    returns the first one inserted (issue-folder iteration order), so
    callers should run id-uniqueness validation alongside.
    """

    def __init__(self, a4_dir: Path) -> None:
        self.a4_dir = a4_dir
        self._by_id: dict[int, ResolvedRef] = {}
        self._by_canonical: dict[str, ResolvedRef] = {}
        self._by_folder_id: dict[tuple[str, int], ResolvedRef] = {}
        self._wiki_by_name: dict[str, ResolvedRef] = {}
        self._spark_by_stem: dict[str, ResolvedRef] = {}
        self._build()

    def _build(self) -> None:
        for kind in WIKI_TYPES:
            p = self.a4_dir / f"{kind}.md"
            if p.is_file():
                ref = ResolvedRef(folder="wiki", stem=kind, id=None, path=p)
                self._wiki_by_name[kind] = ref
                self._by_canonical[kind] = ref

        for folder in ISSUE_FOLDERS:
            for p in iter_issue_files(self.a4_dir, folder):
                fm = extract_preamble(p).fm or {}
                raw_id = fm.get("id")
                id_int: int | None
                if isinstance(raw_id, int) and not isinstance(raw_id, bool):
                    id_int = raw_id
                else:
                    id_int = None
                ref = ResolvedRef(folder=folder, stem=p.stem, id=id_int, path=p)
                self._by_canonical[f"{folder}/{p.stem}"] = ref
                if id_int is not None:
                    self._by_id.setdefault(id_int, ref)
                    self._by_folder_id.setdefault((folder, id_int), ref)

        spark_dir = self.a4_dir / "spark"
        if spark_dir.is_dir():
            for p in sorted(spark_dir.glob("*.md")):
                ref = ResolvedRef(folder="spark", stem=p.stem, id=None, path=p)
                self._spark_by_stem[p.stem] = ref
                self._by_canonical[f"spark/{p.stem}"] = ref

    def resolve(self, ref: object) -> ResolvedRef | None:
        """Resolve any supported reference form to its file.

        Returns None when the input is malformed or the target does not
        exist in the workspace.
        """
        if isinstance(ref, bool):
            return None
        if isinstance(ref, int):
            return self._by_id.get(ref) if ref > 0 else None
        if not isinstance(ref, str):
            return None
        s = ref.strip()
        if not s:
            return None
        if s.endswith(".md"):
            s = s[:-3]
        if not s:
            return None

        if s.startswith("#"):
            tail = s[1:]
            if not tail.isdigit():
                return None
            return self._by_id.get(int(tail))

        if s in self._wiki_by_name:
            return self._wiki_by_name[s]

        if s.startswith("spark/"):
            return self._spark_by_stem.get(s[len("spark/"):])

        if "/" in s:
            folder, _, rest = s.partition("/")
            if folder not in ISSUE_FOLDERS:
                return None
            head = rest.split("-", 1)[0] if rest else ""
            if head.isdigit():
                return self._by_folder_id.get((folder, int(head)))
            return self._by_canonical.get(s)

        head = s.split("-", 1)[0]
        if head.isdigit():
            return self._by_id.get(int(head))
        return None

    def canonical(self, ref: object) -> str | None:
        """Canonical reference string for any input form, or None."""
        r = self.resolve(ref)
        return r.canonical if r else None

    def is_id_bearing(self, ref: object) -> bool:
        """True if the input form names an issue (carries or implies an id)."""
        if isinstance(ref, bool):
            return False
        if isinstance(ref, int):
            return ref > 0
        if not isinstance(ref, str):
            return False
        s = ref.strip()
        if not s:
            return False
        if s.endswith(".md"):
            s = s[:-3]
        if s.startswith("#"):
            return s[1:].isdigit()
        if s in self._wiki_by_name:
            return False
        if s.startswith("spark/"):
            return False
        if "/" in s:
            folder, _, rest = s.partition("/")
            if folder not in ISSUE_FOLDERS:
                return False
            head = rest.split("-", 1)[0] if rest else ""
            return head.isdigit()
        head = s.split("-", 1)[0]
        return head.isdigit()
