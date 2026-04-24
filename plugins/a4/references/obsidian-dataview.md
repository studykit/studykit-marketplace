# a4 Obsidian Dataview Reference

Canonical dataview query blocks for the `a4/` workspace. Primary audience: skill authors and end users writing dataview blocks into wiki pages, issue bodies, or the INDEX dashboard.

Frontmatter-side rules (which fields are queryable, enum values, path format) live in [frontmatter-schema.md](./frontmatter-schema.md). Body-level wikilink and footnote conventions live in [obsidian-conventions.md](./obsidian-conventions.md). These three documents should be read together.

## Scope

Two families of blocks are documented here:

1. **INDEX.md canonical blocks** — verbatim from `plugins/a4/scripts/index_refresh.py`. The script regenerates `a4/INDEX.md` with these blocks on every compass/index run; each block is paired with a static markdown fallback for non-Obsidian viewers.
2. **Derived views** — dataview blocks for pasting onto individual wiki or issue pages. They compute the reverse direction of the ADR's forward-only relationship model (see [frontmatter-schema.md §Relationships are forward-only](./frontmatter-schema.md)), plus a use-case-diagram source listing.

Vault-layout assumption: the Obsidian vault root is the repo root, so `FROM "a4/usecase"` resolves correctly. If you open `a4/` itself as the vault root instead, strip the `a4/` prefix from every `FROM` clause.

## Keeping the INDEX.md blocks in sync

`plugins/a4/scripts/index_refresh.py` is the authoritative source for the blocks in the first family. If you change a block here, change the matching string literal in `index_refresh.py` (and vice versa). The validator does not police dataview drift; keep the two in step manually.

## INDEX.md canonical blocks

Eight INDEX sections; seven carry a dataview block. **Stage progress** is static-only because it mixes wiki-page presence with cross-folder issue aggregates in a way dataview cannot express in a single block.

### Wiki pages

Selects every root wiki page. `kind` gates the result so non-wiki files don't leak in.

```dataview
TABLE WITHOUT ID file.link AS "Page", kind AS "Kind", updated AS "Updated"
FROM "a4"
WHERE kind
SORT kind ASC
```

### Stage progress — static-only

No dataview block. The section aggregates wiki-page presence with per-folder issue status counts — a mixed-axis view dataview cannot render in a single query. INDEX.md always renders this section as static markdown.

### Open issues

Groups active issues by folder and status. The static fallback additionally pivots `review` items by kind (finding / gap / question); dataview keeps the single-axis grouping so the block stays one query.

```dataview
TABLE WITHOUT ID file.folder AS "Folder", status AS "Status", length(rows) AS "Count"
FROM "a4/usecase" OR "a4/task" OR "a4/review" OR "a4/decision" OR "a4/idea"
WHERE status
GROUP BY file.folder + " · " + status
SORT file.folder ASC
```

### Drift alerts

Unresolved review items created by the drift detector. `drift_detector.py` sets `source: drift-detector` on every item it files.

```dataview
TABLE WITHOUT ID file.link AS "Review", target AS "Wiki", priority AS "Priority", status AS "Status"
FROM "a4/review"
WHERE source = "drift-detector" AND (status = "open" OR status = "in-progress")
SORT priority ASC, updated DESC
```

### Milestones

Task count per milestone. The static fallback adds completion and open-review rollups per milestone; keep the dataview block single-axis for the same reason as Open issues.

```dataview
TABLE WITHOUT ID milestone AS "Milestone", length(rows) AS "Tasks"
FROM "a4/task"
WHERE milestone
GROUP BY milestone
SORT milestone ASC
```

### Recent activity

Top ten items by `updated` date across every issue folder. The `LIMIT 10` matches the `RECENT_ACTIVITY_LIMIT` constant in `index_refresh.py`.

```dataview
TABLE WITHOUT ID file.link AS "Item", file.folder AS "Type", status AS "Status", updated AS "Updated"
FROM "a4/usecase" OR "a4/task" OR "a4/review" OR "a4/decision" OR "a4/idea"
WHERE updated
SORT updated DESC
LIMIT 10
```

### Open ideas

Pre-pipeline quick-capture items (see [frontmatter-schema.md §Idea](./frontmatter-schema.md) and `plugins/a4/spec/2026-04-24-idea-slot.decide.md`). Filter is `status = "open"`; `promoted`/`discarded` are terminal.

```dataview
TABLE WITHOUT ID file.link AS "Idea", status AS "Status", updated AS "Updated"
FROM "a4/idea"
WHERE status = "open"
SORT updated DESC
```

### Spark (open)

Open spark files — brainstorms not yet `promoted`/`discarded`, decides not yet `final`/`superseded`. The script precomputes the exact open-or-not decision for the static fallback; the dataview block uses a coarser `!status OR status = "open" OR status = "draft"` filter.

```dataview
LIST
FROM "a4/spark"
WHERE !status OR status = "open" OR status = "draft"
SORT file.name ASC
```

## Derived views

Per [frontmatter-schema.md §Relationships are forward-only](./frontmatter-schema.md), the schema stores only forward relationships. Reverse directions are computed by dataview on demand. Paste one of the blocks below onto the target page (a use case, task, decision, wiki page, etc.) to surface items pointing at it.

**Path-format placeholder.** Each query uses a literal folder-prefixed path like `"usecase/3-search-history"` as a placeholder; replace it with the current page's path (folder-prefixed, no `.md` extension) when pasting. Using a literal keeps the query self-contained and avoids dataview's path-normalization pitfalls when the vault root and frontmatter path format differ.

### Blocks (reverse of `depends_on`)

Items that declare this page as a dependency. Paste on a use case or task page.

```dataview
TABLE WITHOUT ID file.link AS "Blocked item", file.folder AS "Type", status AS "Status"
FROM "a4/usecase" OR "a4/task"
WHERE contains(depends_on, "usecase/3-search-history")
SORT status ASC, file.name ASC
```

### Implemented by (reverse of `implements`)

Tasks that implement this use case. Paste on a use case page.

```dataview
TABLE WITHOUT ID file.link AS "Task", status AS "Status", milestone AS "Milestone"
FROM "a4/task"
WHERE contains(implements, "usecase/3-search-history")
SORT milestone ASC, file.name ASC
```

### Justifies (reverse of `justified_by`)

Items justified by this decision. Paste on a decision page.

```dataview
TABLE WITHOUT ID file.link AS "Justified item", file.folder AS "Type", status AS "Status"
FROM "a4/usecase" OR "a4/task" OR "a4/review"
WHERE contains(justified_by, "decision/8-caching-strategy")
SORT file.folder ASC, file.name ASC
```

### Superseded by (reverse of `supersedes`)

Decisions (or spark decides) that replace this one. Paste on a decision page or a spark decide.

```dataview
TABLE WITHOUT ID file.link AS "Superseded by", file.folder AS "Type", status AS "Status"
FROM "a4/decision" OR "a4/spark"
WHERE contains(supersedes, "decision/8-caching-strategy")
SORT file.name ASC
```

### Children (reverse of `parent`)

Items declaring this page as their parent. Paste on any issue page.

```dataview
TABLE WITHOUT ID file.link AS "Child", file.folder AS "Type", status AS "Status"
FROM "a4/usecase" OR "a4/task" OR "a4/review" OR "a4/decision"
WHERE contains(parent, "usecase/3-search-history")
SORT file.folder ASC, file.name ASC
```

### Reviews targeting this (reverse of `target`)

Review items whose `target:` points at this page. Paste on any use case, task, decision, or wiki page.

```dataview
TABLE WITHOUT ID file.link AS "Review", kind AS "Kind", status AS "Status", priority AS "Priority"
FROM "a4/review"
WHERE target = "usecase/3-search-history"
SORT priority ASC, status ASC
```

For wiki-page targets, `target:` is a bare basename (e.g., `target: architecture`); use `WHERE target = "architecture"` in that case.

## Use case diagram source

Use-case listing with actors and forward dependencies. Obsidian renders the dataview table directly; downstream tooling can post-process the rows into a mermaid diagram via a dataviewjs block if visual output is needed.

```dataview
TABLE WITHOUT ID file.link AS "Use case", actors AS "Actors", depends_on AS "Depends on", status AS "Status"
FROM "a4/usecase"
WHERE id
SORT id ASC
```

Pure-mermaid rendering from frontmatter requires a dataviewjs block (JavaScript execution must be enabled in Obsidian's dataview settings). Inlining dataviewjs in wiki pages is an authoring choice rather than a project-wide convention, and it is kept out of this reference.

## Cross-references

- [frontmatter-schema.md](./frontmatter-schema.md) — queryable frontmatter fields (enums, types, forward-only relationships).
- [obsidian-conventions.md](./obsidian-conventions.md) — body-level wikilink syntax and footnote audit trail.
- `plugins/a4/scripts/index_refresh.py` — authoritative source for the INDEX.md canonical blocks. Must stay in sync with the first section of this document.
- `plugins/a4/scripts/drift_detector.py` — produces the review items surfaced by the Drift alerts block.
- `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` — ADR, the rationale source.
