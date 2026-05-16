# GitHub Issue Relationships

Provider-specific relationship rules for workflow issue artifacts stored as GitHub Issues.

Read with `../common/issue-authoring.md`, `./github-issue-convention.md`.

## Boundary

Issue relationships are not issue metadata fields. Do not store parent, child, dependency, or related issue state in provider metadata fields or issue body fallbacks when native storage is available.

Use GitHub-native relationships when available:

- Parent and child relationships use GitHub sub-issue metadata.
- Blocking relationships use GitHub issue dependency metadata.
- Soft related references use the artifact-specific body section only when no native relationship is available or when the relationship is intentionally human-readable context.

## Relationship intents

When asking `workflow-operator` to apply a GitHub Issue relationship, provide the source issue, canonical relationship intent, and target issue reference.

Use these canonical intents:

- `parent`: the source issue becomes a sub-issue of the target issue.
- `blocked_by`: the source issue is blocked by the target issue.

If the natural wording is "source has child target", invert the source and target and use `parent`. If the natural wording is "source blocks target", invert the source and target and use `blocked_by`.

Use same-repository GitHub issue references such as `#66` for targets.

GitHub provider-native writes do not support a generic `related` relationship. Use an artifact-specific body section only when the relationship is intentionally human-readable context.

## Body boundary

Do not duplicate GitHub-native parent, child, or dependency relationships in issue body sections. Read `./github-issue-anti-patterns.md` for forbidden body sections.

Ask `workflow-operator` to apply provider relationship changes. The main assistant should provide relationship intent and target references, not operator internals.
