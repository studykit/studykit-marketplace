# GitHub Issue Metadata

Provider-specific metadata rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md` and `./github-issue-convention.md`.

## Issue metadata

- `type`: use a label matching the workflow type as the portable default. Use GitHub Issue Types only when repository setup explicitly enables them.
- `priority` and `tags`: use configured fields or labels.
- `title`: use the GitHub issue title.
- `created_at` and `updated_at`: use GitHub timestamps when reading provider state.

GitHub native `state` is the issue open/closed state. Treat close reasons as provider metadata.

## GitHub Project membership

GitHub Project fields are project-item metadata.

When a cached issue belongs to GitHub Projects, local cache frontmatter should
show the project membership and project-scoped `Status` value together. Do not
treat Project `Status` as intrinsic issue metadata. Use Project `Status` as
workflow status only when the workflow is explicitly bound to a specific
GitHub Project.

## Authoring boundary

Do not invent body sections to store provider-owned metadata. Ask `workflow-operator` to apply provider/cache metadata changes.

Issue relationships are outside this metadata document. Read `./github-issue-relationships.md` for relationship authoring boundaries.
