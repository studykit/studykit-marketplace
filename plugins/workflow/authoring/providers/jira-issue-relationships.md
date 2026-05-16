# Jira Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as Jira issues.

Read with `../common/issue-authoring.md`, `./jira-issue-convention.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, related issue, or remote-link state in provider-owned metadata.

Use Jira-native relationships when configured:

- Parent and children come from Jira parent/subtask or hierarchy surfaces.
- Dependencies and related issues come from configured Jira issue links.
- Cross-provider references use remote links.

Relationship writes must use explicit `.workflow/config.yml` mappings. Do not infer Jira link type names, directions, remote-link surfaces, or parent fields from issue body prose.

## Relationship intents

When asking `workflow-operator` to apply a Jira relationship, provide the source issue key, canonical relationship intent, and target reference.

Use these canonical intents:

- `parent`: the source issue should be under the target issue in the configured Jira hierarchy surface.
- `blocked_by`: the source issue is blocked by the target issue.
- `related`: the source issue has a configured related-work link to the target.

If the natural wording is "source has child target", invert the source and target and use `parent`. If the natural wording is "source blocks target", invert the source and target and use `blocked_by`.

Use Jira issue keys such as `PROJ-123` for Jira issue targets. Use absolute URLs for remote-link targets.

Jira issue links are site-specific. The selected project configuration must define the link type, direction, hierarchy field, or remote-link binding before `workflow-operator` can apply the relationship.

## Body boundary

Use body fallback sections only when configured native relationship storage is unavailable or intentionally insufficient for readers.

Do not duplicate Jira-native hierarchy, issue links, or remote links in issue body sections. Read `./jira-issue-anti-patterns.md` for forbidden body sections and fallback boundaries.

Ask `workflow-operator` to apply provider relationship changes. The main assistant should provide relationship intent and target references, not operator internals.
