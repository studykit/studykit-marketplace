# DQL (Dataview Query Language) Syntax Reference

## Query Structure

Every DQL query follows this general structure:

```
<QUERY-TYPE> [fields]
[FROM <source>]
[WHERE <condition>]
[SORT <field> [ASC|DESC]]
[GROUP BY <field>]
[FLATTEN <field> [AS <alias>]]
[LIMIT <number>]
```

The query type is mandatory. All other clauses are optional and execute in the order written.

## Query Types

| Type | Syntax | Output | Notes |
|------|--------|--------|-------|
| TABLE | `TABLE field1, field2, ...` | Tabular rows with columns | Includes `file.link` as first column by default; suppress with `TABLE WITHOUT ID` |
| LIST | `LIST` or `LIST expression` | Bullet-point list of page links | Optional expression appended after each link |
| TASK | `TASK` | Interactive task checkboxes | Renders `- [ ]` and `- [x]` items from matched pages |
| CALENDAR | `CALENDAR date-field` | Calendar grid with dots on dates | Requires a date field; dots link to corresponding pages |

### TABLE Examples

```dataview
TABLE author, rating, date-read
FROM #book
SORT rating DESC
```

```dataview
TABLE WITHOUT ID file.link AS "Note", file.mtime AS "Last Modified"
FROM "Projects"
```

### LIST Examples

```dataview
LIST
FROM #status/open
WHERE due <= date(today)
```

```dataview
LIST "Priority: " + priority
FROM "Tasks"
SORT priority ASC
```

### TASK Example

```dataview
TASK
FROM "Projects"
WHERE !completed
SORT file.name ASC
```

### CALENDAR Example

```dataview
CALENDAR due
FROM #task
WHERE due != null
```

## FROM Sources

The `FROM` clause restricts which notes to query. Omit it to query the entire vault.

| Source Type | Syntax | Description |
|-------------|--------|-------------|
| Tag | `FROM #tag` | Notes (or sections/tasks) with the specified tag |
| Nested tag | `FROM #tag/subtag` | Notes with a specific subtag |
| Folder | `FROM "folder/path"` | All notes in the folder and its subfolders |
| Specific file | `FROM "folder/File"` | A single note (`.md` extension optional) |
| Incoming links | `FROM [[Note]]` | Pages that link TO the specified note |
| Current file links | `FROM [[]]` | Pages that link to the current note |
| Outgoing links | `FROM outgoing([[Note]])` | Pages linked FROM the specified note |

### Combining Sources

Use `AND`, `OR`, and negation (`!`) to combine sources:

```dataview
TABLE file.name
FROM #project AND "Work"
```

```dataview
LIST
FROM #food AND !#fastfood
```

```dataview
LIST
FROM [[Food]] OR [[Exercise]]
```

```dataview
LIST
FROM (#tag AND "folder") OR ("other-folder" AND #other-tag)
```

## WHERE Clause

Filter results by evaluating expressions against each page's metadata.

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equal | `WHERE status = "done"` |
| `!=` | Not equal | `WHERE status != "archived"` |
| `<` | Less than | `WHERE rating < 3` |
| `>` | Greater than | `WHERE rating > 4` |
| `<=` | Less than or equal | `WHERE due <= date(today)` |
| `>=` | Greater than or equal | `WHERE file.ctime >= date(2024-01-01)` |

### Logical Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `AND` | Both conditions true | `WHERE status = "open" AND priority = "high"` |
| `OR` | Either condition true | `WHERE tag = "work" OR tag = "study"` |
| `NOT` / `!` | Negate condition | `WHERE !completed` |

### Null and Existence Checks

```dataview
WHERE due != null
WHERE field
WHERE !field
```

- `WHERE field` evaluates as truthy (non-null, non-empty).
- `WHERE !field` matches pages where the field is null, empty, or missing.

### Containment Checks

```dataview
WHERE contains(file.tags, "#project")
WHERE contains(author, "Smith")
WHERE icontains(title, "meeting")
WHERE econtains(file.tags, "#project")
WHERE containsword(summary, "important")
```

| Function | Behavior |
|----------|----------|
| `contains()` | Case-sensitive; checks if value is in list, string, or object |
| `icontains()` | Case-insensitive variant of `contains()` |
| `econtains()` | Exact match (does not recurse into nested lists) |
| `containsword()` | Matches whole words only |

### String Matching

```dataview
WHERE startswith(file.name, "2024")
WHERE endswith(file.name, "summary")
WHERE regexmatch("^\d{4}-\d{2}", file.name)
```

### Date Comparisons

```dataview
WHERE due <= date(today)
WHERE file.cday >= date(2024-01-01)
WHERE due - date(today) <= dur(7 days)
WHERE dateformat(due, "EEEE") = "Monday"
```

Date arithmetic supports adding/subtracting durations:
```
WHERE due >= date(today) - dur(30 days)
```

## Data Types

| Type | Literal Format | Example |
|------|---------------|---------|
| Text | `"string"` | `"Hello world"` |
| Number | `123`, `-45`, `3.14` | `42` |
| Boolean | `true`, `false` | `true` |
| Date | `date(YYYY-MM-DD)` | `date(2024-03-15)` |
| Date+Time | `date(YYYY-MM-DDTHH:mm)` | `date(2024-03-15T14:30)` |
| Duration | `dur(N unit)` | `dur(3 days)`, `dur(1h 30m)` |
| Link | `[[Page]]` | `[[My Note]]` |
| List | `[val1, val2, ...]` | `[1, 2, 3]` |
| Object | `{ key: value }` | `{ a: 1, b: 2 }` |
| Null | `null` | `null` |

### Date Shortcuts

| Shortcut | Meaning |
|----------|---------|
| `date(today)` | Current date |
| `date(now)` | Current date and time |
| `date(tomorrow)` | Next day |
| `date(yesterday)` | Previous day |
| `date(sow)` | Start of current week |
| `date(eow)` | End of current week |
| `date(som)` | Start of current month |
| `date(eom)` | End of current month |
| `date(soy)` | Start of current year |
| `date(eoy)` | End of current year |

### Duration Units

| Abbreviation | Full | Example |
|-------------|------|---------|
| `s` | `seconds` | `dur(30 s)` |
| `m` | `minutes` | `dur(5 m)` |
| `h` | `hours` | `dur(2 h)` |
| `d` | `days` | `dur(7 d)` |
| `w` | `weeks` | `dur(2 w)` |
| `mo` | `months` | `dur(3 mo)` |
| `yr` | `years` | `dur(1 yr)` |

Combine multiple units: `dur(1h 30m)`, `dur(2d 6h)`.

## Arithmetic Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `+` | Addition / string concat | `rating + 1`, `"A" + "B"` |
| `-` | Subtraction | `due - date(today)` |
| `*` | Multiplication / string repeat | `score * 2`, `"ab" * 3` |
| `/` | Division | `total / count` |
| `%` | Modulo | `index % 2` |

## Implicit Fields (Page Metadata)

Every page automatically has these fields under the `file` namespace:

| Field | Type | Description |
|-------|------|-------------|
| `file.name` | Text | File name without extension |
| `file.folder` | Text | Path of the containing folder |
| `file.path` | Text | Full file path including name |
| `file.ext` | Text | File extension (usually `md`) |
| `file.link` | Link | A link to the file |
| `file.size` | Number | File size in bytes |
| `file.ctime` | Date+Time | Creation date and time |
| `file.cday` | Date | Creation date (no time component) |
| `file.mtime` | Date+Time | Last modification date and time |
| `file.mday` | Date | Last modification date (no time component) |
| `file.tags` | List | All tags (subtags broken into individual levels) |
| `file.etags` | List | Explicit tags only (subtags not decomposed) |
| `file.inlinks` | List | Incoming links (pages linking to this file) |
| `file.outlinks` | List | Outgoing links (pages this file links to) |
| `file.aliases` | List | Aliases defined in YAML frontmatter |
| `file.tasks` | List | All tasks (`- [ ]` items) in the file |
| `file.lists` | List | All list items (including tasks) |
| `file.frontmatter` | List | Raw frontmatter as `key | value` entries |
| `file.day` | Date | Date from file name or `Date` frontmatter field |
| `file.starred` | Boolean | Whether bookmarked via Obsidian Bookmarks plugin |

### Task-Specific Fields

Tasks (items in `file.tasks`) expose additional fields:

| Field | Type | Description |
|-------|------|-------------|
| `completed` | Boolean | Whether the task is checked |
| `fullyCompleted` | Boolean | Whether the task and all subtasks are checked |
| `text` | Text | Task text content |
| `line` | Number | Line number in the file |
| `path` | Text | Full path of the containing file |
| `section` | Link | Link to the section containing the task |
| `status` | Text | Character inside `[ ]` (space, x, etc.) |
| `checked` | Boolean | Whether any character is inside `[ ]` |
| `created` | Date | Created date (if annotated) |
| `due` | Date | Due date (if annotated) |
| `completion` | Date | Completion date (if annotated) |
| `start` | Date | Start date (if annotated) |
| `scheduled` | Date | Scheduled date (if annotated) |

## SORT Clause

Order results by one or more fields. Default is ascending.

```dataview
SORT file.mtime DESC
SORT rating DESC, file.name ASC
SORT date-read ASC
```

## LIMIT Clause

Cap the number of results returned.

```dataview
TABLE file.name
FROM #note
SORT file.mtime DESC
LIMIT 10
```

## FLATTEN Clause

Expand list fields so each list element becomes its own row.

```dataview
TABLE tag
FROM "Projects"
FLATTEN file.tags AS tag
```

Without `FLATTEN`, a page with three tags produces one row. With `FLATTEN`, it produces three rows (one per tag).

## GROUP BY Clause

Group results by a field. Access grouped rows via `rows` and the group key via `key`.

```dataview
TABLE rows.file.link AS "Notes", length(rows) AS "Count"
FROM #book
GROUP BY genre
```

```dataview
TABLE rows.file.link
FROM "Journal"
GROUP BY file.folder
```

Within a `GROUP BY` result:
- `key` — The group value
- `rows` — A list of all pages in the group
- Access fields via `rows.fieldname` to get a list of values across the group

## Inline Queries

Embed a single computed value within running text using inline DQL:

```markdown
Today is `= date(today)`.
This file: `= this.file.name`.
Word count: `= length(this.file.lists)`.
```

The default prefix is `=` (configurable in Dataview settings).

- `this` refers to the current page.
- Only expressions are supported (no `FROM`, `WHERE`, or other clauses).
- Each inline query outputs exactly one value.

### Inline DataviewJS

For more complex inline computations, use the `$=` prefix:

```markdown
Active projects: `$= dv.pages("#project").where(p => p.status == "active").length`
```

## Property Access

### Frontmatter Properties

Define metadata in YAML frontmatter:

```yaml
---
title: My Note
rating: 4
tags: [book, fiction]
due: 2024-12-31
---
```

Access directly by field name: `WHERE rating > 3`, `TABLE title, due`.

### Inline Fields

Define metadata inline within note content:

```markdown
Status:: Active
Rating:: 5
Due Date:: 2024-12-31
```

Both `Key:: Value` (on its own line) and `[Key:: Value]` (inline within text) formats are supported. Access the same way as frontmatter: `WHERE status = "Active"`.

### Field Name Rules

- Field names are case-insensitive in DQL.
- Spaces in field names: use the name as-is (e.g., `due date`).
- Special characters: wrap in backticks if needed.
- Nested object access: `field.subfield`.
- List indexing: `field[0]` (zero-based).
