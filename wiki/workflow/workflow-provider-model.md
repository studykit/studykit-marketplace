# Workflow Provider Model

Date: 2026-05-13

## Purpose

This note summarizes the current design direction for `plugins/workflow` as a provider-backed workflow system.

The goal is to let workflow operate over multiple sources of truth:

- Filesystem-backed local Markdown.
- GitHub Issues and repository-backed `wiki/` Markdown directories.
- Jira and Confluence.
- Mixed provider setups, such as GitHub Issues plus Confluence.

## Core Direction

`plugins/workflow` should be a provider-agnostic workflow and semantic layer.

Local Markdown remains a possible projection or future provider, but the workflow plugin is designed around provider-backed sources of truth. When GitHub, Jira, repository-backed `wiki/`, or Confluence are configured as the source of truth, local Markdown files are optional projections rather than required canonical records.

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
- GitHub: GitHub Issues, Projects, and a repository `wiki/` directory for knowledge.
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
.workflow/config.yml
```

Do not use `.a4/` as the primary configuration location. A hidden `.a4/` directory suggests the legacy local a4 workspace or persistent local state, which conflicts with remote-native operation. If ephemeral cache is needed, keep it outside the canonical config path, such as an OS temp directory or an explicit cache directory.

## Recommended Provider Split

workflow should separate work tracking from knowledge management.

```yaml
source_of_truth:
  issues:
    provider: github # github | jira | filesystem
  knowledge:
    provider: confluence # github | confluence | filesystem
```

This supports mixed configurations such as:

- GitHub Issues + repository `wiki/` directory.
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
- GitHub knowledge mode: repository-relative path under `wiki/`.

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

Relationships should be represented in provider metadata when the provider supports suitable native links, custom fields, or page properties.

Provider-native relationship metadata is the source of truth for relationships the provider can store directly. Do not duplicate those relationships in body sections unless the body needs extra explanation.

Examples:

- GitHub parent/child relationships should use native sub-issues, not duplicate `## Parent` or `## Children` body sections.
- GitHub soft planning order should use the ordered sub-issue list, not duplicate `## Suggested Order` body sections.
- GitHub hard blocking relationships should use native issue dependencies.
- Jira issue hierarchy and issue links should use Jira-native relationships when configured.

The body remains the portable fallback for relationships that are not available as provider metadata, or relationships that must be visible to humans and agents.

Example body fallback:

```markdown
## Implements

- [Login Usecase](https://confluence.example.com/pages/123456)
```

The adapter may also store the same relationship as metadata:

```yaml
implements:
  - confluence:123456
```

See `workflow-issue-relationship-policy.md` for the GitHub issue relationship policy used by the workflow MVP backlog.

## GitHub Mapping

### GitHub Issues

GitHub Issues are a good fit for workflow work-tracking artifacts.

Potential mappings:

| Workflow concept | GitHub capability |
| --- | --- |
| Identity | `owner/repo#number` |
| Title and body | Issue title and body |
| Type | Plain artifact-type labels by default, such as `task`; Issue Types only when explicitly configured |
| Scope | Optional repository-specific label only when configured |
| Status | Issue field or Project field |
| Labels | Labels |
| Assignee | Assignees |
| Milestone | Milestone |
| Parent and children | Sub-issues |
| Soft work order | Ordered sub-issue list |
| Dependencies | Issue dependencies |
| Created and updated time | Issue system metadata |
| Work log | Issue comments and timeline events |

Relevant GitHub documentation:

- Issues overview: https://docs.github.com/issues/tracking-your-work-with-issues/about-issues
- Sub-issues: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues
- Labels: https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels
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

- Use labels for workflow artifact type in v1.
- Prefer issue field metadata for canonical workflow status when available.
- Use Project fields for planning views when needed.

Decision:

- GitHub workflow type should use plain artifact-type labels such as `task`.
- GitHub scope labels should not be required by default; setup may configure one for repositories that need extra filtering.
- GitHub Issue Types may be used only when setup explicitly enables them.
- GitHub canonical workflow status should live in an Issue Field when available.
- GitHub Project fields should be used for board, roadmap, and planning views.

Relevant GitHub documentation:

- Projects overview: https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- Projects API: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

### GitHub Repository `wiki/` Directory

A GitHub repository `wiki/` directory is a good fit for Markdown-oriented knowledge pages, including specs. This means a normal directory in the main repository, not the separate GitHub Wiki feature.

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

A repository `wiki/` directory has normal git history, branch review, pull requests, CODEOWNERS, and CI integration. It does not have provider-native page metadata like Confluence, so workflow metadata may need to live in page metadata blocks or an index file under `wiki/<plugin>/`.

Decision:

- Do not use the separate GitHub Wiki feature as the workflow knowledge backend.
- Use `wiki/` in the main repository when GitHub is the knowledge provider.
- Use `wiki/<plugin>/` for plugin-specific knowledge pages in multi-plugin repositories.
- Treat `wiki/<plugin>/<page>.md` as the provider identity for plugin-specific pages.

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

Confluence is likely a better fit than a GitHub repository `wiki/` directory when provider-native metadata and cross-team document collaboration are important.

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
- GitHub repository `wiki/` directory: git history and optional page section.

The workflow normalized view can render a log section from provider-native events.

For GitHub Issues, use REST timeline/events for relationship, label, dependency, and status history. Use GraphQL `userContentEdits` when description/body edit history is required. See `github-issue-history-access.md`.

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
- GitHub repository `wiki/` directory: `git` against the main repository.
- Jira: a REST wrapper.
- Confluence: a REST wrapper.

MCP should be a fallback, not the primary transport. This keeps the provider layer usable from CI, local scripts, and non-Claude runtimes while still allowing MCP-backed operation when native tools or credentials are unavailable.

The wrapper must enforce the same authoring guard regardless of transport. A write through `gh`, `git`, REST, or MCP must all require the resolved authoring files to have been read in the current session.

## Workdoc Finder Agent

`workdoc-finder` is the provider-backed counterpart to `workspace-assistant`.

Purpose:

- Find project work documents and work items in configured providers.
- Search GitHub Issues, Jira issues, repository `wiki/` Markdown pages, and Confluence pages.
- Return compact results with provider refs, URLs, status/type metadata, and short summaries.

Scope:

- Read-only.
- No issue creation or updates.
- No page creation or updates.
- No status transitions.
- No comments or logs.

The agent should read `.workflow/config.yml`, determine configured issue and knowledge providers, then query those providers through workflow wrapper read commands when available. Direct provider tools may be used only as an implementation detail until wrapper read commands exist.

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
5. Issue ID format.
6. Commit reference style.
7. Local projection mode.
8. Provider relationship conventions.

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

issue_id_format: github

local_projection:
  mode: none # none | ephemeral | persistent

commit_refs:
  enabled: true
  style: provider-native
```

The configuration file should be stored at the repository root:

```text
.workflow/config.yml
```

## Authoring Resolver

Workflow authoring rules must still apply when users do not explicitly invoke a workflow skill. SessionStart should therefore inject a small policy in configured workflow projects that tells the main assistant to delegate workflow provider, cache, write-back, comment append, and authoring guard operations to the workflow operator agent.

The workflow operator owns authoring path discovery and provider/cache writes. The resolver is the single entry point for deciding which authoring files apply.

Inputs:

- Artifact type, such as `task`, `review`, `spec`, or `architecture`.
- Artifact role, usually `issue` or `knowledge`.
- Provider, resolved from `.workflow/config.yml` when possible.
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
    "/absolute/path/to/plugins/workflow/authoring/common/issue-body.md",
    "/absolute/path/to/plugins/workflow/authoring/common/issue-authoring.md",
    "/absolute/path/to/plugins/workflow/authoring/common/review-authoring.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-convention.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-relationships.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-review-authoring.md",
    "/absolute/path/to/plugins/workflow/authoring/providers/github-issue-anti-patterns.md"
  ]
}
```

Authoring contracts are plugin-bundled Markdown files only. The resolver must return absolute file paths so the assistant can read the exact files without guessing relative locations. Project-local, repository `wiki/`, or Confluence-hosted authoring overrides are out of scope for v1.

The main assistant should read the returned files before drafting workflow artifacts. Provider writes, cache refresh, and verification remain operator responsibilities.

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
12. Review targets should use provider-native relationships when available; use a human-readable `## Target` body section only when the target is not represented provider-natively.
13. Remote-native configuration should live in `.workflow/config.yml`, not `.a4/`.
14. GitHub workflow type should use plain artifact-type labels; scope labels are optional and GitHub Issue Types are setup-enabled metadata.
15. GitHub canonical status should use Issue Fields when available; Project fields are for planning views.
16. Provider-native relationships and ordering should not be duplicated in the body; body sections are fallback or explanatory surface when provider-native storage is unavailable or insufficient.
17. Knowledge pages should include a concise `## Change Log` linking material edits to their causing workflow artifacts.
18. Authoring contracts are plugin-bundled Markdown files only for v1.
19. The authoring resolver must return absolute paths to required authoring files.
20. The main assistant should read the required authoring files before drafting workflow artifacts.
21. Workflow skills are explicit commands and should not auto-trigger; authoring policy comes from SessionStart guidance, resolver use, and operator-owned writes.
22. Provider writes should go through workflow wrapper commands; native transports are primary and MCP is fallback.
23. Add `workdoc-finder` as a read-only remote provider search agent, separate from `api-researcher`.

## Open Questions

1. What native reference formats should each provider support and normalize?
2. How should repository `wiki/` page metadata be represented: metadata block, index page, or both?
3. How should provider adapters expose validation errors without local files?
4. What is the minimal MCP contract required for each provider?
5. Should setup create provider metadata, or only report missing metadata and ask for confirmation?

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Published curated knowledge page in repository `wiki/` directory.
