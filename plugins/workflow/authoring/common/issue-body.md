# Workflow Issue Body Conventions

Body-level rules for workflow artifacts stored in an issue backend.

Issue-backed artifacts include `task`, `bug`, `spike`, `epic`, `review`, and the workflow issue side of `usecase` and `research`.

## Scope

These rules apply to visible issue body text.

Type-specific authoring files define the required body shape for each artifact type. This file defines issue body formatting, readability, and reusable issue sections.

## Section heading form

An issue body section is an H2 Markdown heading in Title Case with spaces, followed by free-form Markdown until the next H2 or end of body.

```markdown
## Description

A meeting just ended; absent teammates need the outcome.

## Acceptance Criteria

- The summary can be shared with one selected channel.
```

Rules:

- Section boundary is `## Heading` at column 0, on its own line.
- Heading text is Title Case with single spaces.
- Do not put an H1 in the body when the issue title is stored separately.
- Use H3 and deeper headings only inside an H2 section.
- Unknown H2 headings are tolerated when they are useful and well-formed.
- Avoid stray content above the first H2 unless the selected artifact template requires a short summary block.

Common issue H2 names:

- `## Description`
- `## Acceptance Criteria`
- `## Unit Test Strategy`
- `## Open Questions`
- `## Resume`
- `## Why Discarded`

## Reference form

Use stable, readable references in issue body text.

| Target | Preferred body form |
| --- | --- |
| Issue-backed artifact | Issue reference from the selected issue backend |
| Knowledge-backed artifact | Page, document, or file reference from the selected knowledge backend |
| External source | Standard Markdown link |

Rules:

- Prefer the shortest reference that is unambiguous in the configured project.
- Use full URLs when a short reference would be ambiguous outside its source system.
- Do not require local Markdown paths for artifacts whose canonical identity is not a local file.
- Do not introduce workflow-local numeric IDs when canonical identity already exists.

## Relationship body sections

Issue relationship body sections are type-specific or provider-specific. Do not invent new relationship sections unless the selected authoring files require them.

Provider relationship files define which relationships are provider-native and which may appear as visible body context.

## `## Resume`

Purpose: current-state snapshot for a future session.

Use when an issue-backed artifact is mid-flight and the current state is not obvious from the existing body.

Suggested slots:

- **Approach.** Current strategy.
- **Waiting for.** External input or sequencing note.
- **Open questions.** Questions awaiting input.
- **Next.** Next concrete step.

Rewrite `## Resume` in place. Do not preserve history here.

## `## Why Discarded`

Use when an issue is intentionally abandoned and provider status alone does not explain why.

```markdown
## Why Discarded

- 2026-05-13 10:15 — Superseded by PROJ-456.
```

## Lists and bullets

Use ordinary Markdown lists unless a type-specific contract gives a stricter shape.

Relationship lists should keep one referenced artifact per bullet.

## Comments versus body

Use the issue body for the current structured artifact.
Use comments, work notes, discussions, or history for conversation, progress notes, review conversations, raw investigation notes, and audit facts.

Do not copy long comment threads into the body. Summarize the resulting decision or current state in the relevant body section instead.

## Filesystem projections

If workflow tooling creates local Markdown files as projections of external issues, do not treat projection paths as canonical identity.

- Do not use projection paths in commits, branches, or comments unless the local path itself is the topic.
- Do not edit projection metadata as authoring state. Use provider fields through the selected provider workflow, and keep canonical artifact references in visible body text.

## Cross-references

- `./issue-authoring.md` — issue-backed artifact rules.
