# Workflow Configuration

Date: 2026-05-13

## Purpose

`workflow.config.yml` is the repository-local configuration file for the workflow plugin.

The file declares the issue provider, knowledge provider, local projection behavior, and commit reference convention for a project. It stays at the repository root even when issues or knowledge pages are stored in remote providers.

## Location and discovery

The loader searches for this file from the project path upward:

```text
workflow.config.yml
```

Do not store the primary workflow configuration under `.a4/`.

## Schema version 1

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

### `version`

Required schema version.

Supported value:

- `1`

### `mode`

Optional project mode.

Default:

- `remote-native`

The current loader preserves the value after normalization. Provider behavior is controlled by the provider slots.

### `providers.issues`

Required issue provider slot.

Supported provider kinds:

- `github`
- `jira`
- `filesystem`

Common settings:

```yaml
providers:
  issues:
    kind: github
    repo: owner/repo
```

```yaml
providers:
  issues:
    kind: jira
    site: company.atlassian.net
    project: PROJ
```

```yaml
providers:
  issues:
    kind: filesystem
    path: workflow/issues
```

### `providers.knowledge`

Required knowledge provider slot.

Supported provider kinds:

- `github`
- `confluence`
- `filesystem`

For GitHub knowledge, `kind: github` means the repository `wiki/` directory in the main repository. It does not mean GitHub's separate wiki feature.

Common settings:

```yaml
providers:
  knowledge:
    kind: github
    path: wiki/workflow
```

```yaml
providers:
  knowledge:
    kind: confluence
    site: company.atlassian.net
    space: ENG
```

```yaml
providers:
  knowledge:
    kind: filesystem
    path: workflow/knowledge
```

### `local_projection`

Optional local projection behavior.

Supported modes:

- `none`: no local artifact mirror is expected.
- `ephemeral`: temporary session cache only.
- `persistent`: local mirror may be kept and committed.

Default:

```yaml
local_projection:
  mode: none
```

### `commit_refs`

Optional commit reference convention.

Supported styles:

- `provider-native`: use the configured provider's normal reference style.
- `issue-prefix`: prefix the commit subject with the issue reference.
- `issue-suffix`: suffix the commit subject with the issue reference.
- `disabled`: do not enforce commit issue references.

Default:

```yaml
commit_refs:
  enabled: true
  style: provider-native
```

When `enabled` is `false`, the loader normalizes the style to `disabled`.

## Provider aliases

The loader normalizes common aliases before validation.

Examples:

- `github-issues`, `github_issue`, and `gh-issue` normalize to `github`.
- `repo-wiki`, `github-wiki`, and `wiki` normalize to `github`.
- `jira-issue` and `jira-issues` normalize to `jira`.
- `confluence-page` and `conf` normalize to `confluence`.
- `fs`, `file`, `files`, and `local` normalize to `filesystem`.

Provider aliases are still validated against the configured role. For example, `confluence` is invalid for `providers.issues`, and `jira` is invalid for `providers.knowledge`.

## Compatibility shape

The loader also accepts the earlier provider split shape:

```yaml
source_of_truth:
  issues:
    provider: jira
  knowledge:
    provider: confluence
```

Use `providers` for new configs.

## Loader

Shared loader module:

```text
plugins/workflow/scripts/workflow_config.py
```

CLI example:

```bash
python3 plugins/workflow/scripts/workflow_config.py \
  --project . \
  --require \
  --json
```

The loader returns normalized provider kinds and raises validation errors for missing provider slots, invalid provider-role combinations, invalid local projection modes, and invalid commit reference styles.
