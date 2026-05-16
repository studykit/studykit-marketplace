# GitHub Knowledge Provider Convention

Provider-wide convention rules for knowledge pages stored as Markdown files under a repository `wiki/` directory.

This is not the separate GitHub Wiki feature. The `wiki/` directory lives in the main repository and participates in normal branch, pull request, review, and CI workflows.

## Scope

Use these rules for knowledge pages stored in GitHub repository Markdown files.

This file defines repository Markdown storage, identity, references, visible links, change-log, and common mistake rules only. Type-specific body structure and page-level guidance belong in the matching GitHub knowledge type authoring file.

## Storage model

The repository knowledge root is:

```text
wiki/
```

Place knowledge pages under `wiki/` according to the project's configured knowledge directory structure.

Do not assume a plugin-specific subdirectory or a fixed page naming pattern in this provider convention.

## Identity and references

Identity is repository-scoped path identity.

Use the repository path as canonical page identity.

Store or resolve:

- Git host.
- Owner.
- Repository.
- Branch or commit when versioned identity is needed.
- Repository-relative path under `wiki/`.

Use normal Markdown links in visible text:

```markdown
[Example Page](wiki/path/to/Example.md)
```

Use full GitHub URLs when text must be portable outside the repository.

## Visible links

Use visible Markdown links when a knowledge page needs to reference related work items or other knowledge pages.

Use Markdown links for citations and repository artifacts.

If a link points to a GitHub Issue, manage issue-native relationships on the issue side when possible and keep the knowledge page link as human-readable context.

Use repository-relative links when the target is in the same repository. Use full URLs when the target is outside the repository or when the text must remain portable.

## Change log

Every material page edit should include a concise `## Change Log` entry that links to the causing work item.

Git commit history records who changed what and when. The page `## Change Log` records why the page changed.

## Common mistakes

- Using the separate GitHub Wiki feature as the knowledge source of truth.
- Duplicating issue discussion in the knowledge page.
- Relying on repository Markdown auto-linking for `#123`; use full links when portability matters.
- Creating a duplicate page outside the configured `wiki/` directory.
