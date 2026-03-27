# Templater Modules Reference

Complete API reference for all `tp.*` internal modules and user functions.

**Conventions**: `?` = optional parameter, `= value` = default value.

---

## tp.config

Templater's running configuration. Read-only.

| Property | Type | Description |
|----------|------|-------------|
| `tp.config.active_file` | TFile? | The active file when Templater was launched |
| `tp.config.run_mode` | RunMode | How the template was triggered (create, append, overwrite, etc.) |
| `tp.config.target_file` | TFile | The file where template output is inserted |
| `tp.config.template_file` | TFile | The template file being executed |

---

## tp.date

Date manipulation using Moment.js format strings.

> The global `moment` object is also available for advanced operations (`moment().startOf("week")`, etc.).

### `tp.date.now(format?, offset?, reference?, reference_format?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"YYYY-MM-DD"` | Moment.js format string |
| `offset` | number \| string | — | Days offset (number) or ISO 8601 duration (string, e.g. `"P-1M"`) |
| `reference` | string | — | Reference date to calculate from |
| `reference_format` | string | — | Moment.js format for the reference string |

```
<% tp.date.now() %>                          → 2024-01-15
<% tp.date.now("Do MMMM YYYY") %>           → 15th January 2024
<% tp.date.now("YYYY-MM-DD", -7) %>         → last week
<% tp.date.now("YYYY-MM-DD", 7) %>          → next week
<% tp.date.now("YYYY-MM-DD", "P-1M") %>     → last month (ISO 8601)
<% tp.date.now("YYYY-MM-DD", "P1Y") %>      → next year
<% tp.date.now("YYYY-MM-DD", 1, tp.file.title, "YYYY-MM-DD") %>  → file title date + 1 day
```

### `tp.date.tomorrow(format?)`

| Parameter | Type | Default |
|-----------|------|---------|
| `format` | string | `"YYYY-MM-DD"` |

### `tp.date.yesterday(format?)`

| Parameter | Type | Default |
|-----------|------|---------|
| `format` | string | `"YYYY-MM-DD"` |

### `tp.date.weekday(format?, weekday, reference?, reference_format?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"YYYY-MM-DD"` | Moment.js format |
| `weekday` | number | — | 0 = locale first weekday, -7 = previous week, 7 = next week |
| `reference` | string | — | Reference date string |
| `reference_format` | string | — | Format for reference |

```
<% tp.date.weekday("YYYY-MM-DD", 0) %>       → this Monday
<% tp.date.weekday("YYYY-MM-DD", 7) %>       → next Monday
```

---

## tp.file

File properties and manipulation.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `tp.file.content` | string | File contents at execution time (read-only snapshot) |
| `tp.file.tags` | string[] | Array of file tags |
| `tp.file.title` | string | File title without extension |

### `tp.file.create_new(template, filename?, open_new?, folder?)`

Creates a new file. **Async — requires `await`.**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `template` | TFile \| string | — | Template file or string content |
| `filename` | string | `"Untitled"` | New file name (without extension) |
| `open_new` | boolean | `false` | Open the new file after creation |
| `folder` | TFolder \| string | — | Target folder |

Returns: the newly created `TFile`.

### `tp.file.creation_date(format?)`

| Parameter | Type | Default |
|-----------|------|---------|
| `format` | string | `"YYYY-MM-DD HH:mm"` |

### `tp.file.cursor(order?)`

Sets cursor position after template insertion. Same `order` number = multi-cursor.

| Parameter | Type | Description |
|-----------|------|-------------|
| `order` | number | Cursor jump order (1 = first, 2 = second, etc.) |

### `tp.file.cursor_append(content)`

Appends content after the active cursor.

### `tp.file.exists(filepath)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `filepath` | string | Vault-relative path **including extension** |

Returns: `boolean`.

### `tp.file.find_tfile(filename)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | File name or vault-relative path |

Returns: `TFile` instance.

### `tp.file.folder(absolute?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `absolute` | boolean | `false` | `false` = basename only, `true` = vault-absolute path |

### `tp.file.include(include_link)`

Includes and processes templates from another file. Supports `[[MyFile#Section]]` and block references.

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_link` | string \| TFile | Wiki-link or TFile reference |

### `tp.file.last_modified_date(format?)`

| Parameter | Type | Default |
|-----------|------|---------|
| `format` | string | `"YYYY-MM-DD HH:mm"` |

### `tp.file.move(new_path, file_to_move?)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `new_path` | string | Vault path **without extension** |
| `file_to_move` | TFile? | Defaults to current file |

### `tp.file.path(relative?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `relative` | boolean | `false` | `false` = system absolute, `true` = vault-relative |

### `tp.file.rename(new_title)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `new_title` | string | New title (extension preserved automatically) |

### `tp.file.selection()`

Returns: the active file's selected text (string).

---

## tp.frontmatter

Read-only access to YAML frontmatter variables.

```
<% tp.frontmatter.alias %>
<% tp.frontmatter["variable name with spaces"] %>
```

For frontmatter:
```yaml
---
alias: myfile
note type: seedling
categories:
  - book
  - movie
---
```

```
<% tp.frontmatter.alias %>                    → "myfile"
<% tp.frontmatter["note type"] %>             → "seedling"
<% tp.frontmatter.categories.join(", ") %>    → "book, movie"
```

> **To write frontmatter**, use `tp.hooks.on_all_templates_executed()` with `processFrontMatter()`. See tp.hooks below.

---

## tp.hooks

Execute code on Templater events.

### `tp.hooks.on_all_templates_executed(callback_function)`

Runs the callback after all active templates finish processing. Multiple invocations run callbacks in parallel.

| Parameter | Type | Description |
|-----------|------|-------------|
| `callback_function` | `() => any` | Async or sync callback |

**Frontmatter update pattern:**
```javascript
<%*
tp.hooks.on_all_templates_executed(async () => {
  const file = tp.file.find_tfile(tp.file.path(true));
  await tp.app.fileManager.processFrontMatter(file, (fm) => {
    fm["key"] = "value";
  });
});
-%>
```

**Run Obsidian command after template:**
```javascript
<%*
tp.hooks.on_all_templates_executed(() => {
  tp.app.commands.executeCommandById("obsidian-linter:lint-file");
});
-%>
```

---

## tp.obsidian

Exposes the Obsidian API. Key exports:

| Export | Description |
|--------|-------------|
| `tp.obsidian.TFolder` | Folder class |
| `tp.obsidian.normalizePath(path)` | Normalize file paths |
| `tp.obsidian.htmlToMarkdown(html)` | Convert HTML to Markdown |
| `tp.obsidian.requestUrl(urlOrRequest)` | HTTP requests (async) |

Use `tp.obsidian.requestUrl()` for HTTP calls within Obsidian's sandbox (preferred over `fetch`).

---

## tp.system

User interaction functions. **All require `await`.**

### `tp.system.clipboard()`

Returns: clipboard contents (string).

### `tp.system.prompt(prompt_text?, default_value?, throw_on_cancel?, multiline?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt_text` | string | — | Text displayed above input |
| `default_value` | string | — | Pre-filled value |
| `throw_on_cancel` | boolean | `false` | Throw error on cancel instead of returning null |
| `multiline` | boolean | `false` | Use textarea |

Returns: user input string, or `null` if cancelled (unless `throw_on_cancel`).

```
<% await tp.system.prompt("Enter title") %>
<% await tp.system.prompt("Mood?", "happy") %>
<% await tp.system.prompt("Long text", null, false, true) %>
```

### `tp.system.suggester(text_items, items, throw_on_cancel?, placeholder?, limit?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_items` | string[] \| `(item: T) => string` | — | Display labels or mapping function |
| `items` | T[] | — | Actual values returned on selection |
| `throw_on_cancel` | boolean | `false` | Throw on cancel |
| `placeholder` | string | `""` | Search placeholder |
| `limit` | number | — | Max rendered items |

Returns: the chosen item from `items`, or `null` if cancelled.

```
<% await tp.system.suggester(["Happy", "Sad"], ["Happy", "Sad"]) %>
<% await tp.system.suggester((item) => item.basename, tp.app.vault.getMarkdownFiles()) %>
```

### `tp.system.multi_suggester(text_items, items, throw_on_cancel?, title?, limit?)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_items` | string[] \| `(item: T) => string` | — | Display labels or mapping function |
| `items` | T[] | — | Actual values |
| `throw_on_cancel` | boolean | `false` | Throw on cancel |
| `title` | string | `""` | Modal header text |
| `limit` | number | — | Max rendered items |

Returns: array of chosen items.

```
<% await tp.system.multi_suggester(["A", "B", "C"], ["a", "b", "c"]) %>
```

---

## tp.web

Web request functions. **All require `await`.**

### `tp.web.daily_quote()`

Returns: a daily quote formatted as a callout.

### `tp.web.random_picture(size?, query?, include_size?)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | string | `"<width>x<height>"` |
| `query` | string | Comma-separated search terms |
| `include_size` | boolean | Include dimensions in markdown |

### `tp.web.request(url, path?)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | Target URL |
| `path` | string | JSON path to extract (e.g. `"0.title"`) |

```
<% await tp.web.request("https://jsonplaceholder.typicode.com/todos/1") %>
<% await tp.web.request("https://jsonplaceholder.typicode.com/todos", "0.title") %>
```

---

## tp.app

Direct access to the Obsidian `app` instance. Prefer `tp.app` over the global `app`.

Commonly used:
- `tp.app.vault.getAllLoadedFiles()` — all files in the vault
- `tp.app.vault.getMarkdownFiles()` — all markdown files
- `tp.app.fileManager.processFrontMatter(file, callback)` — update frontmatter
- `tp.app.commands.executeCommandById(id)` — execute an Obsidian command

---

## tp.user

User-defined functions. **Not available on Obsidian mobile.**

### Script Functions

JavaScript `.js` files in the configured script folder, loaded as CommonJS modules.

**Single function:**
```javascript
// Scripts/greet.js
module.exports = function (name) {
  return `Hello, ${name}!`;
};
```
```
<% tp.user.greet("World") %>  → Hello, World!
```

**Object export (multiple functions):**
```javascript
// Scripts/format.js
module.exports = {
  callout: (text, type = "note") => {
    const lines = text.split("\n").map(l => `> ${l}`);
    return `> [!${type}]\n${lines.join("\n")}`;
  },
  heading: (text, level = 2) => `${"#".repeat(level)} ${text}`,
};
```
```
<% tp.user.format.callout("Important note", "warning") %>
```

**Access**: Global namespace (`app`, `moment`) is available. Template-scoped variables (`tp`, `tR`) must be passed as arguments.

### System Command Functions

Configured in Templater settings. Arguments become environment variables.

```
<% tp.user.echo({a: "hello", b: "world"}) %>
```
In the command: `$a` and `$b` are available.
