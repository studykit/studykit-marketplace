# Workflow Issue Relationship Policy

Source document: [`plugins/workflow/doc/issue-relationship-policy.md`](../../plugins/workflow/doc/issue-relationship-policy.md)

Date: 2026-05-13

## Decision

When an issue provider supports native relationships, workflow should use provider-native relationships as the source of truth for those relationships.

Do not duplicate provider-native parent/child relationships in issue body sections.

For GitHub-backed workflow:

- Use GitHub sub-issues for parent/child relationships.
- Use GitHub issue dependencies only for hard blocking relationships.
- Do not use `## Children` in the parent issue body when sub-issues are linked natively.
- Do not use `## Parent` in the child issue body when the parent is linked natively.

The issue body remains the fallback only when a relationship is not available as provider metadata, or when a semantic relationship needs a human-readable explanation.

## Current dogfooding backlog

The workflow MVP backlog is tracked in GitHub Issues:

- Parent: [#28](https://github.com/studykit/studykit-plugins/issues/28)
- Sub-issues: [#29](https://github.com/studykit/studykit-plugins/issues/29), [#30](https://github.com/studykit/studykit-plugins/issues/30), [#31](https://github.com/studykit/studykit-plugins/issues/31), [#32](https://github.com/studykit/studykit-plugins/issues/32), [#33](https://github.com/studykit/studykit-plugins/issues/33), [#34](https://github.com/studykit/studykit-plugins/issues/34), [#35](https://github.com/studykit/studykit-plugins/issues/35), [#36](https://github.com/studykit/studykit-plugins/issues/36), [#37](https://github.com/studykit/studykit-plugins/issues/37)

These are linked with GitHub native sub-issue relationships.

The body of [#28](https://github.com/studykit/studykit-plugins/issues/28) should not maintain duplicate `## Children` or `## Suggested Order` sections.
The bodies of [#29](https://github.com/studykit/studykit-plugins/issues/29) through [#36](https://github.com/studykit/studykit-plugins/issues/36) should not maintain duplicate `## Parent` sections.

Use native relationships to express work order:

- Sub-issue order represents the soft planning order inside the parent issue.
- Issue dependency relationships represent hard blocking order.

Current hard dependency relationships:

- [#30](https://github.com/studykit/studykit-plugins/issues/30) is blocked by [#29](https://github.com/studykit/studykit-plugins/issues/29).
- [#31](https://github.com/studykit/studykit-plugins/issues/31) is blocked by [#30](https://github.com/studykit/studykit-plugins/issues/30).
- [#32](https://github.com/studykit/studykit-plugins/issues/32) is blocked by [#29](https://github.com/studykit/studykit-plugins/issues/29) and [#37](https://github.com/studykit/studykit-plugins/issues/37).
- [#33](https://github.com/studykit/studykit-plugins/issues/33) is blocked by [#29](https://github.com/studykit/studykit-plugins/issues/29).
- [#34](https://github.com/studykit/studykit-plugins/issues/34) is blocked by [#32](https://github.com/studykit/studykit-plugins/issues/32).
- [#35](https://github.com/studykit/studykit-plugins/issues/35) is blocked by [#29](https://github.com/studykit/studykit-plugins/issues/29).
- [#36](https://github.com/studykit/studykit-plugins/issues/36) is blocked by [#31](https://github.com/studykit/studykit-plugins/issues/31), [#32](https://github.com/studykit/studykit-plugins/issues/32), and [#33](https://github.com/studykit/studykit-plugins/issues/33).

These are linked with GitHub native issue dependency relationships.

- [#37](https://github.com/studykit/studykit-plugins/issues/37) is a research item for GitHub issue history APIs.

## Labels and type mapping

GitHub-backed workflow should use labels for workflow artifact type in v1.

Recommended labels:

- `epic` marks workflow epics or parent work items.
- `task` marks workflow implementation tasks.
- Additional artifact-type labels should use the plain type name: `bug`, `spike`, `review`, `usecase`, `research`.

Current dogfooding backlog labels:

- [#28](https://github.com/studykit/studykit-plugins/issues/28): `epic`
- [#29](https://github.com/studykit/studykit-plugins/issues/29) through [#36](https://github.com/studykit/studykit-plugins/issues/36): `task`
- [#37](https://github.com/studykit/studykit-plugins/issues/37): `research`

Do not require a scope label by default. A repository-specific scope label may be configured later when a project needs extra filtering, but the default GitHub mapping should stay close to normal GitHub issue usage.

GitHub Issue Types may be supported later as an optional setup-enabled mapping, but labels are the default because they are portable across repositories.

## Related Guidance

- [GitHub Issues Usage For Workflow](GitHub-Issues-Usage-For-Workflow.md)

## Parent/child relationship

Use parent/child for hierarchy and ownership:

- MVP → implementation tasks.
- Epic → task/bug/spike/review items.
- Large work item → smaller work items.

For GitHub, the native representation is a sub-issue relationship.

Provider wrappers should map workflow `parent` and `children` to GitHub sub-issues when GitHub is the issue provider.

## Work ordering

Workflow should distinguish soft planning order from hard blocking order.

Soft planning order:

- Means the preferred order for humans or agents to pick up work.
- Should use provider-native ordering when available.
- For GitHub, use the ordered sub-issue list under the parent issue.
- Should not be duplicated as a `## Suggested Order` body section when provider ordering is available.

Hard blocking order:

- Means one issue cannot proceed until another issue is completed.
- Should use provider-native dependency relationships when available.
- For GitHub, use `blocked by` / `blocking` issue dependencies.
- May also be explained in the body only when the reason for blocking is not obvious.

## Dependency relationship

Use dependencies only when one issue is truly blocked by another issue.

Do not use dependencies to encode a merely recommended order. If the provider supports ordered sub-issues, use sub-issue ordering for soft planning order. Use dependencies only when work cannot proceed without the other issue.

For GitHub, the native representation is issue dependency metadata.

## Body relationship sections

Workflow authoring still uses body sections for relationships that must be visible to humans and agents.

Keep body sections for relationships such as:

- `## Target` on review items.
- `## Implements` when implementation work points to a use case, spec, or knowledge page.
- `## Related` for soft links that are useful but not native provider relationships.
- `## Dependencies` only when the provider does not support native dependencies or when an explanation is required.

Do not keep body-only duplicates for provider-native parent/child links.

## Provider fallback rule

Relationship storage precedence:

1. Provider-native relationship metadata when supported.
2. Body section when provider metadata is unavailable or insufficient.
3. Normalized adapter view generated from provider metadata and body fallback.

The adapter should avoid writing duplicate body sections for relationships it can store natively.

## References

- GitHub REST API sub-issues documentation: https://docs.github.com/en/rest/issues/sub-issues
- GitHub REST API issue dependencies documentation: https://docs.github.com/en/rest/issues/issue-dependencies

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Published curated knowledge page in repository `wiki/` directory.
