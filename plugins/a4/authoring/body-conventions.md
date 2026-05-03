# a4 Body Conventions

Cross-cutting body-level rules for every file under `a4/`. Covers section heading form and body link form.

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

## Link form (body)

Body cross-references use **standard markdown links** — `[text](relative/path.md)`. The `.md` extension is retained.

| Form | Example |
|------|---------|
| Cross-file reference | `[usecase/3-share-summary](../usecase/3-share-summary.md)` |
| Section anchor on a wiki page | `[architecture#sessionservice](../architecture.md#sessionservice)` |
| Sibling-folder reference | `[research/42-grpc-streaming](../research/42-grpc-streaming.md)` (from `a4/spec/`) |
| External URL | `[the spec text](https://example.com/spec)` |

Plain `#<id>` text (e.g., `see #42 for the rollout plan`) is acceptable in prose. Renders as plain text in local viewers but auto-links as a cross-issue reference in GitHub Issues / PRs when an `a4/` workspace is mirrored. Use it for shorthand mentions; use the markdown-link form when local navigation matters.

Frontmatter paths are different — plain strings (no brackets, no `.md`) per `./frontmatter-common.md` § Path references.

## Cross-references

- `./<type>-authoring.md` — binding per-type contracts (source of truth for body shape and the per-type field table).
- Body shape is documentation-only; nothing validates section presence at runtime.
