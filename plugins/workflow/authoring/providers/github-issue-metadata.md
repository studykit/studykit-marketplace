# GitHub Issue Metadata

Provider-specific metadata rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md` and `./github-issue-convention.md`.

## Semantic metadata mapping

- `type`: use a label matching the workflow type as the portable default. Use GitHub Issue Types only when repository setup explicitly enables them.
- `status`: use a GitHub Issue Field when available. Use a status label such as `workflow/status:<state>` when fields are unavailable.
- `priority` and `tags`: use configured fields or labels.
- `title`: use the GitHub issue title.
- `created_at` and `updated_at`: use GitHub timestamps when reading provider state.

GitHub native `state` is provider lifecycle state, not the workflow `status` field. Treat close reasons as provider metadata unless project configuration maps them into workflow status.

## Authoring boundary

Do not invent body sections to store provider-owned metadata. Ask `workflow-operator` to apply provider/cache metadata changes.

Issue relationships are outside this metadata document. Read `./github-issue-relationships.md` for relationship authoring boundaries.
