# In-Situ Wiki Nudge (adr Step 7)

After writing (or finalizing) an ADR, check whether it affects existing wiki pages at `a4/` root. Discover candidates via `Glob a4/*.md`. Skip silently when no wiki pages exist (fresh workspace). Use judgment — minor decisions (naming conventions, purely internal choices with no wiki-visible effect) skip the nudge entirely.

## Change-to-wiki mapping

| Change type | Likely wiki target |
|-------------|--------------------|
| Technology / framework / library choice | `architecture.md` (Technology Stack, External Dependencies) |
| Process, scope, or constraint shift | `context.md` (Problem Framing, Success Criteria) |
| New actor or role | `actors.md` |
| New domain concept | `domain.md` |
| Non-functional requirement change | `nfr.md` |

For each applicable candidate, present the proposed update and ask the user to confirm. The footnote / `## Changes` / `updated:` mechanics, the defer-via-`kind: gap`-review-item fallback, and the close guard follow [`obsidian-conventions.md §Wiki Update Protocol`](../../../references/obsidian-conventions.md). Cite this ADR (`[[adr/<id>-<slug>]]`) as the causing issue in the footnote payload.
