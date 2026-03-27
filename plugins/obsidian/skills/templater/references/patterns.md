# Templater Patterns Reference

Practical template examples organized by use case. Each pattern explains the techniques used so you can adapt them.

---

## Daily Note

Full daily note template with navigation, weather prompt, and structured sections.

```markdown
<%*
let mood = await tp.system.suggester(
  ["Great", "Good", "Okay", "Bad"],
  ["great", "good", "okay", "bad"]
);
-%>
---
created: <% tp.date.now("YYYY-MM-DD") %>
mood: <% mood %>
tags: [daily]
---

# <% tp.date.now("dddd, MMMM Do YYYY") %>

<< [[<% tp.date.now("YYYY-MM-DD", -1) %>]] | [[<% tp.date.now("YYYY-MM-DD", 1) %>]] >>

## Morning
- [ ] <% tp.file.cursor(1) %>

## Notes
<% tp.file.cursor(2) %>

## Gratitude
1.
2.
3.
```

**Techniques**: `suggester` for mood selection, date offset for navigation links, `cursor()` for jump points.

---

## Weekly Review

Aggregates the current week with navigation to daily notes.

```markdown
---
type: weekly
week: <% tp.date.now("YYYY-[W]ww") %>
start: <% tp.date.weekday("YYYY-MM-DD", 0) %>
end: <% tp.date.weekday("YYYY-MM-DD", 6) %>
---

# Week <% tp.date.now("ww, YYYY") %>

## Daily Notes
<%*
for (let i = 0; i <= 6; i++) {
  let day = tp.date.weekday("YYYY-MM-DD", i);
  let label = tp.date.weekday("dddd", i);
  tR += `- [[${day}|${label}]]\n`;
}
-%>

## Wins
- <% tp.file.cursor(1) %>

## Improvements
- <% tp.file.cursor(2) %>

## Next Week Focus
- <% tp.file.cursor(3) %>
```

**Techniques**: Loop with `tR +=` for dynamic list generation, `weekday()` with offset for each day.

---

## Meeting Note

Interactive template that prompts for attendees and project.

```markdown
<%*
let title = await tp.system.prompt("Meeting title");
let project = await tp.system.suggester(
  (item) => item.basename,
  tp.app.vault.getMarkdownFiles().filter(f => f.path.startsWith("Projects/")),
  false, "Select project"
);
let attendees = await tp.system.prompt("Attendees (comma-separated)");
await tp.file.rename(`${tp.date.now("YYYY-MM-DD")} ${title}`);
-%>
---
type: meeting
project: "[[<% project ? project.basename : "" %>]]"
attendees: [<% attendees.split(",").map(a => `"${a.trim()}"`).join(", ") %>]
date: <% tp.date.now("YYYY-MM-DD") %>
---

# <% title %>

## Agenda
- <% tp.file.cursor(1) %>

## Discussion

## Action Items
- [ ] <% tp.file.cursor(2) %>

## Decisions
```

**Techniques**: `rename()` for dynamic file naming, file filtering with `getMarkdownFiles()`, string splitting for list input.

---

## Book Note

Template with ISBN lookup via web request.

```markdown
<%*
let isbn = await tp.system.prompt("ISBN (or leave empty)");
let title, author, cover;
if (isbn) {
  let data = await tp.web.request(`https://openlibrary.org/isbn/${isbn}.json`);
  let book = JSON.parse(data);
  title = book.title || "Unknown";
  let authorData = await tp.web.request(`https://openlibrary.org${book.authors[0].key}.json`);
  author = JSON.parse(authorData).name || "Unknown";
  cover = `https://covers.openlibrary.org/b/isbn/${isbn}-M.jpg`;
} else {
  title = await tp.system.prompt("Book title");
  author = await tp.system.prompt("Author");
  cover = "";
}
-%>
---
type: book
title: "<% title %>"
author: "<% author %>"
status: to-read
rating:
started:
finished:
tags: [book]
---

# <% title %>
*by <% author %>*

<%* if (cover) { -%>
![](<% cover %>)

<%* } -%>
## Summary
<% tp.file.cursor(1) %>

## Key Ideas
1.

## Quotes
>

## My Thoughts
<% tp.file.cursor(2) %>
```

**Techniques**: `tp.web.request()` for API lookup, conditional image rendering, fallback to manual input.

---

## Project Note

Multi-step project setup with folder creation.

```markdown
<%*
let name = await tp.system.prompt("Project name");
let status = await tp.system.suggester(
  ["Active", "Planning", "On Hold", "Completed"],
  ["active", "planning", "on-hold", "completed"]
);
let area = await tp.system.suggester(
  (f) => f.name,
  tp.app.vault.getAllLoadedFiles().filter(f => f.children && f.path.startsWith("Areas/")),
  false, "Select area"
);
await tp.file.move(`Projects/${name}/${name}`);
-%>
---
type: project
status: <% status %>
area: "[[<% area ? area.name : "" %>]]"
created: <% tp.date.now("YYYY-MM-DD") %>
due:
tags: [project]
---

# <% name %>

## Objective
<% tp.file.cursor(1) %>

## Key Results
- [ ]
- [ ]
- [ ]

## Resources
-

## Log
### <% tp.date.now("YYYY-MM-DD") %>
- Project created
```

**Techniques**: `move()` to relocate file into project folder (creates intermediate directories), folder filtering for area selection.

---

## Zettelkasten / Literature Note

Captures a source reference with linked atomic notes.

```markdown
<%*
let sourceType = await tp.system.suggester(
  ["Article", "Book", "Video", "Podcast", "Paper"],
  ["article", "book", "video", "podcast", "paper"]
);
let sourceTitle = await tp.system.prompt("Source title");
let sourceAuthor = await tp.system.prompt("Author");
let sourceUrl = await tp.system.prompt("URL (optional)");
-%>
---
type: literature
source-type: <% sourceType %>
title: "<% sourceTitle %>"
author: "<% sourceAuthor %>"
<%* if (sourceUrl) { -%>
url: "<% sourceUrl %>"
<%* } -%>
created: <% tp.date.now("YYYY-MM-DD") %>
processed: false
tags: [literature/<% sourceType %>]
---

# <% sourceTitle %>
*<% sourceAuthor %>*<%* if (sourceUrl) { %> — [Link](<% sourceUrl %>)<%* } %>

## Key Points
1. <% tp.file.cursor(1) %>

## Permanent Notes
-

## Questions
- <% tp.file.cursor(2) %>
```

**Techniques**: Conditional frontmatter fields, inline conditional with interpolation, nested tag hierarchy.

---

## Periodic Frontmatter Stamping

Startup template that auto-stamps frontmatter on every new file in a folder.

```markdown
<%*
// This template runs as a folder template for "Inbox/"
tp.hooks.on_all_templates_executed(async () => {
  const file = tp.file.find_tfile(tp.file.path(true));
  await tp.app.fileManager.processFrontMatter(file, (fm) => {
    fm["created"] = tp.date.now("YYYY-MM-DDTHH:mm");
    fm["status"] = "inbox";
    if (!fm["tags"]) fm["tags"] = [];
  });
});
-%>
# <% tp.file.title %>

<% tp.file.cursor() %>
```

**Techniques**: `on_all_templates_executed` hook for safe frontmatter writes, folder template auto-application.

---

## Dynamic Table of Contents

Reads the current file content and generates a TOC from headings.

```markdown
<%*
let content = tp.file.content;
let headings = content.match(/^#{2,6}\s+.+$/gm) || [];
let toc = headings.map(h => {
  let level = h.match(/^(#+)/)[1].length - 2;
  let text = h.replace(/^#+\s+/, "");
  let anchor = text.toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
  return `${"  ".repeat(level)}- [[#${text}|${text}]]`;
}).join("\n");
tR += toc;
-%>
```

**Techniques**: Regex parsing of `tp.file.content`, dynamic markdown generation with `tR +=`.

---

## Multi-File Batch Creator

Creates multiple related files at once from a single prompt.

```markdown
<%*
let projectName = await tp.system.prompt("Project name");
let phases = ["Planning", "Execution", "Review"];

for (let phase of phases) {
  let content = `---\nproject: "[[${projectName}]]"\nphase: ${phase.toLowerCase()}\n---\n\n# ${projectName} — ${phase}\n\n`;
  await tp.file.create_new(content, `${projectName} - ${phase}`, false, "Projects");
}
-%>
Created project files for **<% projectName %>**:
<%* for (let phase of phases) { -%>
- [[<% projectName %> - <% phase %>]]
<%* } -%>
```

**Techniques**: `create_new()` with string content (not template file), loop-based batch creation, output summary with links.

---

## Clipboard-Based Quick Capture

Captures clipboard content with automatic link detection.

```markdown
<%*
let clip = await tp.system.clipboard();
let isUrl = /^https?:\/\//.test(clip);
let category = await tp.system.suggester(
  ["Idea", "Reference", "Quote", "Task"],
  ["idea", "reference", "quote", "task"]
);
-%>
---
type: capture
category: <% category %>
captured: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
---

<%* if (category === "quote") { -%>
> <% clip %>

— Source: <% tp.file.cursor(1) %>
<%* } else if (isUrl) { -%>
[<% tp.file.cursor(1) %>](<% clip %>)

<%* } else { -%>
<% clip %>

<%* } -%>
## Notes
<% tp.file.cursor(2) %>
```

**Techniques**: `clipboard()` for content capture, regex URL detection, category-driven output formatting.
