# GitHub Knowledge Metadata

Provider-specific metadata rules for workflow knowledge artifacts stored as repository Markdown files.

Read with `../common/knowledge-body.md` and `./github-knowledge-convention.md`.

## Semantic metadata mapping

Repository Markdown files do not provide provider-native page fields.

Recommended metadata surfaces:

1. Git path and git history.
2. Optional Markdown metadata block in the page.
3. Optional index file under `wiki/<plugin>/` when a plugin needs navigation metadata.
4. Optional root `wiki/README.md` as a repository-wide plugin index.

Use optional Markdown metadata only when automation needs it. Do not treat Markdown frontmatter as a separate source of truth from the Git-tracked file.

## Identity and freshness

The repository-relative path is the stable page identity. Git history records who changed what and when. Page `## Change Log` entries record why material changes happened.

Do not create a separate local duplicate for a page that already lives in the repository.

## Relationship metadata

Use visible Markdown links for knowledge relationships. If a relationship points to a GitHub Issue, store structured relationship metadata on the issue side when possible and keep the knowledge page link as human-readable context.
