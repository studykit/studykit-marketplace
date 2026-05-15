# GitHub Knowledge Provider Convention

Provider-wide convention rules for workflow knowledge artifacts stored as Markdown files under a repository `wiki/` directory.

This is not the separate GitHub Wiki feature. The `wiki/` directory lives in the main repository and participates in normal branch, pull request, review, and CI workflows.

## Scope

Use these rules for workflow knowledge artifacts stored in GitHub repository Markdown files.

This file defines repository Markdown storage, identity, reference, metadata, relationship, change-log, transport, and common mistake rules only. Artifact-specific body structure and page-level guidance belong in the matching GitHub knowledge type authoring file.

## Storage model

The default repository knowledge root is:

```text
wiki/
```

For plugin-specific knowledge, use a plugin subdirectory by default:

```text
wiki/<plugin>/
```

Recommended page shape:

```text
wiki/<plugin>/<Page-Title>.md
```

A project may configure a different root later, but v1 should default to `wiki/<plugin>/` for plugin repositories and `wiki/` for single-purpose repositories.

## Identity and references

Identity is repository-scoped path identity.

Store or resolve:

- Git host.
- Owner.
- Repository.
- Branch or commit when versioned identity is needed.
- Repository-relative path, such as `wiki/<plugin>/<page>.md`.

Use normal Markdown links in visible text:

```markdown
[Example Page](wiki/<plugin>/<page>.md)
```

Use full GitHub URLs when text must be portable outside the repository.

## Metadata

Repository files do not provide provider-native page fields like Confluence.

Use a lightweight Markdown metadata block only when needed for automation. Do not treat local Markdown frontmatter as a separate source of truth from the Git-tracked file; the file content and git history are the source.

Recommended metadata surfaces:

1. Git path and git history.
2. Optional page metadata block in the Markdown file.
3. Optional index file under `wiki/<plugin>/` when a plugin needs navigation metadata.
4. Optional root `wiki/README.md` as a repository-wide plugin index.

## Relationships

Use visible Markdown links for knowledge relationships.

If a relationship points to a GitHub Issue, store the structured relationship on the issue side when possible and keep the knowledge page link as human-readable context.

Use repository-relative links when the target is in the same repository. Use full URLs when the target is outside the repository or when the text must remain portable.

## Change log

Every material page edit should include a concise `## Change Log` entry that links to the causing workflow artifact.

Git commit history records who changed what and when. The page `## Change Log` records why the page changed.

## Transport

Preferred native transport:

- `git` against the main repository.
- `gh` only for issue, pull request, or repository metadata operations.

MCP is fallback transport.

Provider wrapper commands perform the requested write and verification. The caller is responsible for following the authoring resolver/read policy before invoking a write.

## Common mistakes

- Using the separate GitHub Wiki feature as the knowledge source of truth.
- Duplicating issue discussion in the knowledge page.
- Relying on repository Markdown auto-linking for `#123`; use full links when portability matters.
- Creating a separate local projection for a page that already lives in `wiki/`.
