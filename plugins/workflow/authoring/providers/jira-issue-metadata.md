# Jira Issue Metadata

Provider-specific metadata rules for workflow issue artifacts stored as Jira issues.

Read with `../common/issue-authoring.md` and `./jira-issue-convention.md`.

## Semantic metadata mapping

- `type`: use the configured Jira issue type or project-specific equivalent. Use labels only as fallback or routing metadata.
- `status`: use Jira workflow status.
- `priority`: use Jira priority or a configured priority field.
- `tags`: use Jira labels or configured fields.
- `title`: use Jira summary.
- `created_at` and `updated_at`: use Jira timestamps when reading provider state.

Jira issue types, fields, priorities, and workflow statuses are site-specific. Setup must use `.workflow/config.yml` mappings instead of assuming a global enum.

## Authoring boundary

Do not invent body sections to store provider-owned metadata. Ask `workflow-operator` to apply provider/cache metadata changes.

Issue relationships are outside this metadata document. Read `./jira-issue-relationships.md` for relationship authoring boundaries.
