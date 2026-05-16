# Jira Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as Jira issues.

Read with `../common/issue-authoring.md`, `./jira-issue-convention.md`, and `./jira-issue-metadata.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, related issue, or remote-link state in provider metadata files.

Use Jira-native relationships when configured:

- Parent and children come from Jira parent/subtask or hierarchy surfaces.
- Dependencies and related issues come from configured Jira issue links.
- Cross-provider references use remote links.

Relationship writes must use explicit `.workflow/config.yml` mappings. Do not infer Jira link type names, directions, remote-link surfaces, or parent fields from issue body prose.

## Body boundary

Use body fallback sections only when configured native relationship storage is unavailable or intentionally insufficient for readers. Do not duplicate native Jira links or remote links in the body.

Ask `workflow-operator` to apply provider/cache relationship changes. The main assistant should use authoring guidance to draft relationship intent, not operator internals.
