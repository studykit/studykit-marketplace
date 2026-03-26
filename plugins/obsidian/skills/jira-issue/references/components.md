# Obsidian Jira Issue — Components Reference

Complete reference for all fence components and commands provided by the obsidian-jira-issue plugin.

## Jira Issue Component

Fence component for displaying one or more issue references.

### Syntax

````
```jira-issue
AAA-111
AAA-222
https://my.jira-server.com/browse/BBB-333
# This is a comment
```
````

### Supported Input Formats

- **Issue keys**: `AAA-111` (project key + number)
- **Full Jira URLs**: `https://my.jira-server.com/browse/BBB-333`
- **One issue per line**
- **Comments**: Lines starting with `#` are ignored

---

## Jira Search Component

Fence component that displays JQL query results as a table or list.

### Basic Usage (JQL Only)

Insert a JQL query directly in the fence block:

````
```jira-search
resolution = Unresolved AND assignee = currentUser() AND status = 'In Progress' order by priority DESC
```
````

### Advanced Usage (Keyword Configuration)

| Keyword | Description | Default | Values |
|---------|-------------|---------|--------|
| `type` | Rendering mode | `TABLE` | `TABLE` or `LIST` |
| `query` | Jira query (JQL syntax) | — | JQL string |
| `limit` | Maximum items to display | Settings value | Integer |
| `columns` | Column list to display | Settings value | Comma-separated field names |
| `account` | Account alias to use | Try all by priority | Account alias string |

### Example

````
```jira-search
type: TABLE
query: status = 'In Progress' order by priority DESC
limit: 15
columns: KEY, SUMMARY, -ASSIGNEE, -REPORTER, STATUS
account: Default
```
````

### Standard Fields

Available column names (case-insensitive):

| Field | Description |
|-------|-------------|
| `KEY` | Issue key (e.g., PROJ-123) |
| `SUMMARY` | Issue summary/title |
| `DESCRIPTION` | Issue description |
| `TYPE` | Issue type (Bug, Story, etc.) |
| `CREATED` | Creation date |
| `UPDATED` | Last update date |
| `REPORTER` | Reporter name |
| `ASSIGNEE` | Assignee name |
| `PRIORITY` | Priority level |
| `STATUS` | Current status |
| `DUE_DATE` | Due date |
| `RESOLUTION` | Resolution type |
| `RESOLUTION_DATE` | Resolution date |
| `PROJECT` | Project name |
| `ENVIRONMENT` | Environment field |
| `LABELS` | Issue labels |
| `FIX_VERSIONS` | Fix versions |
| `COMPONENTS` | Components |
| `AGGREGATE_TIME_ESTIMATE` | Aggregate time estimate |
| `AGGREGATE_TIME_ORIGINAL_ESTIMATE` | Aggregate original estimate |
| `AGGREGATE_TIME_SPENT` | Aggregate time spent |
| `TIME_ESTIMATE` | Time estimate |
| `TIME_ORIGINAL_ESTIMATE` | Original time estimate |
| `TIME_SPENT` | Time spent |
| `AGGREGATE_PROGRESS` | Aggregate progress |
| `PROGRESS` | Progress |
| `LAST_VIEWED` | Last viewed date |
| `DEV_STATUS` | Development status |

### Column Modifiers

- **Compact mode**: Prefix with `-` to use compact column rendering (e.g., `-ASSIGNEE`, `-REPORTER`)
- **Custom fields**: Prefix with `$` followed by field name or Jira field ID (e.g., `$Epic Link`, `$Global Rank`, `$12313422`, `-$12313499`)

### NOTES Column

Special column that links search results to notes in the vault:

````
```jira-search
query: status = 'In Progress' order by priority DESC
columns: key, summary, status, notes
```
````

**Matching rules**: Note titles must start with the issue key (e.g., `AAA-123` or `AAA-123 Custom string`). When no matching note exists, a "+" button creates one.

**Frontmatter access via JSONPath**:

```
columns: key, notes, notes.title, notes.status, notes.tags, notes.tags[0]
```

### Footer

Each search table displays:
- Total query results count
- Account alias used
- Last execution timestamp
- Refresh button

---

## Jira Count Component

Fence component that displays a counter of issues matching a JQL query.

### Basic Usage

````
```jira-count
project = REF AND status changed to (Done, "Won't Fix", Archived) after -14d
```
````

### Advanced Usage

| Attribute | Purpose | Default | Type |
|-----------|---------|---------|------|
| `query` | JQL query string | (required) | string |
| `label` | Text displayed beside the counter | `'Count'` | string |
| `account` | Account alias to use | Try all by priority | Account alias string |

### Example

````
```jira-count
query: status = 'In Progress' order by priority DESC
label: Issues to complete
account: Default
```
````

---

## Inline Issue

Embed Jira issue references inline within note text — works in paragraphs, titles, lists, checkboxes, and code blocks.

### Syntax

The plugin detects the inline issue prefix followed by an issue key. The prefix is configurable in the obsidian-jira-issue plugin settings (default: `JIRA:`). The actual prefix depends on the user's configuration.

| Format | Mode | Example |
|--------|------|---------|
| `JIRA:KEY-123` | Extended | Shows type icon, key, summary, status |
| `JIRA:-KEY-123` | Compact | Shows type icon, key, status (no summary) |
| `https://jira.example.com/browse/KEY-123` | Extended (URL) | Full URL reference |
| `-https://jira.example.com/browse/KEY-123` | Compact (URL) | Compact URL reference |

### Rendering Modes

- **Extended mode**: Displays type icon + key + summary + status
- **Compact mode** (hyphen prefix): Displays type icon + key + status (no summary)

### Configuration

The inline issue prefix and URL detection features are configurable through the obsidian-jira-issue plugin settings panel in Obsidian. The default prefix is `JIRA:` but users may set any custom prefix. Always verify the user's configured prefix before generating inline issue references.

---

## Commands

Available via the Obsidian command palette (`Ctrl/Cmd + P`).

### Insert Templates

- **Insert issue template** — Insert `jira-issue` fence block template
- **Insert search template** — Insert `jira-search` fence block template
- **Insert count template** — Insert `jira-count` fence block template

### Clear Cache

Manually clears all cached Jira API responses. The cache also clears automatically when plugin settings are modified. Cache retention duration is configurable in advanced settings.

### Search Wizard

Interactive UI for building `jira-search` blocks without memorizing keyword syntax. Presents a form-based interface for configuring query, columns, limits, and rendering type.
