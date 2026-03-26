# Grouping, Sorting, and Display Options

Complete reference for organizing and displaying Obsidian Tasks query results.

## Sorting

### Syntax

```
sort by <field>
sort by <field> reverse
```

- Default direction is ascending.
- Append `reverse` for descending order.
- Stack multiple `sort by` lines for multi-level sorting. The first line is the primary sort; subsequent lines break ties.

### Sort Fields

| Field | Description |
|-------|-------------|
| `due` | Due date (earliest first) |
| `priority` | Priority level (highest first) |
| `status` | Done/todo status |
| `status.type` | Status type: IN_PROGRESS, TODO, ON_HOLD, DONE, CANCELLED, NON_TASK |
| `status.name` | Status name alphabetically |
| `urgency` | Calculated urgency score |
| `tag` | Tag value (first tag by default) |
| `tag <N>` | Nth tag on the task (1-based index) |
| `description` | Task description text |
| `path` | Full file path |
| `filename` | Filename with extension |
| `heading` | Preceding section heading |
| `recurring` | Recurrence status (recurring first) |
| `created` | Created date |
| `scheduled` | Scheduled date |
| `start` | Start date |
| `done` | Completion date |
| `cancelled` | Cancellation date |
| `happens` | Earliest of start/scheduled/due |
| `id` | Task ID |
| `random` | Random order (deterministic per day) |

### Examples

```tasks
# Priority first, then due date
sort by priority
sort by due

# Most recently created first
sort by created reverse

# Alphabetical by description
sort by description

# By urgency score, highest first
sort by urgency reverse
```

### Custom Sorting

Use JavaScript expressions for advanced sort logic (Tasks 6.0.0+):

```
sort by function <JavaScript expression>
```

The expression receives a `task` object (same properties as custom filters — see `filters.md`). Return a number (negative = sort before), a string (alphabetical comparison), or an array for multi-level logic.

```tasks
# Sort by number of tags (most tags first)
sort by function task.tags.length reverse

# Sort by description length
sort by function task.description.length
```

## Grouping

### Syntax

```
group by <field>
group by <field> reverse
```

- Stack multiple `group by` lines for nested grouping. First line = outermost level (rendered as h4), second = h5, third and beyond = h6.
- Append `reverse` to flip the heading order within that level.

### Group Fields

| Field | Description | Heading format |
|-------|-------------|---------------|
| `due` | Due date | Date with weekday |
| `done` | Completion date | Date with weekday |
| `scheduled` | Scheduled date | Date with weekday |
| `start` | Start date | Date with weekday |
| `created` | Created date | Date with weekday |
| `cancelled` | Cancellation date | Date with weekday |
| `happens` | Earliest of start/scheduled/due | Date with weekday |
| `status` | Status category | "Done" or "Todo" |
| `status.name` | Custom status name | Status name text |
| `status.type` | Status type | IN_PROGRESS, TODO, ON_HOLD, DONE, CANCELLED, NON_TASK |
| `priority` | Priority level | Priority name (Highest, High, Medium, None, Low, Lowest) |
| `urgency` | Urgency score | Numeric urgency value |
| `recurring` | Recurrence status | "Recurring" or "Not Recurring" |
| `recurrence` | Recurrence rule | Rule text (e.g., "every week") |
| `tags` | Task tags | Tag text or "(No tags)" — one group per tag |
| `path` | Full file path | Path string |
| `root` | Top-level vault folder | Root folder name |
| `folder` | Containing folder | Folder path |
| `filename` | Source file | Filename as link |
| `backlink` | File and heading | Filename + heading combined |
| `heading` | Section heading | Heading text or "(No heading)" |
| `id` | Task ID | ID value |

### Examples

```tasks
# Group by project folder, then priority
group by folder
group by priority

# Group by status type, reversed
group by status.type reverse

# Group by due date, then by tags
group by due
group by tags
```

### Custom Grouping

Use JavaScript expressions for fully customized group headings (same `task` object as custom filters):

```
group by function <JavaScript expression>
```

Return a string for the group heading. Return an array to place a task in multiple groups.

#### Task Date Properties for Grouping

Date properties expose formatting methods:

| Method | Output |
|--------|--------|
| `task.due.format("YYYY-MM-DD dddd")` | Formatted date string |
| `task.due.category.groupText` | Category heading: "%%1%% Overdue", "%%2%% Today", "%%3%% Future", "%%4%% Undated" |
| `task.due.fromNow.groupText` | Relative time: "%%1%% 3 days ago", "%%2%% in 5 days" |

The `%%N%%` prefixes control sort order and are hidden in rendered output.

#### Examples

```tasks
# Group overdue / today / future / undated
group by function task.due.category.groupText

# Group by year and month
group by function task.due.format("YYYY-MM [Month] MM")

# Group by custom status label
group by function task.isDone ? "Completed" : "Action Required"

# Group by first tag or "Untagged"
group by function task.tags.length > 0 ? task.tags[0] : "Untagged"

# Group by day of the week
group by function task.due.format("dddd")

# Place task in multiple groups (one per tag)
group by function task.tags
```

## Display Options

### Hiding Task Elements

Hide specific metadata from rendered results. All elements are shown by default.

| Instruction | Hides |
|-------------|-------|
| `hide id` | Task ID (🆔) |
| `hide depends on` | Dependency references (⛔) |
| `hide priority` | Priority emoji |
| `hide created date` | Created date (➕) |
| `hide start date` | Start date (🛫) |
| `hide scheduled date` | Scheduled date (⏳) |
| `hide due date` | Due date (📅) |
| `hide done date` | Done date (✅) |
| `hide cancelled date` | Cancelled date (❌) |
| `hide recurrence rule` | Recurrence rule (🔁) |
| `hide on completion` | On-completion action (🏁) |
| `hide tags` | All tags |

### Hiding Query Elements

| Instruction | Hides |
|-------------|-------|
| `hide edit button` | Pencil icon for editing |
| `hide postpone button` | Postpone action button |
| `hide backlink` | Source file link |
| `hide task count` | Task count at bottom of results |
| `hide toolbar` | Toolbar above results |

### Showing Optional Elements

| Instruction | Shows |
|-------------|-------|
| `show urgency` | Urgency score value |
| `show tree` | Parent/child task hierarchy |

### Display Modes

| Instruction | Effect |
|-------------|--------|
| `full mode` | Show emojis, full dates, and complete recurrence rules (default) |
| `short mode` | Show only emojis; dates and rules appear as tooltips on hover |

Set a per-file default with YAML frontmatter: `TQ_short_mode: true` or `false`.

### Examples

```tasks
# Clean dashboard view
hide edit button
hide backlink
hide task count
short mode

# Minimal: only description and status
hide priority
hide created date
hide start date
hide scheduled date
hide due date
hide done date
hide recurrence rule
hide tags
hide backlink
hide edit button
```

## Limiting Results

### Syntax

| Instruction | Effect |
|-------------|--------|
| `limit to <N> tasks` | Show only the first N results after sorting |
| `limit <N>` | Shorthand for `limit to <N> tasks` |
| `limit groups to <N> tasks` | Show only the first N tasks in each group |
| `limit groups <N>` | Shorthand for `limit groups to <N> tasks` |

`limit groups` is ignored when no `group by` instruction is present.

When a limit hides results, the total count is displayed (e.g., "20 of 150 tasks").

### Examples

```tasks
# Top 10 most urgent tasks
not done
sort by urgency reverse
limit 10

# Top 5 per priority group
not done
group by priority
sort by due
limit groups 5
```

## Explain

Add `explain` on its own line to display a debug summary at the top of the results. The summary shows:

- Expanded dates (relative dates resolved to absolute)
- Boolean filter structure in hierarchical format
- Active global query and global filters
- Query file defaults applied to this block
- Resolved placeholder values
- Sort and group instructions in effect

```tasks
not done
due this week
priority is above medium
sort by due
explain
```

Use `explain` during query development to verify filter interpretation, then remove it for production dashboards.
