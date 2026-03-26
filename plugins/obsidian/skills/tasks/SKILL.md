---
name: tasks
description: >-
  This skill should be used when the user asks to "create a tasks query",
  "show overdue tasks", "filter tasks by due date", "tasks due this week",
  "high priority tasks", "obsidian tasks filter", "task dashboard query",
  "tasks group by", "recurring task query", "tasks sorted by priority",
  "blocked tasks", "incomplete tasks",
  or wants to build task query blocks for the Obsidian Tasks plugin.
argument-hint: <what to query, e.g. "overdue high-priority tasks", "tasks due this week grouped by project">
context: fork
---

# Obsidian Tasks Query Generator

Generate a Tasks plugin query for: **$ARGUMENTS**

## Overview

The Obsidian Tasks plugin extends Obsidian's built-in checklist items with rich metadata — priority levels, multiple date types, recurrence rules, dependencies, and custom statuses. Tasks are standard Markdown checklist lines (`- [ ] ...`) annotated with emoji signifiers that encode structured data inline.

Query blocks use a dedicated ` ```tasks ` fenced code block. Inside the block, each line is a declarative instruction — a filter, sort rule, group rule, or display option. The plugin evaluates all instructions against every task in the vault (or scoped paths) and renders matching results. Multiple filter lines combine with implicit AND logic; explicit boolean operators (AND, OR, NOT, XOR) enable complex combinations within a single line.

**Key differences from Dataview tasks:**
- Tasks uses its own query language (not DQL or inline JS).
- Metadata lives inline via emoji signifiers, not YAML frontmatter or Dataview annotations.
- Queries are placed in ` ```tasks ` blocks, not ` ```dataview ` blocks.
- Built-in support for recurrence, dependencies, and custom status workflows.

## Task Format Quick Reference

### Priority Markers

| Emoji | Syntax in filter | Level |
|-------|-----------------|-------|
| 🔺 | `highest` | Highest |
| ⏫ | `high` | High |
| 🔼 | `medium` | Medium |
| *(none)* | `none` | None (default) |
| 🔽 | `low` | Low |
| ⏬ | `lowest` | Lowest |

### Date Markers

| Emoji | Date type | Filter keyword |
|-------|-----------|---------------|
| ➕ | Created | `created` |
| ⏳ | Scheduled | `scheduled` |
| 🛫 | Start | `starts` |
| 📅 | Due | `due` |
| ✅ | Done | `done` |
| ❌ | Cancelled | `cancelled` |

### Other Signifiers

| Emoji | Purpose |
|-------|---------|
| 🔁 | Recurrence rule (e.g., `🔁 every week on Monday`) |
| 🏁 | On-completion action (`keep` or `delete`) |
| 🆔 | Task identifier for dependencies |
| ⛔ | Depends-on reference |

### Recurrence Syntax

Recurrence rules follow the 🔁 emoji and require at least one date field on the task.

| Pattern | Example |
|---------|---------|
| Interval | `every 3 days`, `every 2 weeks`, `every month` |
| Specific day | `every week on Monday`, `every week on Tuesday, Friday` |
| Weekdays | `every weekday` |
| Monthly position | `every month on the 1st`, `every month on the last Friday` |
| Yearly | `every year`, `every January on the 15th` |
| Based on completion | Append `when done` to any rule |

### Status Types

| Type | Meaning | Matches `not done` |
|------|---------|-------------------|
| `TODO` | Not started | Yes |
| `IN_PROGRESS` | Currently active | Yes |
| `ON_HOLD` | Paused | Yes |
| `DONE` | Completed | No |
| `CANCELLED` | Cancelled | No |
| `NON_TASK` | Not a task | No |

### Full Task Line Format

```
- [ ] Task description 🔺 🔁 every week on Monday 🛫 2024-01-01 📅 2024-01-07 ➕ 2024-01-01
```

Order of signifiers does not matter. The checkbox status character determines the status type.

## Query Generation Workflow

### Step 1: Analyze Intent

Determine what tasks to show based on `$ARGUMENTS`. Identify:

- **Status scope** — all tasks, only incomplete (`not done`), only completed (`done`), or specific status types
- **Date constraints** — overdue, due today/this week/this month, scheduled, upcoming, date ranges
- **Priority level** — highest, high, medium, low, lowest, or ranges (above/below)
- **Content filters** — description text, tags, path/folder restrictions
- **Recurrence** — recurring vs. one-time tasks
- **Dependencies** — blocked or blocking tasks

Most queries should start with `not done` unless completed or all tasks are explicitly requested.

### Step 2: Build Filters

Construct filter lines based on the identified intent. Read `references/filters.md` for the complete filter reference including all date filters, text matching, regex support, and boolean combinations.

**Common filter patterns:**

```tasks
# Overdue tasks
not done
due before today

# Tasks due this week
not done
due this week

# High priority or above
not done
priority is above medium

# Tasks in a specific folder
not done
folder includes Projects/Active

# Boolean combination on a single line
(tags include #urgent) OR (priority is above medium)
```

Each line is an independent filter combined with implicit AND. Use boolean operators (AND, OR, NOT, XOR) with delimiters to combine conditions on a single line. See `references/filters.md` for full boolean syntax, delimiter rules, and nesting.

### Step 3: Add Sorting

Add `sort by <field>` lines to control result ordering. Append `reverse` for descending order. Stack multiple sort lines for multi-level sorting (first line = primary sort).

```tasks
sort by priority
sort by due
sort by path
```

Available sort fields: `due`, `priority`, `status`, `status.type`, `status.name`, `urgency`, `tag`, `description`, `path`, `filename`, `heading`, `recurring`, `created`, `scheduled`, `start`, `done`, `cancelled`, `happens`, `id`, `random`.

Custom sorting: `sort by function <JS expression>` for advanced logic.

### Step 4: Add Grouping

Add `group by <field>` lines to organize results under headings. Stack multiple group lines for nested grouping (first = outermost level). Append `reverse` to flip heading order.

```tasks
group by folder
group by priority
group by due
```

Available group fields: `due`, `done`, `scheduled`, `start`, `created`, `cancelled`, `happens`, `status`, `status.name`, `status.type`, `priority`, `urgency`, `recurring`, `recurrence`, `tags`, `path`, `root`, `folder`, `filename`, `backlink`, `heading`, `id`.

Custom grouping: `group by function <JS expression>` using task properties for fully customized headings. See `references/grouping-sorting.md` for details and examples.

### Step 5: Add Display Options

Control what information appears in the results.

```tasks
# Hide specific elements
hide priority
hide backlink
hide edit button
hide task count

# Compact display
short mode

# Limit results
limit 20
limit groups 5

# Debug the query
explain
```

Full display options: `hide id`, `hide depends on`, `hide priority`, `hide created date`, `hide start date`, `hide scheduled date`, `hide due date`, `hide done date`, `hide cancelled date`, `hide recurrence rule`, `hide on completion`, `hide tags`, `hide edit button`, `hide postpone button`, `hide backlink`, `hide task count`, `hide toolbar`, `show tree`, `show urgency`, `short mode`, `full mode`.

See `references/grouping-sorting.md` for the complete display option reference.

## Output Template

Present the generated query in a fenced code block with a line-by-line explanation:

````markdown
```tasks
not done
due before today
priority is above none
sort by priority
sort by due
group by priority
hide backlink
hide edit button
```
````

**Explanation:**

| Line | Purpose |
|------|---------|
| `not done` | Show only incomplete tasks (TODO, IN_PROGRESS, ON_HOLD) |
| `due before today` | Filter to overdue tasks only |
| `priority is above none` | Exclude tasks with no priority set |
| `sort by priority` | Primary sort: highest priority first |
| `sort by due` | Secondary sort: earliest due date first |
| `group by priority` | Organize results under priority headings |
| `hide backlink` | Remove source file links for cleaner display |
| `hide edit button` | Remove the pencil edit icon |

When the query involves complex boolean logic, provide the expanded explanation using the `explain` instruction to verify filter interpretation.

## Common Query Patterns

### Weekly Review Dashboard

````markdown
```tasks
not done
happens in this week
group by due
sort by priority
hide edit button
hide backlink
```
````

### Overdue Tasks Needing Attention

````markdown
```tasks
not done
due before today
sort by due
sort by priority
group by folder
```
````

### Project-Scoped Task List

````markdown
```tasks
not done
folder includes Projects/MyProject
group by heading
sort by priority
sort by due
hide backlink
```
````

### Completed Tasks This Month

````markdown
```tasks
done
done in this month
sort by done reverse
group by done
hide edit button
```
````

### High Priority Across All Projects

````markdown
```tasks
not done
priority is above medium
sort by due
group by folder
short mode
limit 25
```
````

### Tasks with Boolean Logic

````markdown
```tasks
not done
(tags include #urgent) OR (priority is highest)
due in this week
sort by priority
sort by due
```
````

## Syntax Quick Reference

| Concept | Syntax |
|---------|--------|
| Filter | One instruction per line; implicit AND between lines |
| Boolean | `(filter1) AND/OR/NOT/XOR (filter2)` on a single line |
| Sort | `sort by <field>` or `sort by <field> reverse` |
| Group | `group by <field>` or `group by <field> reverse` |
| Limit | `limit <N>` or `limit groups <N>` |
| Regex | `<field> regex matches /<pattern>/[i]` |
| Custom filter | `filter by function <JS expression>` |
| Custom sort | `sort by function <JS expression>` |
| Custom group | `group by function <JS expression>` |
| Debug | `explain` |
| Compact | `short mode` |
| Line continuation | Trailing `\` on boolean lines |

## Additional Resources

### Reference Files

- **`references/filters.md`** — Complete filter reference covering status, date, priority, text, tag, path, heading, recurrence, dependency, and property filters with boolean combinations and regex syntax
- **`references/grouping-sorting.md`** — Grouping fields, custom group-by-function expressions, sorting fields, display/layout options, limit syntax, and explain usage
