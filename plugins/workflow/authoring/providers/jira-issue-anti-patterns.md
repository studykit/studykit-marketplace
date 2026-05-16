# Jira Issue Authoring Anti-Patterns

Jira can store hierarchy, issue links, and remote links as provider-native relationships. Do not duplicate those relationships in the issue body.

Read this with:

- `../common/issue-body.md`
- `../common/issue-authoring.md`
- `./jira-issue-convention.md`
- `./jira-issue-relationships.md`

## Relationship Body Sections

Do not create dedicated relationship sections for Jira-native hierarchy, issue
links, or remote links, or narrow semantic reference sections that belong in
`## Related`.

Avoid these sections in Jira issue bodies:

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

- Parent and child relationships -> Jira parent/subtask or configured hierarchy fields.
- Blocking and related relationships -> configured Jira issue links.
- External references -> Jira remote links when configured.

If rationale, sequencing, or discussion is useful to humans, write it in a Jira comment or in the coordinating issue narrative. Do not duplicate the machine relationship in the issue body.

## Body Relationship Fallbacks

These body sections may still appear when the relationship is not stored natively and the section carries human-readable context:

- `## Related`
- `## Dependencies`

Do not use those sections as a disguised parent, child, blocked-by, or sequencing list.

Do not create fallback sections only to mirror Jira issue links, hierarchy, or remote links. In particular:

- Do not add `## Related` only to repeat a Jira issue link or remote link.
- Do not add `## Implements`; use a provider-native relationship or `## Related`.
- Do not add `## Target`; use a provider-native relationship or `## Related`.
- Do not add `## Follow-Up`; use `## Related`.
- Do not use `## Dependencies` for soft related work, parent links, or implementation links.

## Work History Body Sections

Do not create `## Log` for Jira issue work history. Use Jira comments, history, and worklog for discussion and audit history.
