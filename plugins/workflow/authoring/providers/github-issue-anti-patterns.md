# GitHub Issue Authoring Anti-Patterns

GitHub Issues can store parent/sub-issue and dependency relationships as provider-native metadata. Do not duplicate those relationships in the issue body.

Read this with:

- `../common/issue-body.md`
- `../common/issue-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-relationships.md`

## Relationship Body Sections

Do not create dedicated relationship sections for GitHub-native parent or
blocking relationships, or narrow semantic reference sections that belong in
`## Related`.

Avoid these sections in GitHub Issue bodies:

- `## Parent`
- `## Children`
- `## Dependencies`
- `## Blocked`
- `## Blocked By`
- `## Blocking`
- `## Target`
- `## Implements`
- `## Follow-Up`

Also avoid equivalent variants such as:

- `## Blockers`
- `## Depends On`
- `## Waiting On`
- blocked-on slots inside `## Resume`

Use provider-native relationships instead:

- Parent and child relationships -> GitHub parent/sub-issue relationships.
- Blocking relationships -> GitHub issue dependency relationships.

If rationale, sequencing, or discussion is useful to humans, write it in a GitHub comment or in the parent issue narrative. Do not duplicate the machine relationship in the child issue body.

## Allowed Body Relationship Sections

This relationship section may still appear when it carries human-readable context:

- `## Related`

Do not use `## Related` as a disguised parent, blocked-by, or sequencing list.

Do not create body sections only to mirror GitHub sub-issues or dependency relationships. In particular:

- Do not add `## Children` only to repeat GitHub sub-issues.
- Do not add `## Target`; use a GitHub dependency relationship or `## Related`.
- Do not add `## Implements`; use `## Related`.
- Do not add `## Follow-Up`; use `## Related`.
- Do not use `## Related` for blockers, parent issues, dependencies, or sequencing constraints.

## Work History Body Sections

Do not create `## Log` for GitHub Issue work history. Use GitHub comments for human-readable notes and timeline/events for audit history.
