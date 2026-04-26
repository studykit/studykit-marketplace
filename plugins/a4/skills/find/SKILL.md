---
name: find
description: "This skill should be used when the user wants to search, list, or query existing items in the a4/ workspace by frontmatter — for example: open review items, tasks for a specific milestone, everything that references a given use case, items touching the architecture wiki, items with a custom frontmatter field, or items updated since a date. Triggers: 'find', 'search', 'list', 'show me all', 'which tasks', 'which reviews', 'what references', 'what depends on', 'what implements', 'what touches the X wiki', 'find by tag', 'find by label', 'find by milestone'. Translates the user's natural-language query into a single `scripts/search.py` invocation and surfaces the result. Reverse lookups (e.g. tasks implementing a UC, items depending on something) are computed by forward-field back-scan so results are always consistent even when stored-reverse fields are stale. Does NOT search body text — frontmatter only. For body grep, use Grep directly. For workspace-wide aggregate state, use `/a4:dashboard`."
argument-hint: <natural-language query, or raw search.py flags>
context: fork
model: haiku
allowed-tools: Bash
---

# a4 Workspace Search

Translate the user's request into a single `scripts/search.py` call and relay its output. Default output is a one-line-per-match table; pass `--json` when the caller will parse the result.

Argument: **$ARGUMENTS**

## Step 1: Resolve workspace root

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
```

If the command fails or `$ROOT/a4/` is not a directory, abort with a clear message — there is no workspace to search.

## Step 2: Build the search.py invocation

`scripts/search.py` is the single entry point. Its full surface is documented in its `--help` output and in the usage block at the top of the file. Available filters (all AND-combined; flags repeat to OR within a filter):

| Flag | Meaning |
|------|---------|
| `--folder <name>` | usecase / task / review / decision / idea / spark / wiki / archive |
| `--status <value>` | family-validated enum (e.g. `open`, `pending`, `ready`, `implementing`, `shipped`, `final`) |
| `--kind <value>` | task: feature/spike/bug · review: finding/gap/question · wiki: context/domain/architecture/actors/nfr/roadmap/bootstrap |
| `--id <int>` | numeric id |
| `--slug <substr>` | case-sensitive substring on filename stem |
| `--label <value>` | matches both `labels:` and `tags:` |
| `--milestone <name>` | exact milestone-name match |
| `--updated-since YYYY-MM-DD` / `--updated-until YYYY-MM-DD` | date-range filter on `updated:` |
| `--target <ref>` | review.target equals this |
| `--wiki-impact <basename>` | bare wiki basename present in `wiki_impact` |
| `--references <ref>` | back-scan all forward relation fields (`depends_on`, `implements`, `justified_by`, `target`, `wiki_impact`, `supersedes`, `promoted`, `parent`, `related`, `research`) for items pointing at `<ref>` |
| `--references-via <field>` | restrict `--references` to a single forward field |
| `--field NAME=VALUE` | exact match on any frontmatter field, including custom/unknown ones; for list values, any element matches |
| `--has-field NAME` | require a frontmatter field to be present and non-null |
| `--include-archived` | also scan `a4/archive/` (auto-enabled for `--folder archive`) |
| `--json` | structured JSON instead of one-line text |

**Translation guide for natural-language queries:**

- "open reviews" → `--folder review --status open`
- "tasks for v1.0" → `--folder task --milestone v1.0`
- "what implements usecase/3-search-history" → `--references usecase/3-search-history --references-via implements`
- "what references usecase/3" or "what depends on it" → `--references usecase/3-...` (omit `--references-via` for any-direction back-scan)
- "reviews touching the architecture wiki" → `--folder review --wiki-impact architecture`
- "items tagged perf" → `--label perf`
- "items updated since 2026-04-01" → `--updated-since 2026-04-01`
- "items with custom field source set to drift-detector" → `--field source=drift-detector`
- "all decisions" → `--folder decision`
- If the user just wants raw output and passes flags directly (e.g. `/a4:find --folder task --status pending`), pass `$ARGUMENTS` through verbatim.

If the query is ambiguous (e.g. "show me everything"), ask one clarifying question before running. Do not guess between mutually exclusive interpretations.

## Step 3: Run the script

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "$ROOT/a4" <translated-flags>
```

Surface stdout verbatim. The script exits non-zero on invalid inputs (unknown folder/status/kind for the requested family, malformed `--field` spec, bad date) — surface stderr and stop without retrying.

If the result is `(no matches)`, optionally suggest a relaxed query (e.g. drop a filter, broaden a folder set) and offer to rerun.

## Step 4: Format the response

- **Default text output** is already one-line-per-match (`<ref> | <status> | <kind> | <title>`). Relay it as-is inside a fenced block.
- For more than ~30 matches, summarize counts by folder and offer to narrow the query.
- If the caller asked for JSON, run with `--json` and relay the JSON inside a fenced block.
- Do not editorialize the contents of individual items — `find` is a query tool, not an analyst. For deeper diagnosis on a specific item the user should invoke `/a4:compass <ref>`.

## Notes

- This skill is read-only. It never writes a file or mutates frontmatter.
- Body text is **not** searched. Use `Grep` directly for body grep.
- Reverse lookups always recompute from forward fields; stored-reverse fields (`implemented_by`, `cited_by`) are intentionally ignored so results stay consistent even when refresh scripts have not run.
- For workspace-wide aggregate state (counts, drift alerts, blocked items, milestone progress), use `/a4:dashboard` instead.
