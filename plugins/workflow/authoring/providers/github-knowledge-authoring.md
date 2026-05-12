# GitHub Knowledge Provider Authoring

Provider binding rules for workflow knowledge artifacts stored as Markdown files under a repository `wiki/` directory.

This is not the separate GitHub Wiki feature. The `wiki/` directory lives in the main repository and participates in normal branch, pull request, review, and CI workflows.

Read with the semantic authoring file for the artifact type, plus:

- `../metadata-contract.md`
- `../knowledge-body.md`

## Scope

Use this binding for knowledge-backed workflow artifacts stored in GitHub repository Markdown files:

- `spec`
- `architecture`
- `domain`
- `context`
- `actors`
- `nfr`
- `ci`
- curated side of `usecase`
- curated side of `research`

## Storage model

The default storage root is:

```text
wiki/
```

Recommended page shape:

```text
wiki/<Page-Title>.md
```

A project may configure a different root later, but v1 should default to `wiki/`.

## Identity and references

Identity is repository-scoped path identity.

Store or resolve:

- Git host.
- Owner.
- Repository.
- Branch or commit when versioned identity is needed.
- Repository-relative path, such as `wiki/Workflow-Provider-Model.md`.

Use normal Markdown links in visible text:

```markdown
[Workflow Provider Model](wiki/Workflow-Provider-Model.md)
```

Use full GitHub URLs when text must be portable outside the repository.

## Metadata

Repository files do not provide provider-native page fields like Confluence.

Use a lightweight Markdown metadata block only when needed for automation. Do not treat local Markdown frontmatter as a separate source of truth from the Git-tracked file; the file content and git history are the source.

Recommended metadata surfaces:

1. Git path and git history.
2. Optional page metadata block in the Markdown file.
3. Optional index file under `wiki/` when a project needs navigation metadata.

## Relationships

Use visible Markdown links for knowledge relationships.

Examples:

```markdown
## Related Work

- [#37](https://github.com/studykit/studykit-plugins/issues/37)
```

```markdown
## Supersedes

- [Auth Session v1](Auth-Session-v1.md)
```

If a relationship points to a GitHub Issue, store the structured relationship on the issue side when possible and keep the knowledge page link as human-readable context.

## Change Log

Every material page edit should include a concise `## Change Log` entry that links to the causing workflow artifact.

Example:

```markdown
## Change Log

- 2026-05-13 — [#37](https://github.com/org/repo/issues/37) — Published GitHub issue history research result.
```

Git commit history records who changed what and when. The page `## Change Log` records why the page changed.

## Transport

Preferred native transport:

- `git` against the main repository.
- `gh` only for issue, pull request, or repository metadata operations.

MCP is fallback transport.

Provider wrapper commands must enforce the authoring resolver/read-ledger guard before writes, regardless of transport.

## Common mistakes

- Using the separate GitHub Wiki feature as the knowledge source of truth.
- Duplicating issue discussion in the knowledge page.
- Relying on repository Markdown auto-linking for `#123`; use full links when portability matters.
- Creating a separate local projection for a page that already lives in `wiki/`.
