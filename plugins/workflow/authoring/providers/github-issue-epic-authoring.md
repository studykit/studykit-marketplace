# GitHub Issue Epic Authoring

Provider-specific binding for workflow `epic` artifacts stored as GitHub Issues.

Read after:

- `../common/epic-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `epic` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `epic` artifacts.

Common required sections are defined by `../common/epic-authoring.md`:

- `## Description`
- `## Children`

Common optional sections are defined by `../common/epic-authoring.md` and `../common/body-conventions.md`:

- `## Coordination Notes`
- `## Acceptance Criteria`
- `## Related Work`
- `## Resume`
- `## Why Discarded`

GitHub-specific H2 sections for this type: None.

GitHub-specific rules:

- Use GitHub sub-issues for canonical hierarchy when available.
- Keep `## Children` as the readable index.
- Do not add `## Parent` to child issues.

## Metadata mapping

Recommended GitHub type label: `epic`.

Use GitHub Issue Fields for workflow status when available. If fields are unavailable, use a status label such as `workflow/status:<state>`.

## GitHub-specific section guidance

Use GitHub sub-issues for canonical child membership when available.

Keep `## Children` as the readable index for humans. Each child entry should use `#123` or `owner/repo#123` and a short label.

Do not add `## Parent` to child issues. Parent membership belongs in GitHub sub-issue metadata.
