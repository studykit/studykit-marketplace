# GitHub Issues Usage For Workflow

Source issues: [#28](https://github.com/studykit/studykit-plugins/issues/28), [#37](https://github.com/studykit/studykit-plugins/issues/37)

## Purpose

This page records how the workflow plugin uses GitHub Issues when GitHub is the issue backend.

GitHub Issues should be treated as the provider-native source of truth for workflow-heavy artifacts such as tasks, bugs, spikes, epics, reviews, and research workflow items.

## Issue Roles

Workflow uses GitHub Issues for issue-backed artifacts:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- workflow side of `usecase`
- workflow side of `research`

A parent issue can act as a handoff/index issue. The current dogfooding example is [#28](https://github.com/studykit/studykit-plugins/issues/28).

A research issue can track investigation while the curated result lives in repository knowledge pages. The current example is [#37](https://github.com/studykit/studykit-plugins/issues/37).

## Labels

Use plain artifact-type labels for workflow type.

Recommended labels:

- `epic`
- `task`
- `bug`
- `spike`
- `review`
- `research`
- `usecase`

Rules:

- Do not use a `type:` prefix by default.
- Do not require a scope label by default.
- A repository-specific scope label may be configured later when a project needs extra filtering.
- GitHub Issue Types may be supported later when setup explicitly enables them, but labels are the portable default.

Dogfooding examples:

- [#28](https://github.com/studykit/studykit-plugins/issues/28): `epic`
- [#29](https://github.com/studykit/studykit-plugins/issues/29) through [#36](https://github.com/studykit/studykit-plugins/issues/36): `task`
- [#37](https://github.com/studykit/studykit-plugins/issues/37): `research`

## Relationships

Use GitHub native relationships when available.

| Workflow meaning | GitHub representation | Body duplication |
| --- | --- | --- |
| Parent/child | Sub-issues | Do not duplicate as `## Parent` or `## Children`. |
| Soft planning order | Ordered sub-issue list | Do not duplicate as `## Suggested Order`. |
| Hard blocking order | Issue dependencies, `blocked by` / `blocking` | Do not duplicate unless explanation is needed. |
| Soft related link | Issue reference or body link | Use `## Related` when useful. |

Rules:

- Use sub-issues for hierarchy and ownership.
- Use dependencies only when one issue truly cannot proceed before another issue.
- Use sub-issue ordering for preferred work order.
- Keep the body as fallback or explanatory surface, not a duplicate metadata store.

## Body Sections

Issue bodies should contain the current structured summary of the work item.

Use provider comments and history for discussion, work notes, label changes, relationship changes, and audit events.

Recommended sections by case:

### Parent or handoff issue

Use a parent issue as a resumable index when a fresh session needs an entry point.

Recommended sections:

- `## Description`
- `## Scope`
- `## Knowledge Context`
- `## Current Commits`
- `## Acceptance Criteria`
- `## Commit Convention`
- `## Related`
- `## Resume`
- `## How To Resume`

Put `## Resume` and `## How To Resume` near the bottom so the main description stays readable.

Do not add duplicate `## Children` or `## Suggested Order` sections when GitHub relationships already hold that data.

### Review issue

A `review` issue must include a visible `## Target` section.

Example:

```markdown
## Target

- [#29](https://github.com/studykit/studykit-plugins/issues/29)
```

Use metadata or relationships when available, but do not omit the body target.

### Research issue

A `research` issue should keep investigation workflow and link to curated output.

Recommended sections:

- `## Research Question`
- `## Findings`
- `## Curated Result`
- `## Related`

Curated results should live in repository `wiki/` pages or another knowledge backend.

## References

GitHub autolinks issue references in GitHub-native contexts such as issue bodies, comments, pull requests, and commit messages.

Use short references there:

```text
#28
#37
```

Repository Markdown files do not reliably autolink issue references. Use explicit Markdown links in repository docs:

```markdown
[#28](https://github.com/studykit/studykit-plugins/issues/28)
```

This applies to files under:

- `wiki/<plugin>/`
- `plugins/workflow/doc/`
- README files
- other checked-in Markdown documents

## Commit Convention

Use issue-prefixed commit messages for work derived from GitHub Issues.

Examples:

```text
#29 feat(workflow): add config loader
#37 docs(workflow): document github issue usage
```

This keeps `git log --grep="#29"` useful for following a work item's lifecycle.

## History Access

Use provider-native history instead of duplicating routine logs in the body.

| Need | API or command | Notes |
| --- | --- | --- |
| Current body | `gh issue view --json body` | Current description only. |
| Relationship, label, dependency, and timeline events | REST timeline/events APIs | Good for workflow event history. |
| Description/body edit history | GraphQL `userContentEdits` | Provides edit timestamps and diffs. |

See [GitHub Issue History Access](GitHub-Issue-History-Access.md) for details and example commands.

## Current Dogfooding Backlog

The current workflow plugin dogfooding backlog uses GitHub Issues this way:

- Parent/handoff issue: [#28](https://github.com/studykit/studykit-plugins/issues/28)
- Next implementation issue: [#29](https://github.com/studykit/studykit-plugins/issues/29)
- GitHub issue history research: [#37](https://github.com/studykit/studykit-plugins/issues/37)

Sub-issues and dependencies are stored as GitHub native relationships.

## Change Log

- 2026-05-13 — [#37](https://github.com/studykit/studykit-plugins/issues/37) — Published GitHub Issues usage guidance from issue history and relationship research.
