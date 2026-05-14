# GitHub Issue Spike Authoring

Provider-specific binding for workflow `spike` artifacts stored as GitHub Issues.

Read after:

- `../common/spike-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `spike` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `spike` artifacts.

Common required sections are defined by `../common/spike-authoring.md`:

- `## Description`
- `## Hypothesis`
- `## Validation Method`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/spike-authoring.md` and `../common/body-conventions.md`:

- `## Artifact Links`
- `## Change Plan`
- `## Follow-Up`
- `## Resume`
- `## Why Discarded`

GitHub-specific H2 sections for this type: `## Related`.

GitHub-specific rules:

- Use GitHub issue references or links in `## Follow-Up`.
- Add `## Related` only for soft references that are not follow-up work.
- Do not add dependency body sections.

## Metadata mapping

Recommended GitHub type label: `spike`.

Use GitHub Issue Fields for workflow status when available. If fields are unavailable, use a status label such as `workflow/status:<state>`.

## GitHub-specific section guidance

Use GitHub issue references in `## Follow-Up` when the follow-up work is also tracked in GitHub.

Use `## Related` only for soft references that are not follow-up work, parent work, or blocking dependencies.

## Forbidden body sections

Do not add GitHub-native parent or dependency relationships as body sections. In particular, do not add `## Parent`, `## Dependencies`, `## Blocked`, `## Blocked By`, or `## Blocking`.
