# Workflow Configuration

Source document: [`plugins/workflow/doc/workflow-config.md`](../../plugins/workflow/doc/workflow-config.md)

Date: 2026-05-13

## Context

Provider-backed workflow still needs a small repository-local configuration file.

The file declares where issue-backed artifacts and knowledge-backed artifacts live, how optional local projection behaves, and how commit messages should reference provider work items.

The configuration file is:

```text
workflow.config.yml
```

It belongs at the repository root. Do not use `.a4/` as the workflow configuration location.

## Specification

Schema version 1 supports:

- Issue provider.
- Knowledge provider.
- Local projection mode.
- Commit reference style.

Example:

```yaml
version: 1
mode: remote-native

providers:
  issues:
    kind: github
    repo: studykit/studykit-plugins

  knowledge:
    kind: github
    path: wiki/workflow

local_projection:
  mode: none

commit_refs:
  enabled: true
  style: provider-native
```

### Issue Provider

Required path:

```yaml
providers:
  issues:
    kind: github
```

Supported issue provider kinds:

- `github`
- `jira`
- `filesystem`

### Knowledge Provider

Required path:

```yaml
providers:
  knowledge:
    kind: github
```

Supported knowledge provider kinds:

- `github`
- `confluence`
- `filesystem`

When the knowledge provider is `github`, workflow uses the main repository `wiki/` directory, such as `wiki/workflow/`. It does not use GitHub's separate wiki feature.

### Local Projection

Supported local projection modes:

- `none`
- `ephemeral`
- `persistent`

The default is `none`.

### Commit References

Supported commit reference styles:

- `provider-native`
- `issue-prefix`
- `issue-suffix`
- `disabled`

The default is `provider-native`.

When `commit_refs.enabled` is `false`, the loader normalizes the style to `disabled`.

## Provider Aliases

The loader normalizes common provider aliases before validation.

Examples:

- `github-issues`, `github_issue`, and `gh-issue` normalize to `github`.
- `repo-wiki`, `github-wiki`, and `wiki` normalize to `github`.
- `jira-issue` and `jira-issues` normalize to `jira`.
- `confluence-page` and `conf` normalize to `confluence`.
- `fs`, `file`, `files`, and `local` normalize to `filesystem`.

Aliases are still checked against the provider role. `confluence` is invalid for the issue provider, and `jira` is invalid for the knowledge provider.

## Compatibility Shape

The loader accepts the earlier provider split shape:

```yaml
source_of_truth:
  issues:
    provider: jira
  knowledge:
    provider: confluence
```

New configuration files should use `providers`.

## Loader

Shared loader:

```text
plugins/workflow/scripts/workflow_config.py
```

The loader discovers `workflow.config.yml` from the project path upward.

It validates:

- Missing provider slots.
- Provider-role compatibility.
- Local projection mode.
- Commit reference style.
- Schema version.

## Change Log

- 2026-05-13 — [#29](https://github.com/studykit/studykit-plugins/issues/29) — Published the version 1 workflow configuration schema.
