# Workflow Body Conventions

Cross-cutting body-level rules for workflow artifacts.

Knowledge body rules: `./knowledge-body.md`.

## Scope

These rules apply to visible artifact body text.

Type-specific authoring files define the required body shape for each artifact type. This file only defines formatting, readability, and reusable section conventions.

## Section heading form

A body section is an H2 Markdown heading in Title Case with spaces, followed by free-form Markdown until the next H2 or end of body.

```markdown
## Situation

A meeting just ended; absent teammates need the outcome.

## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.
```

Rules:

- Section boundary is `## Heading` at column 0, on its own line.
- Heading text is Title Case with single spaces.
- Do not put an H1 in the body when the artifact title is stored separately.
- Use H3 and deeper headings only inside an H2 section.
- Unknown H2 headings are tolerated when they are useful and well-formed.
- Avoid stray content above the first H2 unless the selected artifact template requires a short summary block.

Common H2 names:

- `## Description`
- `## Context`
- `## Specification`
- `## Acceptance Criteria`
- `## Unit Test Strategy`
- `## Sources`
- `## Change Log`
- `## Decision Log`
- `## Open Questions`
- `## Rejected Alternatives`
- `## Resume`
- `## Why Discarded`

## Reference form

Use stable, readable references in body text.

| Target | Preferred body form |
| --- | --- |
| Issue-backed artifact | Issue reference from the selected issue backend |
| Knowledge-backed artifact | Page, document, or file reference from the selected knowledge backend |
| External source | Standard Markdown link |

Examples:

```markdown
## Sources

- [Vendor API documentation](https://example.com/docs)
```

Rules:

- Prefer the shortest reference that is unambiguous in the configured project.
- Use full URLs when a short reference would be ambiguous outside its source system.
- Do not require local Markdown paths for artifacts whose canonical identity is not a local file.
- Do not introduce workflow-local numeric IDs when canonical identity already exists.

## Relationship sections

Relationship body sections are type-specific or backend-specific. Do not invent new relationship sections unless the selected authoring files require them.

Common knowledge relationship sections:

- `## Supersedes` — older knowledge artifact replaced by this one.
- `## Sources` — external evidence, vendor docs, papers, or decision inputs.
- `## Change Log` — semantic cause index on knowledge pages.

## `## Resume`

Purpose: current-state snapshot for a future session.

Use when an artifact is mid-flight and the current state is not obvious from the existing body.

Suggested slots:

- **Approach.** Current strategy.
- **Waiting for.** External input or sequencing note.
- **Open questions.** Questions awaiting input.
- **Next.** Next concrete step.

Rewrite `## Resume` in place. Do not preserve history here.

## `## Why Discarded`

Use when an item is intentionally abandoned and status alone does not explain why.

```markdown
## Why Discarded

- 2026-05-13 10:15 — Superseded by PROJ-456.
```

## Lists and bullets

Use ordinary Markdown lists unless a type-specific contract gives a stricter shape.

Relationship lists should keep one referenced artifact per bullet.

Change-log entries should use this shape:

```markdown
- YYYY-MM-DD — <artifact-ref-or-link> — <concise reason>
```

Example:

```markdown
- 2026-05-13 — PROJ-123 — Updated the latency target after load-test validation.
```

## Comments versus body

Use the body for the current structured artifact.
Use comments, discussions, notes, or history for conversation, progress notes, review conversations, raw investigation notes, and audit facts.

Do not copy long comment threads into the body. Summarize the resulting decision or current state in the relevant body section instead.

## Filesystem projections

If workflow tooling creates local Markdown files as projections of external artifacts, do not treat projection paths as canonical identity.

- Do not use projection paths in commits, branches, or comments unless the local path itself is the topic.
- Projection files may include normalized metadata for tooling, but authoring should still use canonical artifact references.

## Cross-references

- `./issue-authoring.md` — issue-backed artifact rules.
- `./knowledge-body.md` — knowledge-backed body rules.
