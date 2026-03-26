---
name: jira-issue
description: Use obsidian-jira-issue plugin fence components and $ji JavaScript API.
argument-hint: <what to create, e.g. "jira-search table for my open issues", "inline issue reference", "dataviewjs sprint chart">
---

# Obsidian Jira Issue Reference

Generate or assist with obsidian-jira-issue plugin usage for: **$ARGUMENTS**

## Overview

The obsidian-jira-issue plugin integrates Jira with Obsidian, providing fence-based components for displaying issues and an API for programmatic access. It offers two main capabilities:

1. **Fence Components** — Markdown code blocks that render Jira data inline within notes
2. **JavaScript API (`$ji`)** — Programmatic access to Jira data for use with Dataview, Templater, and Obsidian Chart plugins

## Generation Workflow

### Step 1: Analyze Intent

Determine the request category from `$ARGUMENTS`:

| Category | Indicators | Approach |
|----------|-----------|----------|
| Static issue display | "show issues", "list specific tickets", issue keys mentioned | `jira-issue` fence |
| Dynamic query results | "search for", "find issues where", "table of", JQL mentioned | `jira-search` fence |
| Issue counting/metrics | "count", "how many", "number of issues" | `jira-count` fence |
| Inline reference | "mention in text", "inline", "within paragraph" | Inline issue syntax |
| Programmatic/data access | "dataviewjs", "templater", "API", "chart", "sprint data", "worklog" | `$ji` API |

### Step 2: Select Component or API

Apply these decision rules:

1. **Start with fence components.** Most requests for displaying Jira data in notes map to one of the three fence types. Prefer fence components for straightforward display without custom logic.
2. **Escalate to `$ji` API** when the request requires:
   - Dynamic date calculations or conditional logic
   - Combining Jira data with other vault data (Dataview integration)
   - Chart generation (Obsidian Chart integration)
   - Template-based note creation (Templater integration)
   - Sprint/worklog analytics or velocity tracking
3. **Use `$ji.defaulted`** over `$ji.base` when null-safety matters — avoids null checks on missing fields.
4. **Use `$ji.macro`** for sprint and worklog operations — these aggregate multiple API calls internally.

### Step 3: Build and Present

Construct the fence block or API code snippet, then present using the Output Template format below.

## Components Quick Reference

Four fence components and a set of commands are available:

| Component | Fence Type | Purpose |
|-----------|-----------|---------|
| Jira Issue | `` ```jira-issue `` | Display one or more issue references by key or URL |
| Jira Search | `` ```jira-search `` | Table or list view of JQL query results |
| Jira Count | `` ```jira-count `` | Counter of issues matching a JQL query |
| Inline Issue | `JIRA:KEY-123` | Inline issue tag within running text |

### Jira Issue

List issue keys or URLs, one per line. Comments start with `#`:

````
```jira-issue
AAA-111
https://my.jira-server.com/browse/BBB-333
# comment
```
````

### Jira Search

Supports basic (JQL only) and advanced (keyword configuration) modes:

````
```jira-search
type: TABLE
query: status = 'In Progress' order by priority DESC
limit: 15
columns: KEY, SUMMARY, -ASSIGNEE, STATUS, NOTES
account: Default
```
````

**Keywords**: `type` (TABLE/LIST), `query` (JQL), `limit` (integer), `columns` (comma-separated), `account` (alias).

**Column prefixes**: `-` for compact mode, `$` for custom fields (by name or ID). Special `NOTES` column links to vault notes matching the issue key.

For the complete list of standard fields and advanced column options, consult `references/components.md`.

### Jira Count

````
```jira-count
query: status = 'In Progress'
label: Issues to complete
account: Default
```
````

### Inline Issue

Use the inline issue prefix followed by the issue key. The prefix is configurable in the obsidian-jira-issue plugin settings (default: `JIRA:`). Check the user's current prefix setting before generating inline references.

- Extended: `JIRA:OPEN-351`
- Compact: `JIRA:-OPEN-354`
- URL: `https://jira.example.com/browse/OPEN-352`
- Compact URL: `-https://jira.example.com/browse/OPEN-352`

> **Note:** The prefix shown above (`JIRA:`) is the default. The actual prefix depends on the user's Obsidian plugin configuration. When generating inline issue references, confirm the configured prefix with the user if uncertain.

### Commands

Available via Obsidian command palette:
- **Insert issue/search/count template** — Insert component syntax templates
- **Clear cache** — Manually clear cached Jira responses
- **Search wizard** — UI-guided JQL search block builder

## API Quick Reference

Access the API via `$ji` or `this.app.plugins.plugins['obsidian-jira-issue'].api`.

| Module | Key Methods | Purpose |
|--------|------------|---------|
| `$ji.base` | `getIssue`, `getSearchResults`, `getDevStatus`, `getBoards`, `getSprints`, `getLoggedUser` | Direct Jira API access with caching |
| `$ji.defaulted` | `getIssue`, `getSearchResults` | Same as base but missing fields get defaults |
| `$ji.macro` | `getActiveSprint`, `getActiveSprintName`, `getWorkLogBySprint`, `getWorkLogByDates`, `getVelocity`, `getWorkLogSeriesByUser` | High-level sprint and worklog functions |
| `$ji.chart` | `getWorklogPerDay`, `getWorklogPerUser` | Chart-ready worklog data |
| `$ji.account` | `getAccountByAlias`, `getAccountByHost` | Retrieve account settings |
| `$ji.util` | `clearCache` | Clear cached responses |

### Common API Patterns

**Templater — Active Sprint Info:**

```
<%* const projectKey = 'AAA' %>
Sprint: <%* tR += await $ji.macro.getActiveSprintName(projectKey) %>
Start: <%* tR += (await $ji.macro.getActiveSprint(projectKey)).startDate %>
End: <%* tR += (await $ji.macro.getActiveSprint(projectKey)).endDate %>
```

**DataviewJS — Sprint Worklog Chart:**

```dataviewjs
const projectKey = 'AAA'
const sprint = await $ji.macro.getActiveSprint(projectKey)
const chartData = await $ji.chart.getWorklogPerDay(projectKey, sprint.startDate, sprint.endDate)
dv.paragraph(chartData, this.container)
```

**Templater — Loop Search Results:**

```
<%* const results = await $ji.base.getSearchResults(`project = "AAA" AND assignee = currentUser() AND resolution = Unresolved`) %>
<%* for(const issue of results.issues) { %>
## <%* tR += `${issue.key} - ${issue.fields.summary}` %>
<%* } %>
```

For complete API signatures, parameters, return types, and additional examples, consult `references/api.md`.

## Output Template

### For Fence Components

Present fence blocks with the appropriate language tag and an explanation:

````markdown
```jira-search
type: TABLE
query: status = 'In Progress' AND assignee = currentUser() order by priority DESC
limit: 10
columns: KEY, SUMMARY, STATUS, PRIORITY, DUE_DATE
```
````

**Explanation:**
- Describe why this component was chosen (jira-issue vs jira-search vs jira-count)
- Explain the JQL query logic and any keywords used
- Note any column modifiers (`-` for compact, `$` for custom fields, `NOTES` for vault linking)

### For API Code Snippets

Present API usage within the appropriate code block for the target plugin (Templater or DataviewJS):

````markdown
```dataviewjs
const sprint = await $ji.macro.getActiveSprint('PROJ')
const chartData = await $ji.chart.getWorklogPerDay('PROJ', sprint.startDate, sprint.endDate)
dv.paragraph(chartData, this.container)
```
````

**Explanation:**
- Describe why the API approach was required over fence components
- Explain the data pipeline (which `$ji` module, what data is fetched, how it is rendered)
- Note any async operations or integration plugin requirements (Dataview, Templater, Obsidian Chart)

### For Inline Issues

Present inline syntax within a markdown example:

```markdown
The current blocker is JIRA:PROJ-456 and it depends on JIRA:-PROJ-123.
```

**Explanation:**
- Note whether extended or compact mode is used and why

## Additional Resources

### Reference Files

- **`references/components.md`** — Complete component documentation: all fence types, standard/custom field lists, NOTES column with frontmatter JSONPath, rendering modes, and command details
- **`references/api.md`** — Full API reference: all modules (`base`, `defaulted`, `macro`, `chart`, `account`, `util`), method signatures, parameter tables, return types, and integration examples with Templater/Dataview/Obsidian Chart
