# Workflow Configuration

Date: 2026-05-13

## Context

Provider-backed workflow still needs a small repository-local configuration file.

The file declares where issue-backed artifacts and knowledge-backed artifacts live, how optional local projection behaves, and how commit messages should reference provider work items.

The configuration file is:

```text
.workflow/config.yml
```

It belongs at the repository root. Do not use `.a4/` as the workflow configuration location.

## Specification

Schema version 1 supports:

- Issue provider.
- Knowledge provider.
- Issue ID format.
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

issue_id_format: github

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

Jira Data Center relationship writes require explicit mappings under
`providers.issues.relationship_mappings`. The wrapper does not infer Jira link
types, directions, remote-link behavior, or parent fields from prose.

Example:

```yaml
providers:
  issues:
    kind: jira
    site: https://jira.example.com
    deployment: data-center
    relationship_mappings:
      blocked_by:
        surface: issue_link
        link_type: Blocks
        direction: inward
      blocking:
        surface: issue_link
        link_type: Blocks
        direction: outward
      related:
        surface: remote_link
        relationship_label: relates to
      parent:
        surface: field
        field: parent
        write_to: source
        value: key
```

Supported Jira relationship surfaces:

- `issue_link`: requires `link_type` and `direction` (`inward` or `outward`).
- `remote_link`: requires an absolute `http` or `https` target reference.
- `field`: requires `field`, `write_to` (`source` or `target`), and `value`
  (`key`, `key_object`, or `string`).

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

### Issue ID Format

Supported issue ID formats:

- `github`
- `jira`
- `number`
- `provider-native`

The default is `provider-native`. The loader resolves `provider-native` to the configured issue provider's native format: `github` for GitHub Issues, `jira` for Jira, and `number` for filesystem-backed issues.

For GitHub-backed projects, hooks use `issue_id_format: github` to scan prompts and stop payloads for same-repository issue references such as `#123`, `owner/repo#123`, and matching GitHub issue URLs.

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

## Canonical Values

The loader accepts only canonical enum values.

Provider kind values are:

- `github`
- `jira`
- `confluence`
- `filesystem`

Use the values documented in each enum section exactly. Aliases such as `github-issues`, `repo-wiki`, `jira-issues`, `confluence-page`, `fs`, `local`, `temporary`, `mirror`, or `provider_native` are invalid.

Provider values are still checked against the provider role. `confluence` is invalid for the issue provider, and `jira` is invalid for the knowledge provider.

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

The loader discovers `.workflow/config.yml` from the project path upward.

It validates:

- Missing provider slots.
- Provider-role compatibility.
- Local projection mode.
- Commit reference style.
- Issue ID format compatibility with the configured issue provider.
- Schema version.

## Change Log

- 2026-05-15 — [#58](https://github.com/studykit/studykit-plugins/issues/58) — Added explicit Jira Data Center relationship write mappings.
- 2026-05-13 — [#29](https://github.com/studykit/studykit-plugins/issues/29) — Published the version 1 workflow configuration schema.
