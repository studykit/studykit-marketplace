# DataviewJS API Reference

DataviewJS provides a JavaScript API for querying and rendering vault data within `dataviewjs` code blocks. It exposes the `dv` variable with methods for querying pages, rendering output, and accessing utilities.

## Code Block Syntax

````markdown
```dataviewjs
// JavaScript code using the dv API
dv.table(["Name", "Rating"],
    dv.pages("#book")
        .where(p => p.rating >= 4)
        .map(p => [p.file.link, p.rating])
);
```
````

## Query Methods

### dv.pages(source)

Query pages matching a source string. The source format mirrors DQL `FROM` syntax.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `string` | Tag, folder, link, or combination |

**Source format examples:**

| Source | Syntax |
|--------|--------|
| All pages | `dv.pages()` or `dv.pages("")` |
| By tag | `dv.pages("#book")` |
| By folder | `dv.pages('"Projects"')` (note nested quotes) |
| By incoming links | `dv.pages("[[Dashboard]]")` |
| By outgoing links | `dv.pages("outgoing([[Dashboard]])")` |
| Combined | `dv.pages("#tag AND \"folder\"")` |
| Negation | `dv.pages("#food AND -#fastfood")` |

Returns a **DataArray** of page objects. Each page object contains all frontmatter fields plus `file.*` implicit fields.

```javascript
const books = dv.pages("#book");
// books[0].title, books[0].file.name, books[0].file.link, etc.
```

### dv.pagePaths(source)

Return a DataArray of file paths (strings) matching the source, without loading full page data.

```javascript
const paths = dv.pagePaths("#project");
// ["Projects/Alpha.md", "Projects/Beta.md", ...]
```

### dv.page(path)

Load a single page object by file path or link.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `string` or `Link` | File path or link to resolve |

```javascript
const note = dv.page("Projects/Alpha");
dv.paragraph(note.summary);
```

Auto-resolves links and file extensions — `dv.page("Alpha")` works if unambiguous.

### dv.current()

Return the page object for the note containing the current `dataviewjs` block.

```javascript
const me = dv.current();
dv.header(2, me.file.name);
dv.list(me.file.outlinks);
```

## DataArray Chain Methods

`dv.pages()` returns a DataArray supporting functional chain methods. All chain methods return a new DataArray (immutable).

| Method | Signature | Description |
|--------|-----------|-------------|
| `where` | `.where(predicate)` | Keep elements where predicate returns truthy |
| `filter` | `.filter(predicate)` | Alias for `.where()` |
| `sort` | `.sort(fn, [direction])` | Sort by function; direction is `"asc"` (default) or `"desc"` |
| `map` | `.map(fn)` | Transform each element |
| `flatMap` | `.flatMap(fn)` | Map and flatten one level |
| `groupBy` | `.groupBy(fn)` | Group into `{ key, rows }` objects |
| `limit` | `.limit(count)` | Take the first N elements |
| `slice` | `.slice(start, [end])` | Return a portion (zero-indexed) |
| `distinct` | `.distinct()` | Remove duplicate values |
| `array` | `.array()` | Convert DataArray to a plain JavaScript array |
| `values` | `.values` | Property; access the underlying array |

### Chain Method Examples

```javascript
// Filter, sort, and limit
const recent = dv.pages("#note")
    .where(p => p.file.mtime >= dv.date("2024-01-01"))
    .sort(p => p.file.mtime, "desc")
    .limit(20);
```

```javascript
// Group by folder
const grouped = dv.pages("#project")
    .groupBy(p => p.file.folder);

for (const group of grouped) {
    dv.header(3, group.key);
    dv.list(group.rows.map(p => p.file.link));
}
```

```javascript
// FlatMap to expand lists
const allTags = dv.pages('"Notes"')
    .flatMap(p => p.file.tags)
    .distinct();
dv.list(allTags);
```

### Accessing Fields from DataArrays

When accessing a field on a DataArray, it returns a DataArray of that field's values across all elements:

```javascript
const names = dv.pages("#book").file.name;
// DataArray of all book file names

const tags = dv.pages("#project").file.tags;
// DataArray of arrays (each page's tags)
```

## Rendering Methods

### dv.table(headers, rows)

Render a table.

| Parameter | Type | Description |
|-----------|------|-------------|
| `headers` | `string[]` | Column header names |
| `rows` | `any[][]` | 2D array of row data |

```javascript
dv.table(
    ["Book", "Author", "Rating"],
    dv.pages("#book")
        .sort(p => p.rating, "desc")
        .map(p => [p.file.link, p.author, p.rating])
);
```

### dv.list(elements)

Render a bullet-point list.

| Parameter | Type | Description |
|-----------|------|-------------|
| `elements` | `any[]` or `DataArray` | Items to render as list |

```javascript
dv.list(dv.pages("#project").file.link);
```

```javascript
dv.list(
    dv.pages("#task")
        .where(p => p.status === "open")
        .map(p => `${p.file.link} - Due: ${p.due}`)
);
```

### dv.taskList(tasks, groupByFile)

Render an interactive task list.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tasks` | `DataArray` | Task objects (from `page.file.tasks`) |
| `groupByFile` | `boolean` | Group tasks under their source file (default: `true`) |

```javascript
// All incomplete tasks from project notes
dv.taskList(
    dv.pages("#project").file.tasks
        .where(t => !t.completed),
    false
);
```

```javascript
// Tasks due this week, grouped by file
dv.taskList(
    dv.pages('"Tasks"').file.tasks
        .where(t => t.due && t.due <= dv.date("eow")),
    true
);
```

### dv.paragraph(text)

Render a paragraph of text.

```javascript
dv.paragraph("This dashboard was generated at " + dv.date("now"));
```

### dv.header(level, text)

Render a markdown header.

| Parameter | Type | Description |
|-----------|------|-------------|
| `level` | `number` | Header level (1-6) |
| `text` | `string` | Header text |

```javascript
dv.header(2, "Project Summary");
```

### dv.span(text)

Render inline text (no block-level wrapper).

```javascript
dv.span("Status: **Active**");
```

### dv.el(element, text, [options])

Render an arbitrary HTML element.

| Parameter | Type | Description |
|-----------|------|-------------|
| `element` | `string` | HTML tag name (e.g., `"div"`, `"b"`, `"em"`) |
| `text` | `string` | Content |
| `options` | `object` | Optional: `{ cls: "class-name", attr: { id: "my-id" } }` |

```javascript
dv.el("b", "Important note");
dv.el("div", "Styled content", { cls: "my-custom-class", attr: { style: "color: red;" } });
```

## IO Methods

### dv.io.load(path, [originFile])

Asynchronously load the text contents of a file. Requires `await`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `string` | Path to the file |
| `originFile` | `string` | Optional origin file for resolving relative paths |

Returns `string` or `undefined` if the file does not exist.

```javascript
const content = await dv.io.load("Templates/header.md");
dv.paragraph(content);
```

### dv.io.normalize(path, [originFile])

Convert a relative path to an absolute vault path.

```javascript
const fullPath = dv.io.normalize("./subfolder/note");
```

## Date Utilities

### dv.date(text)

Convert text to a Luxon `DateTime` object. Accepts the same shortcuts as the DQL `date()` function.

```javascript
const today = dv.date("today");
const specific = dv.date("2024-03-15");
const startOfMonth = dv.date("som");
```

### Luxon DateTime

DataviewJS uses Luxon for date handling. Common operations:

```javascript
const now = dv.date("now");

// Access components
now.year;    // 2024
now.month;   // 3
now.day;     // 15
now.weekday; // 1-7 (Monday = 1)

// Formatting
now.toFormat("yyyy-MM-dd");
now.toISODate();

// Arithmetic
now.plus({ days: 7 });
now.minus({ months: 1 });
now.startOf("month");
now.endOf("week");

// Comparison
date1 < date2;
date1.equals(date2);
date1.diff(date2, "days").days;
```

## Common Patterns

### Conditional Rendering

```javascript
const tasks = dv.pages("#project").file.tasks.where(t => !t.completed);

if (tasks.length > 0) {
    dv.header(3, "Open Tasks (" + tasks.length + ")");
    dv.taskList(tasks, true);
} else {
    dv.paragraph("All tasks completed.");
}
```

### Multi-Source Dashboard

```javascript
// Combine data from different sources
dv.header(2, "Dashboard");

dv.header(3, "Recent Notes");
dv.list(
    dv.pages('"Notes"')
        .sort(p => p.file.mtime, "desc")
        .limit(5)
        .map(p => p.file.link)
);

dv.header(3, "Upcoming Deadlines");
dv.table(
    ["Task", "Due"],
    dv.pages("#task")
        .where(p => p.due && p.due >= dv.date("today"))
        .sort(p => p.due, "asc")
        .limit(10)
        .map(p => [p.file.link, p.due])
);
```

### Progress Tracker

```javascript
const projects = dv.pages("#project");
dv.table(
    ["Project", "Progress", "Tasks"],
    projects.map(p => {
        const total = p.file.tasks.length;
        const done = p.file.tasks.where(t => t.completed).length;
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;
        const bar = "█".repeat(Math.floor(pct / 10)) + "░".repeat(10 - Math.floor(pct / 10));
        return [p.file.link, `${bar} ${pct}%`, `${done}/${total}`];
    })
);
```

### Aggregation with Group By

```javascript
const grouped = dv.pages("#book")
    .groupBy(p => p.genre);

dv.table(
    ["Genre", "Count", "Avg Rating"],
    grouped.map(g => [
        g.key,
        g.rows.length,
        Math.round(dv.func.average(g.rows.map(b => b.rating)) * 10) / 10
    ])
);
```

### Dynamic Tag Cloud

```javascript
const allTags = dv.pages("")
    .flatMap(p => p.file.etags)
    .groupBy(t => t);

const sorted = allTags.sort(g => g.rows.length, "desc").limit(20);
dv.list(sorted.map(g => `${g.key} (${g.rows.length})`));
```

### Habit Tracker (Calendar-like)

```javascript
const days = dv.pages('"Journal"')
    .where(p => p.file.day && p.exercise === true)
    .map(p => p.file.day.toFormat("yyyy-MM-dd"));

dv.header(3, "Exercise Days This Month");
dv.list(days.sort(d => d, "desc"));
```

### Reading File Content

```javascript
// Load and display a file's raw content
const content = await dv.io.load("Templates/daily-template.md");
if (content) {
    dv.header(3, "Template Preview");
    dv.paragraph(content);
} else {
    dv.paragraph("Template not found.");
}
```

### Inline DataviewJS

Embed computed values inline within note text using the `$=` prefix:

```markdown
Total books: `$= dv.pages("#book").length`
Last modified: `$= dv.current().file.mtime.toFormat("yyyy-MM-dd")`
Open tasks: `$= dv.pages("#project").file.tasks.where(t => !t.completed).length`
```
