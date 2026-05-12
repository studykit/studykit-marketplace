# Workflow Provider Abstraction Notes

Date: 2026-05-13

## Purpose

This note summarizes the current design direction for `plugins/workflow` as a provider-backed workflow system.

The goal is to let workflow operate over multiple sources of truth:

- Filesystem-backed local Markdown.
- GitHub Issues and GitHub Wiki.
- Jira and Confluence.
- Mixed provider setups, such as GitHub Issues plus Confluence.

## Core Direction

`plugins/workflow` should be a provider-agnostic workflow and semantic layer.

Local Markdown remains a possible projection or future provider, but the workflow plugin is designed around provider-backed sources of truth. When GitHub, Jira, GitHub Wiki, or Confluence are configured as the source of truth, local Markdown files are optional projections rather than required canonical records.

## Terms

### Semantic Model

The workflow semantic model is the shared workflow language:

- Artifact types: `task`, `bug`, `spike`, `research`, `epic`, `review`, `usecase`, `spec`, `architecture`, `domain`, `context`, `actors`, `nfr`, `ci`.
- Relationships: `parent`, `depends_on`, `implements`, `target`, `related`, `supersedes`.
- Workflow concepts: status, lifecycle, logs, review, validation.

This model should stay stable across providers.

### Source of Truth

The source of truth is the provider that owns canonical persistence for an artifact.

Examples:

- Filesystem: local Markdown files under a configured projection path.
- GitHub: GitHub Issues, Projects, and Wiki.
- Atlassian: Jira issues and Confluence pages.

### Local Projection

A local projection is a local representation of remote data.

Projection modes:

- `none`: no local files are generated.
- `ephemeral`: temporary session cache only.
- `persistent`: a local mirror is kept, possibly committed to git.

For GitHub or Jira source-of-truth mode, the default should be `none` or `ephemeral`, not persistent local workflow files.

## Configuration Location

Remote-native mode still needs a repository-local configuration file, even when no local workflow document workspace exists.

Use a root-level config file:

```text
workflow.config.yml
```

Do not use `.a4/` as the primary configuration location. A hidden `.a4/` directory suggests the legacy local a4 workspace or persistent local state, which conflicts with remote-native operation. If ephemeral cache is needed, keep it outside the canonical config path, such as an OS temp directory or an explicit cache directory.

## Recommended Provider Split

workflow should separate work tracking from knowledge management.

```yaml
source_of_truth:
  issues:
    provider: github # github | jira | filesystem
  knowledge:
    provider: confluence # github-wiki | confluence | filesystem
```

This supports mixed configurations such as:

- GitHub Issues + GitHub Wiki.
- Jira + Confluence.
- GitHub Issues + Confluence.
- Filesystem-only.

## Recommended Type Mapping

### Issue Backend

The issue backend should own workflow-heavy artifacts:

- `task`
- `bug`
- `spike`
- `epic`
- `review`

These artifacts need status tracking, assignees, due dates, comments, and work logs.

`review` is always an issue-backed workflow artifact. It represents feedback that must be triaged, tracked, and resolved. Page comments can be useful local discussion aids, but they do not replace workflow review items.

Each review item must identify what it reviewed. The normalized field is `target`, and it may point to issue artifacts, knowledge artifacts, or both. Providers should store `target` as metadata when they support suitable custom fields or links. Every review item should also include a human-readable `## Target` section in the body. If provider metadata is unavailable or unreliable, the body section is the fallback source for target resolution.

### Knowledge Backend

The knowledge backend should own curated documentation:

- `spec`
- `architecture`
- `domain`
- `context`
- `actors`
- `nfr`
- `ci`

These artifacts should contain stable, organized knowledge rather than discussion history.

### Dual Backend Artifacts

`usecase` and `research` should support both an issue artifact and a knowledge artifact.

These artifacts should be issue-first. The issue artifact is always created first so the workflow has a durable place for conversation, questions, status, feedback, and logs. The knowledge artifact is created or updated later when there is curated content worth publishing.

The issue artifact owns:

- Discovery workflow.
- Questions.
- Discussion.
- Assignee and due date.
- Status.
- Work logs.

The knowledge artifact owns:

- Curated summary.
- Agreed content.
- Final research result.
- Stable use case description.
- Links to related tasks and decisions.

This avoids putting raw discussion into the wiki while still preserving the workflow.

Example:

```yaml
type_mapping:
  task:
    issue: primary
  bug:
    issue: primary
  spike:
    issue: primary
  epic:
    issue: primary
  review:
    issue: primary

  spec:
    knowledge: primary
  architecture:
    knowledge: primary
  domain:
    knowledge: primary
  context:
    knowledge: primary
  actors:
    knowledge: primary
  nfr:
    knowledge: primary
  ci:
    knowledge: primary

  usecase:
    issue: workflow
    knowledge: curated
  research:
    issue: workflow
    knowledge: curated
```

## Identity Model

When a remote provider is the source of truth, workflow should not require a local integer `id`.

Recommended identity authority:

- Filesystem mode: local monotonic workflow id.
- GitHub mode: `owner/repo#number`.
- Jira mode: Jira issue key, such as `PROJ-123`.
- Confluence mode: page id, page URL, or stable space/page key.
- GitHub Wiki mode: wiki page path or slug.

Commit messages should use provider-native references:

- GitHub: `feat(auth): add login API (#123)`.
- Jira: `PROJ-123 feat(auth): add login API`.

## Virtual Frontmatter

For remote providers, frontmatter should become a normalized view rather than the storage format.

Example issue view:

```yaml
---
provider: github
kind: issue
key: org/repo#123
type: task
status: progress
title: Add login API
parent: org/repo#100
depends_on:
  - org/repo#98
created_at: 2026-05-13T00:00:00Z
updated_at: 2026-05-13T00:30:00Z
---
```

Example knowledge view:

```yaml
---
provider: confluence
kind: page
key: ENG/Auth Session v2
type: spec
status: active
supersedes:
  - ENG/Auth Session v1
related:
  - org/repo#123
created_at: 2026-05-13T00:00:00Z
updated_at: 2026-05-13T00:30:00Z
---
```

The provider adapter should translate this normalized view to native provider metadata, fields, labels, comments, links, and page properties.

## Relationship Rendering

Relationships such as `target`, `implements`, `related`, and `supersedes` should be represented in provider metadata when the provider supports suitable native links, custom fields, or page properties.

The body must still include a human-readable representation of these relationships. Provider metadata is useful for search, validation, and automation, but the body is the portable fallback that humans and agents can read without provider-specific field access.

Example:

```markdown
## Implements

- [Login Usecase](https://confluence.example.com/pages/123456)
```

The adapter may also store the same relationship as metadata:

```yaml
implements:
  - confluence:123456
```

## GitHub Mapping

### GitHub Issues

GitHub Issues are a good fit for workflow work-tracking artifacts.

Potential mappings:

| Workflow concept | GitHub capability |
| --- | --- |
| Identity | `owner/repo#number` |
| Title and body | Issue title and body |
| Type | Issue type |
| Status | Issue field or Project field |
| Labels | Labels |
| Assignee | Assignees |
| Milestone | Milestone |
| Parent and children | Sub-issues |
| Dependencies | Issue dependencies |
| Created and updated time | Issue system metadata |
| Work log | Issue comments and timeline events |

Relevant GitHub documentation:

- Issues overview: https://docs.github.com/issues/tracking-your-work-with-issues/about-issues
- Sub-issues: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues
- Issue types: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization
- Issue field values API: https://docs.github.com/rest/issues/issue-field-values
- Sub-issues API: https://docs.github.com/en/rest/issues/sub-issues
- Issue dependencies API: https://docs.github.com/en/rest/issues/issue-dependencies
- Issue comments API: https://docs.github.com/en/rest/issues/comments
- Timeline events API: https://docs.github.com/v3/issues/timeline

### GitHub Projects

GitHub Projects are useful for board and planning views.

Potential use:

- Project status board.
- Roadmap view.
- Effort and priority fields.
- Filtering, grouping, and reporting.

Open design question:

- Should workflow status be canonical in an issue field or a project field?

Initial recommendation:

- Prefer issue field metadata for canonical workflow semantics.
- Use Project fields for planning views when needed.

Decision:

- GitHub canonical workflow status should live in an Issue Field when available.
- GitHub Project fields should be used for board, roadmap, and planning views.

Relevant GitHub documentation:

- Projects overview: https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- Projects API: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

### GitHub Wiki

GitHub Wiki is a good fit for Markdown-oriented knowledge pages, including specs.

Recommended knowledge artifacts:

- `spec`
- `architecture`
- `domain`
- `context`
- `actors`
- `nfr`
- `ci`
- Curated `usecase` pages.
- Curated `research` reports.

GitHub Wiki metadata is weaker than issue metadata. If GitHub Wiki is used as a source of truth, workflow metadata may need to live in page frontmatter or in an index page.

Relevant GitHub documentation:

- GitHub Wiki editing: https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages

## Confluence Mapping

Confluence is a strong fit for curated knowledge artifacts.

Recommended artifacts:

- `spec`
- `architecture`
- `domain`
- `context`
- `actors`
- `nfr`
- `ci`
- Curated `usecase` pages.
- Curated `research` reports.

Potential mappings:

| Workflow concept | Confluence capability |
| --- | --- |
| Page identity | Page id, URL, or space/page key |
| Title and body | Page title and content |
| Type | Label or page property |
| Status | Label, page property, or status macro |
| Related items | Page links and Jira issue links |
| Created and updated time | Page system metadata |
| Log | Comments and version history |

Confluence is likely a better fit than GitHub Wiki when provider-native metadata and cross-team document collaboration are important.

## Jira Mapping

Jira is a strong fit for issue workflow.

Recommended artifacts:

- `task`
- `bug`
- `spike`
- `epic`
- `review`
- Workflow side of `usecase`.
- Workflow side of `research`.

Potential mappings:

| Workflow concept | Jira capability |
| --- | --- |
| Identity | Jira issue key |
| Type | Jira issue type |
| Status | Jira workflow status |
| Parent | Parent issue, epic link, or issue hierarchy |
| Dependencies | Issue links |
| Created and updated time | Issue system metadata |
| Work log | Comments, history, and worklog |

Jira workflows and issue types vary by site. The setup flow must discover or ask for mappings instead of assuming a fixed global status model.

## Logs

For remote providers, `## Log` should not be a local-only body section.

Recommended log storage:

- GitHub Issues: comments plus timeline events.
- Jira: comments, history, and worklog.
- Confluence: comments and page version history.
- GitHub Wiki: git history and optional page section.

The workflow normalized view can render a log section from provider-native events.

## Knowledge Page Change Log

Provider history and workflow change logs serve different purposes.

Provider history records audit facts:

- Who changed the page.
- When the page changed.
- What changed.

workflow change logs record semantic cause:

- Why the page changed.
- Which issue, review, use case, research item, or task caused the change.

Every material knowledge-page change should link back to the workflow artifact that caused it. The page should not duplicate the discussion. Long discussion, questions, and work logs belong in the issue backend.

Recommended body section:

```markdown
## Change Log

- 2026-05-13 — [GH #456](https://github.com/org/repo/issues/456) — Clarified async retry boundary.
- 2026-05-14 — [PROJ-123](https://company.atlassian.net/browse/PROJ-123) — Updated latency target.
```

Provider version history remains the audit source. The knowledge page `## Change Log` is the semantic cause index.

## Provider Interfaces

The provider abstraction should separate issue operations from knowledge operations.

```text
IssueProvider
  create_issue()
  update_issue()
  get_issue()
  search_issues()
  list_children()
  set_parent()
  set_dependency()
  append_log()

KnowledgeProvider
  create_page()
  update_page()
  get_page()
  search_pages()
  set_page_metadata()
  link_pages()
  append_comment()
```

Composite artifacts such as `usecase` and `research` need both:

```text
WorkflowCompositeArtifact
  work_item: IssueProvider record
  knowledge_page: KnowledgeProvider record
```

## Provider Transports

Provider operations should go through workflow wrapper commands rather than direct ad-hoc `gh`, `git`, `curl`, or MCP calls from the assistant.

Recommended transport priority:

1. Native wrapper transport.
2. MCP fallback transport.

Native transports:

- GitHub Issues: `gh` and `gh api`.
- GitHub Wiki: `git` against the wiki repository.
- Jira: a REST wrapper.
- Confluence: a REST wrapper.

MCP should be a fallback, not the primary transport. This keeps the provider layer usable from CI, local scripts, and non-Claude runtimes while still allowing MCP-backed operation when native tools or credentials are unavailable.

The wrapper must enforce the same authoring guard regardless of transport. A write through `gh`, `git`, REST, or MCP must all require the resolved authoring files to have been read in the current session.

## Workdoc Finder Agent

`workdoc-finder` is the provider-backed counterpart to `workspace-assistant`.

Purpose:

- Find project work documents and work items in configured providers.
- Search GitHub Issues, Jira issues, GitHub Wiki pages, and Confluence pages.
- Return compact results with provider refs, URLs, status/type metadata, and short summaries.

Scope:

- Read-only.
- No issue creation or updates.
- No page creation or updates.
- No status transitions.
- No comments or logs.

The agent should read `workflow.config.yml`, determine configured issue and knowledge providers, then query those providers through workflow wrapper read commands when available. Direct provider tools may be used only as an implementation detail until wrapper read commands exist.

Relationship to existing agents:

- `workspace-assistant`: local filesystem-backed `a4/` search and snapshots in the legacy a4 plugin.
- `workdoc-finder`: remote provider-backed work document search.
- `api-researcher`: external API and SDK documentation research. Keep this separate.

## Setup Skill Direction

The setup skill should initialize provider choices and conventions.

It should ask or infer:

1. Issue provider.
2. Knowledge provider.
3. Type mapping.
4. Identity authority.
5. Commit reference style.
6. Local projection mode.
7. Provider metadata conventions.

Example configuration:

```yaml
version: 1
mode: remote-native

providers:
  issues:
    kind: github
    repo: org/repo

  knowledge:
    kind: confluence
    site: company.atlassian.net
    space: ENG

local_projection:
  mode: none # none | ephemeral | persistent

commit_refs:
  enabled: true
  style: provider-native
```

The configuration file should be stored at the repository root:

```text
workflow.config.yml
```

## Authoring Resolver and Read Ledger

Workflow authoring rules must still apply when users do not explicitly invoke a workflow skill. SessionStart should therefore inject a small policy in configured workflow projects:

1. Resolve the required authoring contracts before creating or editing any workflow artifact.
2. Read every authoring file returned by the resolver in the current session.
3. Only then write to the issue or knowledge provider.

The resolver is the single entry point for deciding which authoring files apply.

Inputs:

- Artifact type, such as `task`, `review`, `spec`, or `architecture`.
- Artifact role, usually `issue` or `knowledge`.
- Provider, resolved from `workflow.config.yml` when possible.
- Optional local path for filesystem-backed legacy artifacts.

Output:

```json
{
  "artifact": {
    "type": "review",
    "role": "issue",
    "provider": "github"
  },
  "required_authoring_files": [
    "/absolute/path/to/plugins/workflow/authoring/metadata-contract.md",
    "/absolute/path/to/plugins/workflow/authoring/body-conventions.md",
    "/absolute/path/to/plugins/workflow/authoring/issue-body.md",
    "/absolute/path/to/plugins/workflow/authoring/review-authoring.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-authoring.md"
  ]
}
```

Authoring contracts are plugin-bundled Markdown files only. The resolver must return absolute file paths so the assistant can read the exact files without guessing relative locations. Project-local, GitHub Wiki, or Confluence-hosted authoring overrides are out of scope for v1.

The session read ledger records absolute paths of authoring files that were successfully read in the current session.

Example:

```json
{
  "read_authoring_files": [
    "/absolute/path/to/plugins/workflow/authoring/metadata-contract.md",
    "/absolute/path/to/plugins/workflow/authoring/body-conventions.md",
    "/absolute/path/to/plugins/workflow/authoring/issue-body.md",
    "/absolute/path/to/plugins/workflow/authoring/review-authoring.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-authoring.md"
  ]
}
```

Write guards should compare the resolver output with the ledger:

```text
required_authoring_files ⊆ read_authoring_files
```

If any required authoring file has not been read, the write should be denied or delayed with a message that lists the absolute files to read.

This rule applies to local filesystem projection writes and remote provider writes through native wrappers or MCP fallback tools.

## Skill Invocation Policy

Workflow skills are explicit commands, not automatic triggers.

When a user explicitly invokes a workflow skill, the skill may run its workflow and should call the authoring resolver internally before writing artifacts.

When a user does not invoke a skill, the assistant should not auto-start a skill. It should still follow the SessionStart authoring policy and use the resolver before creating or editing workflow artifacts.

This separates workflow convenience from authoring enforcement:

- Skills provide guided workflows when explicitly requested.
- SessionStart and hooks enforce authoring discipline in configured workflow projects.

## Design Decisions So Far

1. Mixed providers are preferred over a single global backend.
2. Issue and knowledge providers should be separate abstractions.
3. GitHub or Jira source-of-truth mode should not require local workflow files.
4. Local files can still exist as optional projections.
5. Remote provider identity should replace local workflow ids when the provider is canonical.
6. Frontmatter should become a normalized view over provider metadata.
7. `spec` belongs in the knowledge backend, not the issue backend.
8. `usecase` and `research` should support dual artifacts and should always create the issue artifact first.
9. Wiki or Confluence pages should contain curated content only.
10. Discussion, questions, and work logs should stay in the issue backend.
11. `review` is always issue-backed because it represents feedback workflow, not page-local commentary.
12. `review.target` should use provider metadata when available, but each review item must also include a human-readable `## Target` body section.
13. Remote-native configuration should live in `workflow.config.yml`, not `.a4/`.
14. GitHub canonical status should use Issue Fields when available; Project fields are for planning views.
15. Relationship fields should always be present in the body and should also be metadata when provider capabilities allow.
16. Knowledge pages should include a concise `## Change Log` linking material edits to their causing workflow artifacts.
17. Authoring contracts are plugin-bundled Markdown files only for v1.
18. The authoring resolver must return absolute paths to required authoring files.
19. A session read ledger should record which required authoring files were actually read before local or remote writes.
20. Workflow skills are explicit commands and should not auto-trigger; authoring enforcement comes from SessionStart policy, resolver use, and write guards.
21. Provider writes should go through workflow wrapper commands; native transports are primary and MCP is fallback.
22. Add `workdoc-finder` as a read-only remote provider search agent, separate from `api-researcher`.

## Open Questions

1. What native reference formats should each provider support and normalize?
2. How should GitHub Wiki page metadata be represented: frontmatter, index page, or both?
3. How should provider adapters expose validation errors without local files?
4. What is the minimal MCP contract required for each provider?
5. Should setup create provider metadata, or only report missing metadata and ask for confirmation?
