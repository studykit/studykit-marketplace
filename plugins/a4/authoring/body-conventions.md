# a4 Body Conventions

Cross-cutting body-level rules for every file under `a4/`. Covers section heading form and body backlink form.

Frontmatter-side rules: `./frontmatter-common.md` (cross-cutting), `./frontmatter-wiki.md` (wiki minimal), `./frontmatter-issue.md` (issue-side), and the `## Frontmatter` section of each `<type>-authoring.md` (per-type field tables). Type-specific body sections (issue-only or wiki-only) live in the companion file each `<type>-authoring.md` lists alongside this one.

## Scope

Every markdown file inside `a4/`. Each file declares `type:` in frontmatter; recommended body shape per `type:` is documented in per-type contracts under `plugins/a4/authoring/`. The binding form is the markdown heading defined below.

## Section heading form

A body section is an **H2 markdown heading** in Title Case with spaces, followed by free-form markdown until the next H2 (or end of file).

```markdown
## Situation

A meeting just ended; absent teammates need the outcome.

## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.
```

Rules:

- **Section boundary is `## Heading`** — column-0 H2, on its own line. Section ends at next column-0 H2 or EOF.
- **Heading text is Title Case** — each word capitalised, single spaces. Examples: `## Context`, `## Specification`, `## Change Logs`, `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Acceptance Criteria`, `## Why This Matters`. Map kebab-case slugs from per-type contracts to Title Case by replacing hyphens with spaces and capitalising each word.
- **No H1 in the body.** Title belongs to frontmatter `title:`.
- **Sections do not nest.** Every declared section sits at top level; use H3+ for inner structure.
- **Unknown H2 headings are tolerated.** Authors may add supplemental sections (`## Benchmarks`, `## Migration Notes`, …) provided the heading is well-formed Title Case.
- **No stray content above the first section.** Anything in the body that is not whitespace must live under an H2.

## Backlink form (body)

Body cross-references to other `a4/` files are **backtick-wrapped paths** — `` `<relpath>/<file>.md` `` (relative path) or `` `<file>.md` `` (basename, when the target is unambiguous). No `[text](path)` brackets — the backticks are the visual delimiter and parsers extract the path between them. The `.md` extension is retained. The relpath form is computed from the citing file's directory (e.g., from `a4/usecase/3-share-summary.md` to `architecture.md`, write `` `../architecture.md` ``). Obsidian and most editor tooling render code-styled `.md` paths as clickable backlinks; this is the form the a4 plugin standardizes on.

### Inline backlink (in prose)

| Form | Example |
|------|---------|
| Cross-file reference (relpath) | `` `../usecase/3-share-summary.md` `` |
| Cross-file reference (basename) | `` `architecture.md` ``, `` `3-share-summary.md` `` |
| Section anchor on a wiki page | `` `../architecture.md#sessionservice` `` |
| External URL | `[the spec text](https://example.com/spec)` |

External URLs (anything not resolving to an `a4/` file) keep the **standard markdown link** form — `[text](https://...)` — since a bare URL has no display text.

### Bullet backlink (in `## Children`, `## Change Logs`, etc.)

Append-only audit / membership lists use the timestamped-bullet form:

```markdown
- YYYY-MM-DD HH:mm `<relpath>/<file>.md`
```

- The timestamp is `YYYY-MM-DD HH:mm` in KST, matching the `created:` / `updated:` shape (`./frontmatter-common.md`).
- Exactly one space separates timestamp and path; **no em dash** between them.
- The path is backtick-wrapped, either relpath or basename per the inline rule above.
- Optional trailing prose after the closing backtick records annotations (`— moved to ...`, `— discarded ...`, free-form notes).

Plain `#<id>` text (e.g., `see #42 for the rollout plan`) is acceptable in prose. Renders as plain text in local viewers but auto-links as a cross-issue reference in GitHub Issues / PRs when an `a4/` workspace is mirrored. Use it for shorthand mentions; use the backlink form when local navigation matters.

Frontmatter paths are different — plain strings (no brackets, no `.md`) per `./frontmatter-common.md` § Path references.

## Cross-references

- `./<type>-authoring.md` — binding per-type contracts (source of truth for body shape and the per-type field table).
- Body shape is documentation-only; nothing validates section presence at runtime.
