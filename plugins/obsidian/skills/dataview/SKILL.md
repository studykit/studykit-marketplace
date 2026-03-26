---
name: dataview
description: >-
  This skill should be used when the user asks to "create a dataview query",
  "generate DQL", "dataview table of", "list notes by", "dataviewjs to show",
  "query vault metadata", "obsidian dataview", "DQL query for",
  "filter notes by tag", "aggregate data across notes", "dataview calendar",
  or wants to create dynamic views in an Obsidian vault using the Dataview plugin.
  Only trigger when the current project is an Obsidian vault (contains a .obsidian/ directory).
argument-hint: <what to query, e.g. "table of books with rating > 4", "list tasks due this week">
---

# Obsidian Dataview Query Generator

Generate a Dataview query for: **$ARGUMENTS**

## Overview

Dataview is an Obsidian plugin that treats a vault as a queryable database, enabling dynamic views over notes, tags, tasks, and frontmatter metadata. It provides two query interfaces:

- **DQL (Dataview Query Language)** — A declarative SQL-like syntax for straightforward queries. Supports `TABLE`, `LIST`, `TASK`, and `CALENDAR` output types with `FROM`, `WHERE`, `SORT`, `GROUP BY`, `FLATTEN`, and `LIMIT` clauses. Prefer DQL for most use cases.
- **DataviewJS** — A JavaScript-based API (`dv.*`) for complex logic, conditional rendering, multi-step data transformations, or custom HTML output. Use DataviewJS when DQL alone cannot express the required logic (e.g., nested loops, dynamic headers, combining data from multiple unrelated sources, or advanced formatting).

### When to Use Each

| Scenario | Recommended |
|----------|-------------|
| Simple table of notes with metadata columns | DQL |
| Filtered list by tags, folders, or properties | DQL |
| Task lists with date filtering | DQL |
| Calendar view of dated notes | DQL |
| Conditional formatting or dynamic rendering | DataviewJS |
| Aggregations across groups with custom output | DataviewJS |
| Multi-source joins or complex transformations | DataviewJS |
| Inline computed values in running text | Inline DQL (`` `= expression` ``) |

## Query Generation Workflow

### Step 1: Analyze Intent

Determine the appropriate query type based on `$ARGUMENTS`:

| Query Type | Use When | Syntax |
|------------|----------|--------|
| `TABLE` | Displaying structured columns of metadata | `TABLE field1, field2, ...` |
| `LIST` | Showing a bullet-point list of pages | `LIST` or `LIST expression` |
| `TASK` | Rendering interactive task checkboxes | `TASK` |
| `CALENDAR` | Showing a date-based calendar view | `CALENDAR date-field` |

Identify the key elements from the user's request:
- **Source scope** — Which notes to query (tags, folders, links, or all)
- **Filter conditions** — What criteria to apply (dates, values, existence checks)
- **Output fields** — Which metadata to display as columns or list items
- **Ordering** — How to sort results (ascending/descending, by which field)
- **Grouping** — Whether results should be grouped by a field
- **Limits** — Whether to cap the number of results

### Step 2: Decide DQL vs DataviewJS

Apply these decision rules:

1. **Start with DQL.** It covers the vast majority of use cases with cleaner, more readable syntax. DQL is the correct choice whenever the query can be expressed as a single pass of filtering, sorting, and projecting fields. Most requests involving "show me notes where...", "list all...", "table of...", or "calendar of..." map directly to DQL.
2. **Escalate to DataviewJS** only when the request requires:
   - Conditional logic (if/else) in output rendering — e.g., showing different text based on a field value
   - String building or template interpolation beyond simple field references
   - Iterating over nested data structures with custom formatting per level
   - Combining queries from multiple unrelated sources into a single output view
   - Custom HTML elements, CSS classes, or styling beyond plain markdown
   - Async operations such as loading file contents with `dv.io.load()`
   - Progress bars, sparklines, or other computed visual elements
   - Multi-step aggregations that GROUP BY cannot express alone (e.g., nested grouping, pivot-table logic)
3. **Use Inline DQL** (`` `= expression` ``) when embedding a single computed value within running note text — e.g., displaying the current file's creation date or a count of tasks. Inline queries support `this.*` for current page access and all DQL functions, but do not support `FROM`, `WHERE`, or other clauses.
4. **Use Inline DataviewJS** (`` `$= dv.expression()` ``) for inline computations that require querying across pages or applying logic beyond what inline DQL supports.

### Step 3: Build DQL Query

Construct the query using the following clause order:

```
<QUERY-TYPE> [fields]
[FROM <source>]
[WHERE <condition>]
[SORT <field> [ASC|DESC]]
[GROUP BY <field>]
[FLATTEN <field> [AS <alias>]]
[LIMIT <number>]
```

All clauses after the query type are optional. Multiple data commands (WHERE, SORT, etc.) execute in the order written.

#### FROM Sources

The `FROM` clause restricts which notes to query. Omit it to query the entire vault. Combine sources with `AND`, `OR`, and negation (`!`):

| Source Type | Syntax | Description |
|-------------|--------|-------------|
| Tag | `FROM #tag` | Notes with the specified tag |
| Folder | `FROM "folder/path"` | All notes in folder and subfolders |
| Incoming links | `FROM [[note]]` | Pages that link TO the note |
| Outgoing links | `FROM outgoing([[note]])` | Pages linked FROM the note |
| Current file | `FROM [[]]` | Pages that link to the current note |
| Combined | `FROM #tag AND "folder"` | Both conditions must match |
| Negated | `FROM #food AND !#fastfood` | Exclude matching sources |

Use parentheses for complex combinations: `FROM (#tag AND "folder") OR ("other" AND #alt)`.

#### WHERE Conditions

Filter results using comparison, logical, and function-based operators:

- **Comparison**: `=`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `AND`, `OR`, `NOT` (or `!`)
- **Containment**: `contains(field, value)` (case-sensitive), `icontains()` (case-insensitive), `econtains()` (exact), `containsword()` (whole word)
- **String matching**: `startswith(string, prefix)`, `endswith(string, suffix)`, `regexmatch(pattern, string)`, `regextest(pattern, string)`
- **Date comparisons**: `WHERE due <= date(today)`, `WHERE file.cday >= date(2024-01-01)`, `WHERE due - date(today) <= dur(7 days)`
- **Null/existence checking**: `WHERE field != null` (field exists and is non-null), `WHERE field` (truthy -- non-null, non-empty), `WHERE !field` (null, empty, or missing)

For the full operator and expression reference, consult `references/dql-syntax.md`.

#### Implicit Fields

Access built-in page metadata without defining frontmatter. Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `file.name` | Text | File name without extension |
| `file.path` | Text | Full file path |
| `file.folder` | Text | Containing folder path |
| `file.link` | Link | Clickable link to the file |
| `file.tags` | List | All tags (subtags decomposed) |
| `file.etags` | List | Explicit tags (subtags not decomposed) |
| `file.ctime` / `file.cday` | Date | Creation datetime / date |
| `file.mtime` / `file.mday` | Date | Modification datetime / date |
| `file.size` | Number | File size in bytes |
| `file.inlinks` | List | Pages linking to this file |
| `file.outlinks` | List | Pages this file links to |
| `file.tasks` | List | All tasks in the file |
| `file.lists` | List | All list items (including tasks) |
| `file.day` | Date | Date from filename or Date field |
| `file.aliases` | List | Aliases from frontmatter |
| `file.starred` | Boolean | Bookmarked via Obsidian Bookmarks |
| `file.frontmatter` | List | Raw frontmatter key-value entries |

For the complete implicit fields reference including task-specific fields, consult `references/dql-syntax.md`.

#### SORT, LIMIT, FLATTEN, GROUP BY

- **SORT**: `SORT field ASC` or `SORT field DESC`. Multiple fields: `SORT rating DESC, file.name ASC`.
- **LIMIT**: `LIMIT 10` -- Cap the number of results.
- **FLATTEN**: `FLATTEN file.tags AS tag` -- Expand list fields so each element becomes its own row. Without FLATTEN, a page with three tags produces one row; with it, three rows (one per tag).
- **GROUP BY**: `GROUP BY genre` -- Group results; access the group key via `key` and grouped rows via `rows`. Use `rows.fieldname` to get a list of values within a group. Use `TABLE WITHOUT ID` with GROUP BY to avoid duplicate link columns.

#### Functions

Apply transformations and checks within WHERE, TABLE fields, and LIST expressions. Key categories:

- **String**: `contains`, `icontains`, `replace`, `lower`, `upper`, `split`, `join`, `startswith`, `endswith`, `regextest`, `regexreplace`, `substring`, `truncate`, `padleft`, `padright`
- **Date**: `date()`, `dur()`, `dateformat()`, `durationformat()`, `striptime()`, `localtime()`
- **Numeric**: `round`, `sum`, `average`, `min`, `max`, `floor`, `ceil`, `abs`, `product`, `reduce`, `minby`, `maxby`
- **List**: `length`, `filter`, `map`, `sort`, `reverse`, `flat`, `unique`, `any`, `all`, `none`, `nonnull`, `firstvalue`, `join`, `slice`
- **Utility**: `default`, `choice`, `typeof`, `meta`, `elink`, `link`, `embed`, `number`, `string`, `object`, `list`

For complete function signatures with parameters and examples, consult `references/functions.md`.

### Step 4: Build DataviewJS Query

When DQL is insufficient, construct a DataviewJS block using the `dv.*` API. The core workflow involves three stages: query, transform, and render.

**Stage 1 -- Query pages:**

Use `dv.pages(source)` with the same source syntax as DQL `FROM`. Note that folder sources require nested quotes: `dv.pages('"FolderName"')`.

```javascript
const pages = dv.pages("#tag")           // by tag
    .where(p => p.rating > 4)            // filter
    .sort(p => p.file.name, "asc")       // sort
    .limit(10);                          // limit
```

**Stage 2 -- Transform data:**

Chain DataArray methods to shape results. Key methods: `.where()` / `.filter()`, `.sort()`, `.map()`, `.flatMap()`, `.groupBy()`, `.limit()`, `.distinct()`. All methods return a new DataArray (immutable). Access a field across all elements by property access: `dv.pages("#book").file.name` returns a DataArray of all book file names.

**Stage 3 -- Render output:**

```javascript
// Table -- headers array + 2D rows array
dv.table(["Name", "Rating"], pages.map(p => [p.file.link, p.rating]));

// List -- array of items
dv.list(pages.map(p => p.file.link));

// Task list -- task objects, optional groupByFile boolean
dv.taskList(pages.file.tasks.where(t => !t.completed), false);

// Text output
dv.header(2, "Results");
dv.paragraph("Found " + pages.length + " matching notes.");

// Custom HTML element
dv.el("div", "Styled content", { cls: "my-class", attr: { style: "color: red;" } });
```

**Current page access:**

```javascript
const current = dv.current();
dv.list(current.file.outlinks);
```

**Date handling** uses Luxon DateTime objects via `dv.date()`:

```javascript
const today = dv.date("today");
const weekAgo = dv.date("today").minus({ days: 7 });
```

**File content loading** is async and requires `await`:

```javascript
const content = await dv.io.load("Templates/header.md");
dv.paragraph(content);
```

For the complete DataviewJS API including all chain methods, rendering functions, and advanced patterns, consult `references/dataviewjs.md`.

## Output Template

Present the generated query in the following format:

### For DQL Queries

````markdown
```dataview
TABLE field1, field2
FROM #tag
WHERE condition
SORT field DESC
```
````

**Explanation:**
- Describe why this query type was chosen
- Explain each clause and what it filters/sorts/groups
- Note any implicit fields or functions used

### For DataviewJS Queries

````markdown
```dataviewjs
dv.table(
    ["Column1", "Column2"],
    dv.pages("#tag")
        .where(p => p.field > value)
        .sort(p => p.field, "asc")
        .map(p => [p.file.link, p.field])
);
```
````

**Explanation:**
- Describe why DataviewJS was required over DQL
- Explain the data pipeline (query, filter, transform, render)
- Note any Luxon date operations or async calls used

### For Inline Queries

Use inline DQL for embedding a single computed value in running text:

```markdown
Last modified: `= this.file.mtime`
Total tasks: `= length(this.file.tasks)`
```

Use inline DataviewJS for more complex inline computations:

```markdown
`$= dv.pages("#project").where(p => p.status == "active").length` active projects
```

## Additional Resources

### Reference Files

- **`references/dql-syntax.md`** — Complete DQL query language reference covering query types, FROM sources, WHERE operators, data types, implicit fields, and all clauses (SORT, LIMIT, FLATTEN, GROUP BY)
- **`references/functions.md`** — Comprehensive Dataview functions reference with signatures and examples for string, numeric, date, list, and utility functions
- **`references/dataviewjs.md`** — DataviewJS API reference covering `dv.pages()`, chain methods, rendering functions, `dv.current()`, IO operations, and common patterns
