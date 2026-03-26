# Tasks Filter Reference

Complete reference for all Obsidian Tasks plugin query filters. Each filter occupies its own line inside a ` ```tasks ` block. Multiple lines combine with implicit AND logic.

> Most filter instructions are case-insensitive (Tasks 5.2.0+). Boolean operators (AND, OR, NOT, XOR) must remain uppercase. Regular expressions and custom filter functions are case-sensitive.

## Status Filters

| Filter | Description |
|--------|-------------|
| `done` | Match completed tasks (DONE, CANCELLED, NON_TASK statuses) |
| `not done` | Match incomplete tasks (TODO, IN_PROGRESS, ON_HOLD statuses) |
| `status.name includes <string>` | Match by custom status name text |
| `status.name does not include <string>` | Exclude by custom status name text |
| `status.name regex matches /<regex>/` | Match status name by regex |
| `status.name regex does not match /<regex>/` | Exclude status name by regex |
| `status.type is <type>` | Match by status type |
| `status.type is not <type>` | Exclude by status type |

**Status types:** `TODO`, `DONE`, `IN_PROGRESS`, `ON_HOLD`, `CANCELLED`, `NON_TASK`

```tasks
# Example: show only in-progress tasks
status.type is IN_PROGRESS
```

## Date Filters

Six date properties are available: `due`, `done`, `scheduled`, `starts`, `created`, `cancelled`. Each supports the same set of filter operations.

### Single Date Comparisons

| Syntax | Description |
|--------|-------------|
| `<date> on <value>` | Exact date match |
| `<date> before <value>` | Strictly before |
| `<date> after <value>` | Strictly after |
| `<date> on or before <value>` | On or before |
| `<date> on or after <value>` | On or after |

**Date values** can be absolute (`2024-01-15`) or relative (`today`, `tomorrow`, `yesterday`, `last Monday`, `next Friday`).

```tasks
# Tasks due today
due on today

# Tasks due before end of week
due before next Saturday

# Overdue tasks
not done
due before today
```

### Date Range Searches

| Syntax | Description |
|--------|-------------|
| `<date> in <range>` | Within the range |
| `<date> before <range>` | Before the range starts |
| `<date> after <range>` | After the range ends |
| `<date> in or before <range>` | Within or before the range |
| `<date> in or after <range>` | Within or after the range |

**Range formats:**

| Format | Example |
|--------|---------|
| Absolute range | `2024-01-01 2024-01-31` |
| Relative named | `last week`, `this month`, `next quarter`, `this year` |
| ISO week | `2024-W03` |
| ISO month | `2024-01` |
| ISO quarter | `2024-Q1` |
| ISO year | `2024` |

```tasks
# Tasks due this week
due in this week

# Tasks due in January 2024
due in 2024-01

# Tasks due in Q1 2024
due in 2024-Q1
```

### Date Existence Checks

| Syntax | Description |
|--------|-------------|
| `has <date> date` | Task has this date set |
| `no <date> date` | Task does not have this date set |

```tasks
# Tasks without a due date
no due date

# Tasks with a start date
has start date
```

### Invalid Date Check

| Syntax | Description |
|--------|-------------|
| `<date> date is invalid` | Date field contains an invalid value |

### The `happens` Meta-Filter

The `happens` filter matches against the earliest of start, scheduled, and due dates on a task. It supports all the same comparison and range operators.

| Syntax | Description |
|--------|-------------|
| `happens on <value>` | Any of start/scheduled/due matches the date |
| `happens before <value>` | Earliest relevant date is before value |
| `has happens date` | Task has at least one of start/scheduled/due |
| `no happens date` | Task has none of start/scheduled/due |

```tasks
# Tasks happening this week (any date type)
happens in this week
```

## Priority Filters

| Syntax | Description |
|--------|-------------|
| `priority is <level>` | Exact priority match |
| `priority is not <level>` | Exclude exact priority |
| `priority is above <level>` | Higher than specified level |
| `priority is below <level>` | Lower than specified level |

**Priority levels** (highest to lowest): `highest`, `high`, `medium`, `none`, `low`, `lowest`

```tasks
# High priority or above
priority is above medium

# Only highest priority
priority is highest

# Exclude unprioritized tasks
priority is not none
```

## Description Filters

| Syntax | Description |
|--------|-------------|
| `description includes <string>` | Description contains text |
| `description does not include <string>` | Description does not contain text |
| `description regex matches /<regex>/` | Description matches regex |
| `description regex does not match /<regex>/` | Description does not match regex |

```tasks
# Tasks mentioning "review"
description includes review

# Case-insensitive regex
description regex matches /meeting\|standup/i
```

## Tag Filters

| Syntax | Description |
|--------|-------------|
| `has tags` | Task has at least one tag |
| `no tags` | Task has no tags |
| `tags include <tag>` | Task has the specified tag (include `#`) |
| `tags do not include <tag>` | Task does not have the specified tag |
| `tag includes <tag>` | Alias — same as `tags include` |
| `tag does not include <tag>` | Alias — same as `tags do not include` |
| `tags regex matches /<regex>/` | Any tag matches regex |
| `tags regex does not match /<regex>/` | No tag matches regex |
| `tag regex matches /<regex>/` | Alias form |
| `tag regex does not match /<regex>/` | Alias form |

```tasks
# Tasks tagged with #project
tags include #project

# Tasks with any tag matching a pattern
tag regex matches /#work-.*/
```

## Path and File Filters

### Path

| Syntax | Description |
|--------|-------------|
| `path includes <path>` | File path contains string |
| `path does not include <path>` | File path does not contain string |
| `path regex matches /<regex>/` | File path matches regex |
| `path regex does not match /<regex>/` | File path does not match regex |

### Root

| Syntax | Description |
|--------|-------------|
| `root includes <root>` | Top-level vault folder matches |
| `root does not include <root>` | Top-level vault folder does not match |
| `root regex matches /<regex>/` | Top-level folder matches regex |
| `root regex does not match /<regex>/` | Top-level folder does not match regex |

### Folder

| Syntax | Description |
|--------|-------------|
| `folder includes <folder>` | Containing folder matches |
| `folder does not include <folder>` | Containing folder does not match |
| `folder regex matches /<regex>/` | Folder matches regex |
| `folder regex does not match /<regex>/` | Folder does not match regex |

### Filename

| Syntax | Description |
|--------|-------------|
| `filename includes <filename>` | Filename contains string |
| `filename does not include <filename>` | Filename does not contain string |
| `filename regex matches /<regex>/` | Filename matches regex |
| `filename regex does not match /<regex>/` | Filename does not match regex |

```tasks
# Tasks only from the Projects folder
folder includes Projects

# Exclude daily notes
path does not include Daily Notes

# Tasks from files matching a pattern
filename regex matches /^2024-.*/
```

## Heading Filters

| Syntax | Description |
|--------|-------------|
| `heading includes <string>` | Section heading contains text |
| `heading does not include <string>` | Section heading does not contain text |
| `heading regex matches /<regex>/` | Heading matches regex |
| `heading regex does not match /<regex>/` | Heading does not match regex |

```tasks
# Tasks under headings containing "Sprint"
heading includes Sprint
```

## Recurrence Filters

| Syntax | Description |
|--------|-------------|
| `is recurring` | Task has a recurrence rule |
| `is not recurring` | Task does not recur |
| `recurrence includes <string>` | Recurrence rule text contains string |
| `recurrence does not include <string>` | Recurrence rule text does not contain string |
| `recurrence regex matches /<regex>/` | Recurrence rule matches regex |
| `recurrence regex does not match /<regex>/` | Recurrence rule does not match regex |

```tasks
# Only recurring tasks
is recurring

# Weekly recurring tasks
recurrence includes every week
```

## Dependency Filters

| Syntax | Description |
|--------|-------------|
| `is blocking` | Task is blocking other tasks |
| `is not blocking` | Task is not blocking others |
| `is blocked` | Task is blocked by other tasks |
| `is not blocked` | Task is not blocked |
| `has id` | Task has an ID assigned |
| `no id` | Task has no ID |
| `id includes <string>` | Task ID contains string |
| `id does not include <string>` | Task ID does not contain string |
| `id regex matches /<regex>/` | Task ID matches regex |
| `id regex does not match /<regex>/` | Task ID does not match regex |
| `has depends on` | Task depends on other tasks |
| `no depends on` | Task has no dependencies |

```tasks
# Actionable tasks (not blocked)
not done
is not blocked
```

## Other Filters

| Syntax | Description |
|--------|-------------|
| `exclude sub-items` | Exclude indented sub-tasks |

## Custom Filters

Use JavaScript expressions for filters not covered by built-in syntax:

```
filter by function <JavaScript expression>
```

The expression receives a `task` object with these properties:

| Property | Type | Description |
|----------|------|-------------|
| `task.isDone` | boolean | Whether task is done |
| `task.status.type` | string | Status type (TODO, DONE, etc.) |
| `task.status.symbol` | string | Status checkbox character |
| `task.status.name` | string | Status display name |
| `task.due` | TasksDate | Due date object |
| `task.done` | TasksDate | Done date object |
| `task.scheduled` | TasksDate | Scheduled date object |
| `task.start` | TasksDate | Start date object |
| `task.created` | TasksDate | Created date object |
| `task.cancelled` | TasksDate | Cancelled date object |
| `task.happens` | TasksDate | Earliest of start/scheduled/due |
| `task.description` | string | Task description text |
| `task.descriptionWithoutTags` | string | Description without tags |
| `task.tags` | string[] | Array of tag strings |
| `task.priorityName` | string | Priority as text |
| `task.priorityNumber` | number | Priority as number |
| `task.urgency` | number | Calculated urgency score |
| `task.isRecurring` | boolean | Whether task recurs |
| `task.recurrenceRule` | string | Recurrence rule text |
| `task.id` | string | Task ID |
| `task.dependsOn` | string[] | IDs this task depends on |
| `task.file.path` | string | Source file path |
| `task.file.folder` | string | Source folder |
| `task.file.filename` | string | Source filename |
| `task.file.root` | string | Top-level folder |
| `task.heading` | string | Section heading |
| `task.lineNumber` | number | Line number (zero-indexed) |
| `task.originalMarkdown` | string | Raw markdown line |

```tasks
# Tasks where due date is a weekend
filter by function task.due.moment?.day() === 0 || task.due.moment?.day() === 6
```

## Boolean Combinations

Combine multiple conditions on a single line using boolean operators. Each sub-filter must be wrapped in a delimiter.

### Operators

| Operator | Meaning |
|----------|---------|
| `AND` | Both conditions must match |
| `OR` | At least one condition must match |
| `NOT` | Negate the following condition |
| `AND NOT` | First matches, second does not |
| `OR NOT` | First matches or second does not |
| `XOR` | Exactly one of two conditions matches |

### Delimiter Types

Each boolean line must use exactly one delimiter type:

| Delimiter | Example |
|-----------|---------|
| `( )` | `(due before today) AND (priority is high)` |
| `[ ]` | `[due before today] AND [priority is high]` |
| `{ }` | `{due before today} AND {priority is high}` |
| `" "` | `"due before today" AND "priority is high"` |

### Operator Precedence

Evaluated in this order: NOT, XOR, AND, OR.

### Line Continuation

Break long boolean lines with a trailing backslash (`\`):

```tasks
(path includes inbox) OR \
(description includes #inbox) OR \
(tags include #inbox)
```

### Nesting

Nest filters using different or additional delimiters:

```tasks
NOT ( (path includes templates) OR (description includes #template) )
```

### Examples

```tasks
# Tasks due soon OR high priority
(due before next Monday) OR (priority is above medium)

# Inbox tasks from any source
(path includes inbox) OR (tags include #inbox)

# Exclude templates and archived
NOT ( (path includes templates) OR (folder includes Archive) )

# Complex: due this week AND (high priority OR tagged urgent)
(due in this week) AND ( (priority is above medium) OR (tags include #urgent) )
```

## Regular Expressions

Use regex for pattern matching in text-based filters. Wrap the pattern in forward slashes.

### Syntax

```
<field> regex matches /<pattern>/[flags]
<field> regex does not match /<pattern>/[flags]
```

### Supported Fields

All text-based filters support regex: `description`, `path`, `root`, `folder`, `filename`, `heading`, `tags`/`tag`, `status.name`, `recurrence`, `id`.

### Flags

| Flag | Meaning |
|------|---------|
| `i` | Case-insensitive matching |

### Special Characters

Escape these characters with `\` when matching literally: `[ \ ^ $ . | ? * + ( )`

### Examples

```tasks
# Match tasks starting with "Log"
description regex matches /^Log/i

# Match multiple keywords
description regex matches /waiting|blocked|pending/i

# Match time patterns (HH:MM)
description regex matches /[012][0-9]:[0-5][0-9]/

# Tags matching a prefix
tag regex matches /#project-.*/

# Files in year-based folders
folder regex matches /2024|2025/
```
