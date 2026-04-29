# In-Situ Wiki Nudge (spec Step 7)

After writing (or activating) a spec, check whether it affects existing wiki pages at `a4/` root. Discover candidates via `Glob a4/*.md`. Skip silently when no wiki pages exist (fresh workspace). Use judgment — narrow specs (renderer-internal grammar, purely structural shape with no wiki-visible effect) skip the nudge entirely.

## Change-to-wiki mapping

| Spec scope | Likely wiki target |
|------------|--------------------|
| Technology / framework / protocol choice | `architecture.md` (Technology Stack, External Dependencies) |
| Process, scope, or constraint shift | `context.md` (Problem Framing, Success Criteria) |
| New actor or role | `actors.md` |
| New domain concept | `domain.md` |
| Non-functional requirement change | `nfr.md` |

For each applicable candidate, present the proposed update and ask the user to confirm. The `## Change Logs` / `updated:` mechanics, the defer-via-`kind: gap`-review-item fallback, and the close guard follow [`body-conventions.md §Wiki Update Protocol`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md). Cite this spec as a standard markdown link (`[spec/<id>-<slug>](../spec/<id>-<slug>.md)`, with the relative path computed from the wiki page) in the `## Change Logs` bullet.
