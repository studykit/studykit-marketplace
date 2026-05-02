# a4 Body Conventions

Cross-cutting body-level rules that apply to every file under the `a4/` workspace. Covers section heading form, blank-line discipline, and body link form.

Frontmatter-side rules live in `./frontmatter-common.md` (cross-cutting rules: `type:`, path-reference format, empty collections, unknown fields, `created` / `updated`), `./frontmatter-wiki.md` (wiki minimal contract), `./frontmatter-issue.md` (issue-side rules: `id`, title placeholders, relationships, status changes and cascades, structural relationship fields), and the `## Frontmatter` section of each `<type>-authoring.md` (per-type field tables). Type-specific body sections (issue-only or wiki-only) live in the companion file each `<type>-authoring.md` lists alongside this one.

## Scope

Applies to every markdown file inside the `a4/` workspace. Each file declares `type:` in frontmatter; the recommended body shape per `type:` is documented in the per-type authoring contracts under `plugins/a4/authoring/`. The binding form in the file body is the markdown heading defined below.

## Section heading form

A body section is an **H2 markdown heading** in Title Case with spaces, followed by free-form markdown content until the next H2 (or end of file).

```markdown
## Situation

A meeting just ended; absent teammates need the outcome.

## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.
```

Rules:

- **Section boundary is `## Heading`** — column-0 H2, on its own line. The section ends at the next column-0 H2 or end of file.
- **Heading text is Title Case** — each word capitalised, words separated by single spaces. Examples: `## Context`, `## Specification`, `## Change Logs`, `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Acceptance Criteria`, `## Why This Matters`. Map the kebab-case slug from the per-type authoring contract to Title Case by replacing hyphens with spaces and capitalising each word.
- **No H1 in the body.** Title belongs to frontmatter `title:`.
- **Sections do not nest.** Every declared section sits at the body's top level; use H3+ for inner structure.
- **Unknown H2 headings are tolerated.** Authors may add supplemental sections (`## Benchmarks`, `## Migration Notes`, …) provided the heading is well-formed Title Case.
- **No stray content above the first section.** Anything in the body that is not whitespace must live under an H2 heading.

## Link form (body)

Body cross-references use **standard markdown links** — `[text](relative/path.md)`. The `.md` extension is retained.

| Form | Example |
|------|---------|
| Cross-file reference | `[usecase/3-share-summary](../usecase/3-share-summary.md)` |
| Section anchor on a wiki page | `[architecture#sessionservice](../architecture.md#sessionservice)` |
| Sibling-folder reference | `[research/42-grpc-streaming](../research/42-grpc-streaming.md)` (from `a4/spec/`) |
| External URL | `[the spec text](https://example.com/spec)` |

Plain `#<id>` text (e.g., `see #42 for the rollout plan`) is also acceptable in prose. It renders as plain text in local markdown viewers but is auto-linked as a cross-issue reference in GitHub Issues / Pull Requests when an `a4/` workspace is mirrored into a tracker. Use it for shorthand mentions; use the markdown-link form when local navigation matters.

Frontmatter paths are different — they stay plain strings (no brackets, no `.md`) per `./frontmatter-common.md` § Path references.

## Cross-references

- `./<type>-authoring.md` — binding per-type authoring contracts (the source of truth for body shape and the per-type field table).
- Body shape is documentation-only; nothing validates section presence at runtime.
