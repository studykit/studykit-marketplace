# GitHub Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md`, `./github-issue-convention.md`, and `./github-issue-metadata.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, or related issue state in provider metadata fields or issue body fallbacks when native storage is available.

Use GitHub-native relationships when available:

- Parent and child relationships use GitHub sub-issue metadata.
- Blocking relationships use GitHub issue dependency metadata.
- Soft related references use the artifact-specific body section only when no native relationship is available or when the relationship is intentionally human-readable context.

## Body boundary

Do not duplicate GitHub-native parent, child, or dependency relationships in issue body sections. Read `./github-issue-anti-patterns.md` for forbidden body sections.

Ask `workflow-operator` to apply provider/cache relationship changes. The main assistant should use authoring guidance to draft relationship intent, not operator internals.
