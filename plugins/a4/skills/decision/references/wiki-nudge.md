# In-Situ Wiki Nudge (decision Step 7)

After writing (or finalizing) a decision, check whether it affects existing wiki pages at `a4/` root. Discover candidates via `Glob a4/*.md`. Skip silently when no wiki pages exist (fresh workspace). Use judgment — minor decisions (naming conventions, purely internal choices with no wiki-visible effect) skip the nudge entirely.

## Change-to-wiki mapping

| Change type | Likely wiki target |
|-------------|--------------------|
| Technology / framework / library choice | `architecture.md` (Technology Stack, External Dependencies) |
| Process, scope, or constraint shift | `context.md` (Problem Framing, Success Criteria) |
| New actor or role | `actors.md` |
| New domain concept | `domain.md` |
| Non-functional requirement change | `nfr.md` |

## Apply confirmed updates

For each applicable candidate, present the proposed update and ask the user to confirm. For every confirmed update:

1. Edit the wiki page — update the affected section, append a footnote marker `[^N]` inline (monotonic per file), and append a `## Changes` line `[^N]: <YYYY-MM-DD> — [[decision/<id>-<slug>]]` pointing to this decision.
2. Bump the wiki page's `updated:` frontmatter to today.

See [`obsidian-conventions.md §Wiki Update Protocol`](../../../references/obsidian-conventions.md) for footnote format.

## Defer via review item

If the user defers any update, open a review item instead so the gap does not disappear:

1. Allocate an id: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"`.
2. Write `a4/review/<id>-<slug>.md` with:
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: decision/<decision-id>-<slug>`
   - `wiki_impact: [<affected wiki basenames>]`

The wiki close guard (at session close) and drift detector (between sessions) re-surface unresolved impact later.
