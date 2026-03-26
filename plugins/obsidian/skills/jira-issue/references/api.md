# Obsidian Jira Issue — API Reference

Complete reference for the obsidian-jira-issue plugin API. Access via:

```javascript
$ji
// or
this.app.plugins.plugins['obsidian-jira-issue'].api
```

All API responses are cached to reduce network load. Clear cache with `$ji.util.clearCache()` or the "Clear cache" command. Full Jira REST API documentation: https://developer.atlassian.com/cloud/jira/platform/rest

---

## Base API (`$ji.base`)

Direct Jira API access with caching.

### getIssue

Retrieve details about a specific issue.

```typescript
$ji.base.getIssue(issueKey: string, options?: {
    fields?: string[],
    account?: IJiraIssueAccountSettings
}): Promise<IJiraIssue>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `issueKey` | Yes | string | — | Issue ID or key (e.g., `PROJ-123`) |
| `options.fields` | No | string[] | Most fields | Specific fields to retrieve |
| `options.account` | No | IJiraIssueAccountSettings | Auto-detect | Jira account configuration |

### getSearchResults

Execute a JQL query to find matching issues.

```typescript
$ji.base.getSearchResults(query: string, options?: {
    limit?: number,
    offset?: number,
    fields?: string[],
    account?: IJiraIssueAccountSettings
}): Promise<IJiraSearchResults>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `query` | Yes | string | — | JQL query string |
| `options.limit` | No | number (>0) | Settings value | Maximum issues returned |
| `options.offset` | No | number | 0 | Pagination offset |
| `options.fields` | No | string[] | Most fields | Specific fields to retrieve |
| `options.account` | No | IJiraIssueAccountSettings | Auto-detect | Jira account configuration |

### getDevStatus

Retrieve pull request information linked to an issue. Requires OAuth2 connection between version control and Jira.

```typescript
$ji.base.getDevStatus(issueId: string, options?: {
    account?: IJiraIssueAccountSettings
}): Promise<IJiraDevStatus>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `issueId` | Yes | string | — | Issue ID (numeric, from `getIssue` result) |
| `options.account` | No | IJiraIssueAccountSettings | Auto-detect | Jira account configuration |

> **Note**: Requires OAuth2 connection. Check authorization at Profile > Tools > View OAuth Access Tokens.

### getBoards

Retrieve boards associated with a project.

```typescript
$ji.base.getBoards(projectKeyOrId: string, options?: {
    limit?: number,
    offset?: number,
    account?: IJiraIssueAccountSettings
}): Promise<IJiraBoard[]>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `projectKeyOrId` | Yes | string | — | Project key or numeric ID |
| `options.limit` | No | number (>0) | Settings value | Maximum boards returned |
| `options.offset` | No | number | 0 | Pagination offset |
| `options.account` | No | IJiraIssueAccountSettings | Auto-detect | Jira account configuration |

### getSprints

Retrieve sprints associated with a board.

```typescript
$ji.base.getSprints(boardId: number, options?: {
    limit?: number,
    offset?: number,
    state?: ESprintState[],
    account?: IJiraIssueAccountSettings
}): Promise<IJiraSprint[]>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `boardId` | Yes | number | — | Board numeric ID |
| `options.limit` | No | number (>0) | Settings value | Maximum sprints returned |
| `options.offset` | No | number | 0 | Pagination offset |
| `options.state` | No | ESprintState[] | All states | Filter by sprint state |
| `options.account` | No | IJiraIssueAccountSettings | Auto-detect | Jira account configuration |

### getLoggedUser

Retrieve current user information.

```typescript
$ji.base.getLoggedUser(account?: IJiraIssueAccountSettings): Promise<IJiraUser>
```

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `account` | No | IJiraIssueAccountSettings | — | Jira account configuration |

---

## Defaulted API (`$ji.defaulted`)

Same as Base API but all fields are set to default values when the Jira API response has missing data. Simplifies data handling by eliminating null checks.

### getIssue

```typescript
$ji.defaulted.getIssue(issueKey: string, options?: {
    fields?: string[],
    account?: IJiraIssueAccountSettings
}): Promise<IJiraIssue>
```

Parameters identical to `$ji.base.getIssue`.

### getSearchResults

```typescript
$ji.defaulted.getSearchResults(query: string, options?: {
    limit?: number,
    offset?: number,
    fields?: string[],
    account?: IJiraIssueAccountSettings
}): Promise<IJiraSearchResults>
```

Parameters identical to `$ji.base.getSearchResults`.

---

## Macro API (`$ji.macro`)

High-level functions that perform multiple API calls internally for simplified data access.

### getActiveSprint

```typescript
$ji.macro.getActiveSprint(projectKeyOrId: string): Promise<IJiraSprint>
```

Retrieve the active sprint for a project.

### getActiveSprintName

```typescript
$ji.macro.getActiveSprintName(projectKeyOrId: string): Promise<string>
```

Retrieve the name of the currently active sprint.

### getWorkLogBySprint

```typescript
$ji.macro.getWorkLogBySprint(projectKeyOrId: string, sprint: IJiraSprint): Promise<IWorkLog[]>
```

Fetch work log entries for a specific sprint.

### getWorkLogBySprintId

```typescript
$ji.macro.getWorkLogBySprintId(projectKeyOrId: string, sprintId: number): Promise<IWorkLog[]>
```

Fetch work log entries by sprint ID.

### getWorkLogByDates

```typescript
$ji.macro.getWorkLogByDates(projectKeyOrId: string, startDate: string, endDate: string = 'now()'): Promise<IWorkLog[]>
```

Retrieve work log data within a date range. End date defaults to current time.

### getWorkLogSeriesByUser

```typescript
$ji.macro.getWorkLogSeriesByUser(projectKeyOrId: string, startDate: string, endDate: string): Promise<IWorkLogSeries[]>
```

Retrieve work log data grouped by user.

### getVelocity

```typescript
$ji.macro.getVelocity(projectKeyOrId: string, sprintId: number, storyPointFieldName: string): Promise<IVelocity>
```

Calculate velocity for a sprint using the specified story point field.

---

## Chart API (`$ji.chart`)

Generate chart-ready data from Jira worklog information. Designed for use with the Obsidian Chart plugin.

### getWorklogPerDay

```typescript
$ji.chart.getWorklogPerDay(projectKeyOrId: string, startDate: string, endDate: string = 'now()'): Promise<IChartData>
```

Retrieve worklog data organized by individual days.

### getWorklogPerUser

```typescript
$ji.chart.getWorklogPerUser(projectKeyOrId: string, startDate: string, endDate: string = 'now()', options?: {
    format?: EChartFormat,
    capacity?: ISeries
}): Promise<IChartData>
```

Aggregate worklog information by team member with optional chart format and capacity tracking.

---

## Account API (`$ji.account`)

Access stored account settings configured in the plugin.

### getAccountByAlias

```typescript
$ji.account.getAccountByAlias(alias: string): IJiraIssueAccountSettings
```

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `alias` | Yes | string | Account alias defined in plugin settings |

### getAccountByHost

```typescript
$ji.account.getAccountByHost(host: string): IJiraIssueAccountSettings
```

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `host` | Yes | string | Host URL defined in plugin settings |

---

## Util API (`$ji.util`)

### clearCache

```typescript
$ji.util.clearCache(): void
```

Remove all cached Jira API responses. Cache retention duration is configurable in plugin advanced settings.

---

## Integration Examples

### Templater — Active Sprint Info

```
<%* const projectKey = 'AAA' %>
Sprint Name: <%* tR += await $ji.macro.getActiveSprintName(projectKey) %>
Sprint Start: <%* tR += (await $ji.macro.getActiveSprint(projectKey)).startDate %>
Sprint End: <%* tR += (await $ji.macro.getActiveSprint(projectKey)).endDate %>
```

### Templater — Loop Search Results

```
<%* const query = `project = "AAA" AND assignee = currentUser() AND resolution = Unresolved` %>
<%* const searchResults = await $ji.base.getSearchResults(query) %>
<%* for(const issue of searchResults.issues) { %>
## <%* tR += `${issue.key} - ${issue.fields.summary}` %>
Description
<%* tR += issue.fields.description %>
<%* } %>
```

### DataviewJS — Sprint Worklog Per Day Chart

```dataviewjs
const projectKey = 'AAA'
const sprint = await $ji.macro.getActiveSprint(projectKey)
const chartData = await $ji.chart.getWorklogPerDay(projectKey, sprint.startDate, sprint.endDate)
dv.paragraph(chartData, this.container)
```

### DataviewJS — Worklog Per User Chart

```dataviewjs
const projectKey = 'AAA'
const sprint = await $ji.macro.getActiveSprint(projectKey)
const chartData = await $ji.chart.getWorklogPerUser(projectKey, sprint.startDate, sprint.endDate)
dv.paragraph(chartData, this.container)
```
