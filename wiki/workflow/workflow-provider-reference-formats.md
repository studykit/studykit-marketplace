# Workflow Provider Reference Formats

Date: 2026-05-13

## Summary recommendation

`plugins/workflow` should prefer provider-native short references in bodies, commits, branch names, PR titles, and comments. The provider adapter resolves those short references using `.workflow/config.yml`, git remotes, and provider context.

Use full normalized references only when local context is ambiguous or when writing machine-only metadata that needs a stable provider object.

Recommended author-facing references:

- GitHub issue or PR in the configured repository: `#123`.
- GitHub issue or PR in another repository on the same host: `owner/repo#123`.
- GitHub issue or PR outside GitHub-native contexts when ambiguity matters: full URL.
- Jira issue: `PROJ-123`.
- Jira issue in GitHub comments when using GitHub for Atlassian: `[PROJ-123]`.
- Confluence page: page title or Smart Link; use full URL when creating portable text links.
- GitHub repository `wiki/` page: repository-relative Markdown path such as `wiki/workflow/home.md`, or a full GitHub file URL when portability matters.

The adapter should resolve author-facing refs into provider-native identity objects when it needs to call APIs, validate relationships, or write metadata.

Example resolved reference object:

```yaml
input: "#123"
provider: github
kind: issue
authority: github.com
native:
  owner: octo-org
  repo: octo-repo
  number: 123
url: https://github.com/octo-org/octo-repo/issues/123
display: "#123"
```

If a machine-only metadata field needs a compact stable value, use a provider-qualified canonical ref as an escape hatch:

```text
workflowref:github:issue:github.com/octo-org/octo-repo/123
workflowref:jira:issue:acme.atlassian.net/PROJ-123
workflowref:confluence:page:acme.atlassian.net/123456789
```

Do not require users or LLM-authored prose to use `workflowref:`. It is a machine fallback, not the normal writing style.

## Provider-by-provider native formats

### GitHub Issues and Pull Requests

GitHub automatically links issue, pull request, URL, and commit references in GitHub conversations. Native issue and PR forms include full issue or PR URLs, `#123`, `GH-123`, `owner/repo#123`, and `org/repo#123`. GitHub notes that these autolinks are not created in wikis or repository files, so workflow should not rely on `#123` autolinking in GitHub repository `wiki/` pages or checked-in Markdown files. Source: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls

GitHub closing keywords are relevant when workflow writes PR descriptions or commit messages. Supported keyword families are close, fix, and resolve. Same-repository syntax is `KEYWORD #ISSUE-NUMBER`; cross-repository syntax is `KEYWORD OWNER/REPOSITORY#ISSUE-NUMBER`; each issue in a multi-issue close phrase needs its own keyword/reference pair. GitHub only interprets these keywords for PRs targeting the default branch, and commit-message closing takes effect when the commit is merged into the default branch. Source: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue

For API resolution, GitHub's Issues REST API uses `{owner}/{repo}/issues/{issue_number}` and returns issue fields including `id`, `node_id`, `html_url`, and `number`. GitHub documents that a transferred issue may return `301 Moved Permanently` from the old repository endpoint, while deleted or inaccessible issues can return `404` or `410`. Source: https://docs.github.com/en/rest/issues/issues

GitHub GraphQL global node IDs are available as REST `node_id` and GraphQL `id`. GitHub says these IDs are opaque unique strings and should be treated as references rather than decoded. Source: https://docs.github.com/en/graphql/guides/using-global-node-ids and https://docs.github.com/en/graphql/guides/migrating-graphql-global-node-ids

Implications for workflow:

- Resolve `#number` using the configured GitHub provider context.
- The GitHub provider context should come from `.workflow/config.yml` first, then the configured git remote, then `origin`.
- Record `issue_id_format: github` in `.workflow/config.yml` so hooks can use the configured issue ID format when scanning prompts and hook payloads.
- GitHub Enterprise host, owner, and repo can usually be inferred from the git remote URL.
- Store or compute `host`, `owner`, `repo`, `number`, and optionally `node_id` when metadata or API calls need a resolved identity.
- Same-repo body/comment display should be `#number`; cross-repo display should be `owner/repo#number`.
- Use full URLs outside GitHub-native contexts when a short ref would be ambiguous or would not autolink.
- If available, retain `node_id` as a provider opaque ID, but do not make it the only user-visible reference.
- When writing closing relationships, generate provider-native closing keywords only where workflow intentionally wants GitHub auto-close behavior.

### GitHub repository `wiki/` directory pages

When GitHub is the knowledge provider, workflow should use a normal `wiki/` directory in the main repository. Do not use the separate GitHub Wiki feature or `.wiki.git` repository as the workflow knowledge backend. In repositories with multiple plugins, store plugin-specific pages under `wiki/<plugin>/` and keep `wiki/README.md` as the repository-wide index.

A repository `wiki/` page is an ordinary Markdown file, for example:

```text
wiki/workflow/workflow-provider-model.md
```

Implications for workflow:

- Treat `wiki/<plugin>/<page>.md` as a repository file provider object for plugin-specific knowledge.
- Store `host`, `owner`, `repo`, `path`, and optionally branch or commit SHA when versioned identity is needed.
- Use normal Markdown links for visible references, such as `[Provider Model](workflow-provider-model.md)`.
- Use full GitHub file URLs outside repository context.
- Git history is the audit trail for page edits.
- Page `## Change Log` records semantic cause, not the full diff.
- GitHub repository Markdown does not reliably autolink `#123` in every context; use full issue links when portability matters.
- There is no page-level opaque ID comparable to a GitHub issue `node_id`; use repository path plus git history.

Benefits over the separate GitHub Wiki feature:

- Works with normal branches and pull requests.
- Works with code review and CODEOWNERS.
- Can be tested by CI.
- Lives in the same clone as the source code and workflow plugin.
- Avoids separate `.wiki.git` lifecycle and weaker collaboration flow.

### GitHub Projects and issue fields

GitHub Projects and issue fields are relevant for structured metadata, not primary linking identity. GitHub issue fields are organization-level typed metadata that can appear on issues and in projects; they are currently in public preview and only supported in private projects. Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields

Implications for workflow:

- Do not use Project item IDs or issue field IDs as canonical workflow artifact references.
- Use issue fields only as optional synchronization targets for workflow type, status, priority, parent, or dependency metadata when the provider supports them.
- Keep canonical references anchored to the issue or page object, then map fields separately.

### Jira issues

Jira work item keys are the native human reference. Atlassian describes keys as unique identifiers that appear on work items, in search results, boards, links, URLs, and anywhere users need to reference tracked work. Keys consist of a project key plus a sequential number. Project keys must be at least two characters and start with an uppercase letter. Source: https://support.atlassian.com/jira-software-cloud/docs/what-is-a-work-item/

Jira Cloud REST issue APIs identify an issue by ID or key via `issueIdOrKey`. Jira documents that if the supplied identifier does not match directly, Jira may perform a case-insensitive search and check for moved issues, and the returned issue contains the found issue's key. Source: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/

Jira issue links are native relationships between work items. Atlassian documents link types such as `blocks`, `is blocked by`, `relates to`, `implements`, and `is implemented by`, and notes that admins can configure link types. Source: https://support.atlassian.com/jira-software-cloud/docs/link-issues/

Remote issue links are relevant for cross-provider links from Jira to non-Jira artifacts. Atlassian's remote issue link API requires a remote object URL and title, and strongly recommends a `globalId` so the link can later be updated or deleted without relying on Jira's internal remote-link ID. Sources: https://developer.atlassian.com/server/jira/platform/jira-rest-api-for-remote-issue-links/ and https://developer.atlassian.com/server/jira/platform/using-fields-in-remote-issue-links/

Smart Commits are relevant if workflow writes commit messages for Jira-backed work. Atlassian documents the basic syntax as `<ignored text> <ISSUE_KEY> <ignored text> #<COMMAND> <optional COMMAND_ARGUMENTS>`. Source: https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/

Implications for workflow:

- Use `PROJ-123` as the normal author-facing ref.
- Resolve Jira keys using `.workflow/config.yml` provider context, especially the Jira `site`.
- Store or compute `site`, `issue_key`, and optionally immutable numeric `issue_id` when metadata or API calls need a resolved identity.
- Display `issue_key` in commits, branches, PR titles, comments, and page content.
- For GitHub comments with GitHub for Atlassian, use `[PROJ-123]` when a clickable Jira link is desired.
- Use Jira issue links for Jira-to-Jira relationships when configured link types match workflow semantics.
- Use remote links for Jira-to-GitHub, Jira-to-Confluence, or Jira-to-filesystem references. If a `globalId` is needed, derive it from the resolved reference object.

Branch, commit, and PR conventions:

- Branch default: `PROJ-123-some-name`.
- Commit default: `PROJ-123 <summary>`.
- PR title default: `PROJ-123 <summary>`.
- A slash branch pattern such as `PROJ-123/some-name` may work because the key is present, but the default should follow Atlassian's hyphen examples for maximum compatibility.

### Confluence pages

Confluence Cloud REST API v2 identifies pages by numeric/string page `id`; page objects include `title`, `spaceId`, `parentId`, version data, and `_links` such as `webui`, `editui`, and `tinyui`. The page create and update APIs use `spaceId`, `title`, `parentId`, body, and version fields. Source: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/

Confluence supports ordinary links and Smart Links. Atlassian documents that most pasted URLs in a Confluence page or live doc automatically unfurl or convert into Smart Links, and that Smart Links work across Confluence, Jira, and other apps. Sources: https://support.atlassian.com/confluence-cloud/docs/insert-links-and-anchors/ and https://support.atlassian.com/platform-experiences/docs/use-smart-links-to-collaborate-across-products/

Smart Link rendering is permission-sensitive. Atlassian documents that a pasted URL is checked against a domain pattern, and if the domain matches and the user is authenticated, the link can display metadata such as title, last updated date, and preview image. Source: https://support.atlassian.com/platform-experiences/docs/what-data-is-sent-and-received-when-pasting-a-smart-link/

Confluence Data Center documentation says internal Confluence page links are relative, so moves and renames do not break those internal links. This is useful behavior inside Confluence, but an external workflow reference should still retain the page ID because external URLs and titles are easier to change. Source: https://confluence.atlassian.com/doc/links-776656293.html

Implications for workflow:

- Store `site`, `page_id`, `space_id`, `title`, and URLs from `_links`, including `webui` and `tinyui` when available.
- Resolve Confluence pages using configured site and space context.
- Metadata identity should prefer `page_id` scoped by Confluence site.
- Body display should prefer page title or Smart Link, with URL fallback.
- `space + title` is readable but not stable across rename or move; use it as a lookup/display alias, not canonical identity.
- For cross-links to Jira, Confluence's Smart Links are useful display behavior, but workflow should resolve and store the underlying Jira or Confluence identity separately when metadata is available.

## Stability and human-readability tradeoffs

| Provider object | Preferred author-facing ref | Resolved identity for APIs/metadata | Main weakness |
| --- | --- | --- | --- |
| GitHub issue/PR | `#123` in configured repo; `owner/repo#123` cross-repo | host, owner, repo, number, optional `node_id` | `#123` is context-relative. |
| GitHub repository `wiki/` page | `wiki/<plugin>/<page>.md` for plugin-specific pages, or full GitHub file URL | host, owner, repo, path, optional branch/commit | Path changes change identity; no page-level opaque ID. |
| Jira issue | `PROJ-123` | Jira site, key, optional numeric issue ID | Keys are site-scoped; key changes can happen after project moves or renames. |
| Confluence page | Page title or Smart Link | Confluence site, page ID, space ID, URLs | Titles and spaces are readable but rename/move-sensitive. |
| GitHub Project item/field | Project view field name | Project item/field IDs | Useful metadata target, not artifact identity. |

General rule: accept and render native short references for humans. Resolve them with provider context for APIs and metadata. Do not force every provider into an integer workflow ID. Do not treat display references as globally unique without provider authority and site/repository scope.

## Proposed reference handling for workflow

Use raw provider-native references in body sections by default:

```markdown
## Target

- #123
- PROJ-456
- [Auth Session v2](https://acme.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2)
```

When provider metadata supports structured relationships, store a resolved object. The object can be generated from the raw ref and `.workflow/config.yml`.

```yaml
input: "#123"
provider: github
kind: issue
authority: github.com
native:
  owner: octo-org
  repo: octo-repo
  number: 123
  node_id: I_kwDOExample
url: https://github.com/octo-org/octo-repo/issues/123
display: "#123"
title: Add login API
status: open
```

Provider-specific examples:

```yaml
input: "#123"
provider: github
kind: issue
authority: github.com
native:
  owner: octo-org
  repo: octo-repo
  number: 123
  node_id: I_kwDOExample
url: https://github.com/octo-org/octo-repo/issues/123
display: "#123"
```

```yaml
input: "workflow/Home"
provider: github
kind: page
authority: github.com
native:
  owner: octo-org
  repo: octo-repo
  path: wiki/workflow/home.md
  title: Home
  last_seen_commit: abc1234
url: https://github.com/octo-org/octo-repo/blob/main/wiki/workflow/home.md
display: wiki/workflow/home.md
```

```yaml
input: "PROJ-123"
provider: jira
kind: issue
authority: acme.atlassian.net
native:
  key: PROJ-123
  id: "10042"
url: https://acme.atlassian.net/browse/PROJ-123
display: PROJ-123
```

```yaml
input: "Auth Session v2"
provider: confluence
kind: page
authority: acme.atlassian.net
native:
  page_id: "123456789"
  space_id: "98765"
  title: Auth Session v2
  tinyui: /x/AbCdE
  webui: /spaces/ENG/pages/123456789/Auth+Session+v2
url: https://acme.atlassian.net/wiki/spaces/ENG/pages/123456789/Auth+Session+v2
display: Auth Session v2
```

Recommended fields:

- `input`: the author-facing raw ref that was parsed.
- `provider`: `filesystem`, `github`, `jira`, or `confluence`.
- `kind`: provider object kind, such as `issue`, `pull_request`, `page`, `project_item`, or `file`.
- `authority`: host or instance authority, such as `github.com` or `acme.atlassian.net`.
- `native`: provider-native identity fields needed for API resolution.
- `url`: preferred browser URL.
- `display`: provider-native display reference.
- `title`: optional last-known title/summary.
- `status`: optional last-known state/status.
- `aliases`: optional previous keys, previous URLs, old wiki paths, or old titles found during sync.
- `version`: optional provider version marker, such as Confluence page version or wiki commit SHA.
- `ref`: optional machine-only canonical ref, used only where a compact stable metadata key is useful.

Relationship body sections should keep raw provider-native refs. Relationship metadata should use resolved objects when provider capabilities allow. Raw strings should be accepted in user input and normalized by provider-specific parsers.

## Open questions and validation needs

1. Confirm repository `wiki/` path conventions for spaces, Unicode, punctuation, case, and duplicate titles.
2. Decide whether workflow should store GitHub `node_id` for issues as a mandatory field. It is stable and API-friendly, but less portable and less readable than `owner/repo#number`.
4. Validate Jira key-change behavior for moved issues in target Jira Cloud instances. The REST API documents moved issue lookup behavior, but display and Smart Link behavior may vary by instance configuration.
5. Decide which Jira link types map to workflow relationships by default, and how to handle instances where admins rename or remove link types.
6. Confirm Confluence Cloud URL shapes for the target tenant, including whether `tinyui` is consistently present from API v2 and whether public/shared links introduce additional URL forms.
7. Decide whether Confluence `space_id` or space key should be displayed in workflow refs. Space keys are readable; page IDs are more stable.
8. Define parser precedence for ambiguous text such as `ABC-123` in GitHub comments where custom autolinks may also exist.
9. Define how aliases are updated after provider redirects, repository renames, issue transfers, Jira project moves, or page renames.

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Published curated knowledge page in repository `wiki/` directory.
