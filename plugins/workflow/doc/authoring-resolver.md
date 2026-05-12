# Workflow Authoring Resolver

Date: 2026-05-13

## Purpose

The authoring resolver decides which plugin-bundled authoring contracts must be read before an agent creates or edits a workflow artifact.

It exists so agents do not infer authoring files from local paths or rely on skill-specific context. The same rule applies to issue providers, knowledge providers, and optional filesystem projections.

## Script

Resolver entry point:

```text
plugins/workflow/scripts/authoring_resolver.py
```

Example:

```bash
python3 plugins/workflow/scripts/authoring_resolver.py \
  --project . \
  --type review \
  --role issue \
  --json
```

The script returns absolute paths.

Example output shape:

```json
{
  "configured": true,
  "config_path": "/repo/workflow.config.yml",
  "artifact": {
    "type": "review",
    "role": "issue",
    "provider": "github"
  },
  "required_authoring_files": [
    "/repo/plugins/workflow/authoring/metadata-contract.md",
    "/repo/plugins/workflow/authoring/body-conventions.md",
    "/repo/plugins/workflow/authoring/issue-body.md",
    "/repo/plugins/workflow/authoring/review-authoring.md",
    "/repo/plugins/workflow/authoring/providers/github-issue-authoring.md"
  ]
}
```

## Resolution inputs

- Artifact type: `task`, `bug`, `spike`, `epic`, `review`, `spec`, `architecture`, `domain`, `context`, `actors`, `nfr`, `ci`, `usecase`, or `research`.
- Role: `issue` or `knowledge`.
- Provider: optional explicit provider override.
- Project path: used to discover `workflow.config.yml`.

Role is inferred for single-role artifact types:

- Issue role: `task`, `bug`, `spike`, `epic`, `review`.
- Knowledge role: `spec`, `architecture`, `domain`, `context`, `actors`, `nfr`, `ci`.

Role must be explicit for dual artifacts:

- `usecase`
- `research`

This prevents accidentally reading issue authoring rules when editing the curated knowledge page, or vice versa.

## Provider inference

When `--provider` is omitted, the resolver looks for `workflow.config.yml` from the project path upward.

Supported config shapes:

```yaml
providers:
  issues:
    kind: github
  knowledge:
    kind: confluence
```

```yaml
source_of_truth:
  issues:
    provider: jira
  knowledge:
    provider: github
```

Explicit `--provider` wins over configuration.

## Required file set

Every resolution includes:

1. `metadata-contract.md`
2. `body-conventions.md`
3. `issue-body.md` or `knowledge-body.md`
4. `<type>-authoring.md`
5. Provider-specific authoring file when available

Provider-specific files:

| Role | Provider | File |
| --- | --- | --- |
| issue | GitHub | `providers/github-issue-authoring.md` |
| issue | Jira | `providers/jira-issue-authoring.md` |
| knowledge | GitHub repository `wiki/` | `providers/github-knowledge-authoring.md` |
| knowledge | Confluence | `providers/confluence-page-authoring.md` |

Filesystem provider support intentionally has no provider-specific authoring file yet.

## SessionStart and write guard integration

SessionStart should only inject the workflow authoring policy when `workflow.config.yml` exists for the current project.

Before writing a workflow artifact:

1. Call the resolver with the artifact type, role, and provider context.
2. Read every returned absolute authoring path.
3. Record the read paths in the session read ledger.
4. Allow the write only if every required path is present in the ledger.

The resolver does not itself record reads or enforce writes. It is the single source for the required file list.

## Current limitations

- No project-local authoring overrides.
- No provider metadata discovery beyond provider kind inference.
- No transport calls.
- No read ledger or write guard implementation yet.
