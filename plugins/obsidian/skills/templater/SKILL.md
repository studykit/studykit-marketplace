---
name: templater
description: Read, understand, and modify Obsidian Templater templates — command syntax, tp.* API, and practical patterns.
argument-hint: <what to modify, e.g. "add a date picker to my daily note template", "fix the frontmatter update logic">
---

# Templater Skill

Help users understand and modify existing Templater templates in their Obsidian vault. Templater uses a command syntax (`<% %>`) with a `tp.*` API to dynamically generate note content.

## Command Syntax Quick Reference

| Syntax | Name | Purpose | Output? |
|--------|------|---------|---------|
| `<% expr %>` | Interpolation | Evaluate expression and insert result | Yes |
| `<%* code %>` | Execution | Run JavaScript silently | No (use `tR +=` to output) |
| `<%+ expr %>` | Dynamic | Re-evaluate on each preview open | Yes (deprecated — prefer Dataview) |

### Whitespace Control

| Modifier | Effect |
|----------|--------|
| `<%-` | Trim one newline before |
| `-%>` | Trim one newline after |
| `<%_` | Trim all whitespace before |
| `_%>` | Trim all whitespace after |

### Key Variables

- **`tR`** — The accumulated template result string. Use `tR += "text"` in execution commands to append output. `tR = ""` resets all prior output.

## Template Modification Workflow

When the user asks to modify an existing template, follow these steps:

### Step 1: Analyze the Existing Template

Read the template file and identify:
- Which `tp.*` modules are used (date, file, system, frontmatter, etc.)
- Control flow patterns (conditionals, loops)
- User interaction points (prompts, suggesters)
- Frontmatter manipulation hooks
- Cursor placement positions

### Step 2: Understand the Modification Intent

Classify the request:

| Intent | Approach |
|--------|----------|
| Add new dynamic field | Insert `<% %>` interpolation with appropriate `tp.*` call |
| Add user input | Use `tp.system.prompt()` or `tp.system.suggester()` with `await` |
| Add conditional logic | Use `<%* if/else %>` execution blocks with `-%>` whitespace trimming |
| Modify frontmatter | Use `tp.hooks.on_all_templates_executed()` + `processFrontMatter()` |
| Fix broken template | Check syntax, missing `await`, unmatched brackets, wrong API signatures |
| Add file operations | Use `tp.file.create_new()`, `tp.file.move()`, `tp.file.rename()` |

### Step 3: Build the Modification

Consult `references/modules.md` for exact function signatures and parameters. Apply these rules:

1. **Always `await` async functions** — `tp.system.prompt()`, `tp.system.suggester()`, `tp.web.request()`, `tp.file.create_new()` all require `await`.
2. **Use execution blocks for setup** — Capture variables with `<%* let x = await ... %>`, then reference with `<% x %>`.
3. **Trim whitespace around control flow** — Use `-%>` after opening `<%* if -%>` and `<%* } -%>` to avoid blank lines.
4. **Frontmatter updates run in hooks** — Direct `tp.frontmatter` is read-only. To write, use `tp.hooks.on_all_templates_executed()`.
5. **Cursor placement is ordered** — `tp.file.cursor(1)` jumps first, `tp.file.cursor(2)` second. Same number = multi-cursor.

### Step 4: Validate and Present

Before presenting the modified template:
- Verify all `tp.*` function signatures match `references/modules.md`
- Check that `await` is used where needed
- Ensure whitespace trimming produces clean output
- Confirm variable scoping (variables declared in `<%* %>` are available in subsequent commands)

## Common Patterns

### Prompted Metadata

```markdown
<%*
let title = await tp.system.prompt("Title");
let type = await tp.system.suggester(
  ["Note", "Meeting", "Project"],
  ["note", "meeting", "project"]
);
let tags = await tp.system.multi_suggester(
  ["work", "personal", "urgent", "reference"],
  ["work", "personal", "urgent", "reference"],
  false, "Select tags"
);
-%>
---
title: <% title %>
type: <% type %>
tags: [<% tags.join(", ") %>]
created: <% tp.date.now() %>
---
```

### Conditional Sections

```markdown
<%* let includeLog = await tp.system.suggester(["Yes", "No"], [true, false]); -%>
<%* if (includeLog) { -%>
## Activity Log

| Time | Activity |
|------|----------|
| <% tp.date.now("HH:mm") %> | <% tp.file.cursor(1) %> |
<%* } -%>
```

### Frontmatter Update via Hook

```markdown
<%*
tp.hooks.on_all_templates_executed(async () => {
  const file = tp.file.find_tfile(tp.file.path(true));
  await tp.app.fileManager.processFrontMatter(file, (fm) => {
    fm["modified"] = tp.date.now();
    if (!fm["created"]) fm["created"] = tp.date.now();
  });
});
-%>
```

### Daily Note with Navigation

```markdown
---
created: <% tp.date.now() %>
---

# <% tp.file.title %>

<< [[<% tp.date.now("YYYY-MM-DD", -1) %>]] | [[<% tp.date.now("YYYY-MM-DD", 1) %>]] >>

## Tasks
- [ ] <% tp.file.cursor(1) %>

## Notes
<% tp.file.cursor(2) %>
```

### File Creation from Template

```markdown
<%*
let name = await tp.system.prompt("Project name");
let folder = await tp.system.suggester(
  (f) => f.path,
  tp.app.vault.getAllLoadedFiles().filter(f => f.children),
  false, "Select folder"
);
await tp.file.create_new(
  tp.file.find_tfile("Templates/Project"),
  name,
  true,
  folder
);
-%>
```

## Output Template

When presenting a modified template, use this format:

````markdown
Here is the updated template:

```markdown
(full template content with modifications)
```

**Changes made:**
- (bullet list of what was changed and why)

**Notes:**
- (any caveats, e.g. required settings, plugin dependencies)
````

## Additional Resources

### Reference Files

- **`references/modules.md`** — Complete `tp.*` API reference covering all internal modules (tp.date, tp.file, tp.system, tp.frontmatter, tp.hooks, tp.obsidian, tp.web, tp.config) and user functions (tp.user) with signatures, parameters, and examples
- **`references/patterns.md`** — Practical template examples organized by use case (daily notes, meeting notes, project templates, book notes, weekly reviews, etc.) with explanations of techniques used
