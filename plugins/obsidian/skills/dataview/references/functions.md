# Dataview Functions Reference

All functions are available in both DQL `WHERE`/`TABLE`/`LIST` expressions and DataviewJS via `dv.func.<name>()` (though most are used directly in DQL).

## Constructors

Functions that create or convert values into specific types.

| Function | Signature | Description |
|----------|-----------|-------------|
| `object` | `object(key1, value1, key2, value2, ...)` | Create an object from alternating key-value pairs |
| `list` | `list(val1, val2, ...)` | Create a list; `array` is an alias |
| `date` | `date(any)` | Parse a date from text, date, or link with a date in its name |
| `date` | `date(text, format)` | Parse a date using Luxon format tokens |
| `dur` | `dur(any)` | Parse a duration from text (e.g., `"3 hours"`) |
| `number` | `number(string)` | Extract the first number from a string |
| `string` | `string(any)` | Convert any value to its string representation |
| `link` | `link(path, [display])` | Create a link to a file; optional display text |
| `embed` | `embed(link, [embed?])` | Convert a link to an embedded link |
| `elink` | `elink(url, [display])` | Create an external URL link for rendering |
| `typeof` | `typeof(any)` | Return the type name: `"number"`, `"string"`, `"date"`, etc. |

### Date Constructor Shortcuts

```
date(today)       - Current date
date(now)         - Current date and time
date(tomorrow)    - Next day
date(yesterday)   - Previous day
date(sow)         - Start of week
date(eow)         - End of week
date(som)         - Start of month
date(eom)         - End of month
date(soy)         - Start of year
date(eoy)         - End of year
```

### Examples

```dataview
TABLE dateformat(date(file.name), "yyyy-MM-dd") AS "Date"
FROM "Journal"
WHERE date(file.name) != null
```

```dataview
LIST dur("2 hours 30 minutes")
```

## String Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `contains` | `contains(string, substr)` | Check if string contains substr (case-sensitive) |
| `icontains` | `icontains(string, substr)` | Case-insensitive containment check |
| `econtains` | `econtains(string, substr)` | Exact containment (no recursion into nested structures) |
| `containsword` | `containsword(string, word)` | Check if string contains word as a whole word |
| `startswith` | `startswith(string, prefix)` | Check if string starts with prefix |
| `endswith` | `endswith(string, suffix)` | Check if string ends with suffix |
| `replace` | `replace(string, pattern, replacement)` | Replace all occurrences of pattern |
| `regextest` | `regextest(pattern, string)` | Test if string matches regex (partial match) |
| `regexmatch` | `regexmatch(pattern, string)` | Test if entire string matches regex |
| `regexreplace` | `regexreplace(string, pattern, replacement)` | Replace using regex pattern |
| `lower` | `lower(string)` | Convert to lowercase |
| `upper` | `upper(string)` | Convert to uppercase |
| `split` | `split(string, delimiter, [limit])` | Split string into list by delimiter |
| `substring` | `substring(string, start, [end])` | Extract substring by index |
| `truncate` | `truncate(string, length, [suffix])` | Truncate to length with optional suffix (default `"..."`) |
| `padleft` | `padleft(string, length, [char])` | Pad left side to reach target length |
| `padright` | `padright(string, length, [char])` | Pad right side to reach target length |
| `length` | `length(string)` | Return character count |

### Examples

```dataview
TABLE file.name
FROM "Notes"
WHERE icontains(file.name, "meeting")
```

```dataview
LIST replace(file.name, "-", " ")
FROM "Journal"
```

```dataview
TABLE truncate(summary, 50) AS "Summary"
FROM #article
```

## Numeric Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `round` | `round(number, [digits])` | Round to specified decimal places (default: 0) |
| `trunc` | `trunc(number)` | Remove decimal part (truncate toward zero) |
| `floor` | `floor(number)` | Round down to nearest integer |
| `ceil` | `ceil(number)` | Round up to nearest integer |
| `min` | `min(a, b, ...)` | Return the smallest value |
| `max` | `max(a, b, ...)` | Return the largest value |
| `sum` | `sum(array)` | Sum all numeric values in a list |
| `product` | `product(array)` | Multiply all values in a list |
| `average` | `average(array)` | Compute the arithmetic mean |
| `reduce` | `reduce(array, operand)` | Reduce using `"+"`, `"-"`, `"*"`, `"/"`, `"&"`, `"|"` |
| `minby` | `minby(array, function)` | Return the element with the minimum value of function |
| `maxby` | `maxby(array, function)` | Return the element with the maximum value of function |
| `abs` | `abs(number)` | Return the absolute value |

### Examples

```dataview
TABLE round(rating, 1) AS "Rating", sum(rows.pages) AS "Total Pages"
FROM #book
GROUP BY genre
```

```dataview
LIST "Average: " + round(average(rows.score), 2)
FROM #exam
GROUP BY subject
```

## Date Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `date` | `date(any)` | Parse date from ISO string, date, or link |
| `date` | `date(text, format)` | Parse date with custom Luxon format tokens |
| `dur` | `dur(any)` | Parse duration from string |
| `dateformat` | `dateformat(date, format)` | Format a date using Luxon format tokens |
| `durationformat` | `durationformat(duration, format)` | Format a duration string |
| `striptime` | `striptime(date)` | Remove the time component, keeping only the date |
| `localtime` | `localtime(date)` | Convert a date to the local timezone |

### Luxon Format Tokens (for `dateformat`)

| Token | Meaning | Example |
|-------|---------|---------|
| `yyyy` | 4-digit year | `2024` |
| `yy` | 2-digit year | `24` |
| `MM` | 2-digit month | `03` |
| `MMM` | Short month name | `Mar` |
| `MMMM` | Full month name | `March` |
| `dd` | 2-digit day | `15` |
| `EEE` | Short weekday | `Fri` |
| `EEEE` | Full weekday | `Friday` |
| `HH` | 24-hour hour | `14` |
| `mm` | Minutes | `30` |
| `ss` | Seconds | `45` |

### Date Arithmetic

Dates support addition and subtraction with durations:

```dataview
TABLE due, (due - date(today)) AS "Days Left"
FROM #task
WHERE due != null AND due >= date(today)
SORT due ASC
```

```dataview
LIST
FROM "Journal"
WHERE file.cday >= date(today) - dur(30 days)
```

### Examples

```dataview
TABLE dateformat(file.ctime, "yyyy-MM-dd HH:mm") AS "Created"
FROM "Notes"
SORT file.ctime DESC
```

```dataview
TABLE dateformat(due, "EEEE, MMMM dd") AS "Due Date"
FROM #task
WHERE due >= date(som) AND due <= date(eom)
```

## List / Array Functions

These functions operate on lists (arrays). Many also work on strings or objects where noted.

| Function | Signature | Description |
|----------|-----------|-------------|
| `length` | `length(list)` | Return the number of elements |
| `contains` | `contains(list, value)` | Check if list contains value (case-sensitive) |
| `icontains` | `icontains(list, value)` | Case-insensitive list containment |
| `econtains` | `econtains(list, value)` | Exact containment (no nested recursion) |
| `sort` | `sort(list)` | Sort elements in ascending order |
| `reverse` | `reverse(list)` | Reverse the list order |
| `flat` | `flat(list, [depth])` | Flatten nested lists to specified depth (default: infinity) |
| `unique` | `unique(list)` | Remove duplicate values |
| `slice` | `slice(list, [start], [end])` | Return a portion of the list (zero-indexed) |
| `filter` | `filter(list, predicate)` | Keep elements matching the predicate |
| `map` | `map(list, function)` | Transform each element |
| `join` | `join(list, [separator])` | Join elements into a string (default separator: `", "`) |
| `nonnull` | `nonnull(list)` | Remove null values from the list |
| `firstvalue` | `firstvalue(list)` | Return the first non-null value |
| `all` | `all(list)` or `all(list, predicate)` | Check if all elements are truthy or match predicate |
| `any` | `any(list)` or `any(list, predicate)` | Check if any element is truthy or matches predicate |
| `none` | `none(list)` or `none(list, predicate)` | Check if no elements are truthy or match predicate |
| `extract` | `extract(object, key1, key2, ...)` | Extract specific fields from an object |

### Lambda Syntax

Functions like `filter`, `map`, `all`, `any`, `none`, `minby`, and `maxby` accept lambda expressions:

```
(x) => x.field > 5
(item) => contains(item, "keyword")
```

### Examples

```dataview
TABLE join(file.tags, ", ") AS "Tags"
FROM "Projects"
```

```dataview
TABLE length(file.tasks) AS "Total Tasks",
      length(filter(file.tasks, (t) => t.completed)) AS "Done"
FROM #project
```

```dataview
LIST flat(rows.file.tags)
FROM "Notes"
GROUP BY file.folder
```

```dataview
TABLE filter(file.outlinks, (l) => !contains(string(l), "Template")) AS "Links"
FROM "Docs"
```

## Utility Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `default` | `default(field, value)` | Return `value` if `field` is null/empty |
| `choice` | `choice(condition, ifTrue, ifFalse)` | Return `ifTrue` when condition is truthy, else `ifFalse` |
| `meta` | `meta(link)` | Return metadata object for a link |
| `hash` | `hash(seed, [text], [variant])` | Generate a hash value |
| `display` | `display(value)` | Convert value while preserving display properties |
| `currencyformat` | `currencyformat(number, [currency])` | Format number as currency |

### `meta()` Fields

The `meta(link)` function returns an object with:

| Property | Description |
|----------|-------------|
| `meta(link).display` | Display text of the link |
| `meta(link).embed` | Whether the link is embedded |
| `meta(link).path` | File path portion |
| `meta(link).subpath` | Heading or block reference |
| `meta(link).type` | `"file"`, `"header"`, or `"block"` |

### Examples

```dataview
TABLE default(status, "Not Set") AS "Status",
      choice(rating >= 4, "Good", "Needs Work") AS "Verdict"
FROM #book
```

```dataview
TABLE default(due, "No deadline") AS "Due",
      choice(completed, "Done", "Pending") AS "Status"
FROM #task
```

```dataview
TABLE currencyformat(price, "USD") AS "Price"
FROM #product
WHERE price != null
SORT price DESC
```
