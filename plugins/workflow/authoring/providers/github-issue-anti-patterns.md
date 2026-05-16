# GitHub Issue Authoring Anti-Patterns

GitHub Issues can store parent/sub-issue and dependency relationships as provider-native metadata. Do not duplicate those relationships in the issue body.

Read this with:

- `../common/body-conventions.md`
- `../common/issue-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-relationships.md`

## Relationship Body Sections

Do not create dedicated relationship sections for GitHub-native parent or blocking relationships.

Avoid these sections in GitHub Issue bodies:

- `## Parent`
- `## Dependencies`
- `## Blocked`
- `## Blocked By`
- `## Blocking`

Also avoid equivalent variants such as:

- `## Blockers`
- `## Depends On`
- `## Waiting On`
- blocked-on slots inside `## Resume`

Use provider-native metadata instead:

- Parent/child relationships → GitHub parent/sub-issue metadata through the provider wrapper.
- Blocking relationships → GitHub dependency metadata through the provider wrapper.

If rationale, sequencing, or discussion is useful to humans, write it in a GitHub comment or in the parent issue narrative. Do not duplicate the machine relationship in the child issue body.

## Allowed Body Relationship Sections

These relationship sections may still appear when they carry human-readable artifact context:

- `## Target`
- `## Implements`
- `## Related`

Do not use those sections as a disguised parent or blocked-by list.

## Work History Body Sections

Do not create `## Log` for GitHub Issue work history. Use GitHub comments for human-readable notes and timeline/events for audit history.
