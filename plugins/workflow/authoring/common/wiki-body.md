# Workflow Knowledge Page Body Conventions

Compatibility document for legacy references to `wiki-body.md`.

New authoring contracts should prefer `./knowledge-body.md`. This file keeps the wiki-page name for compatibility with older references.

Common body rules: `./body-conventions.md`.
Knowledge body rules: `./knowledge-body.md`.

## Knowledge pages are curated

Knowledge pages contain durable reference content, not raw workflow discussion.

Use knowledge pages for:

- Specs.
- Architecture.
- Domain vocabulary.
- Context and actors.
- Non-functional requirements.
- CI and test execution contracts.
- Curated use case summaries.
- Curated research reports.

Use issue-backed artifacts for:

- Task execution.
- Review feedback.
- Discussion and triage.
- Raw investigation notes.
- Work logs.

## `## Change Log`

Every material page edit should include a concise `## Change Log` entry.

Version history records author, timestamp, and diff. The body `## Change Log` records why the page changed and which workflow item caused it.

Format:

```markdown
## Change Log

- 2026-05-13 — #123 — Added checkout actor after use case refinement.
- 2026-05-14 — PROJ-456 — Updated timeout requirement after production incident review.
```

Rules:

- One bullet per material edit.
- New entries are appended in chronological order.
- Link to the causing workflow issue, review item, task, use case workflow issue, or research workflow issue.
- Keep the reason short.
- Do not paste the discussion transcript into the page.

## Update protocol

Update a knowledge page when issue-backed workflow changes affect curated content.

Examples:

- A use case changes actors, flow, or scope.
- A task discovers implementation detail that changes architecture documentation.
- A research item produces a final recommendation.
- A spec supersedes an older decision.
- A review item resolves with a required documentation update.

Update steps:

1. Read the authoring files returned by the authoring resolver.
2. Edit the affected curated section.
3. Add or update visible relationships such as `## Related Work` or `## Supersedes` when needed.
4. Append a `## Change Log` entry with the causing workflow artifact.
5. Use structured metadata when available.

## Deferred updates

If a needed knowledge update cannot be completed immediately, create or update a review item in the issue backend.

The review item should include:

- A target reference to the affected knowledge page, represented according to active issue authoring rules.
- A clear description of the missing or stale content.
- Links to the causing workflow item.

Do not rely on a page comment as the only deferred-work record when the update needs triage, ownership, or lifecycle tracking.

## Cross-references

- `./knowledge-body.md` — canonical knowledge body rules.
- `./body-conventions.md` — common heading and reference rules.
- `./review-authoring.md` — review items for deferred feedback and documentation gaps.
