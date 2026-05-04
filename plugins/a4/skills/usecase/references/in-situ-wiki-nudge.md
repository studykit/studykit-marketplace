# In-Situ Wiki Nudge

After writing a UC file (and after any other significant issue change — new actor, domain concept, NFR, etc.), check whether the change affects existing wiki pages:

- New actor → `actors.md` likely needs an entry.
- Concept used across 3+ UCs → `domain.md` needs a glossary entry.
- Scope broadening → `context.md` Problem Framing may need refinement.

If yes, present the candidate updates and ask the user to confirm.

## Apply path

For each confirmed update:

1. Edit the affected wiki page — update the relevant `## <Section>` content, then append a dated bullet to the page's `## Change Logs` section with a markdown link to the causing issue. Create the `## Change Logs` section if it does not yet exist.


## Defer path

If the user defers the update, open a review item instead:

1. Allocate id, write `a4/review/<id>-<slug>.md` with `kind: gap`, `status: open`, `source: self`, `target: [<causing issue path>, <affected wiki basenames>]`. Frontmatter and body shape follow `${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md`.
2. The wiki close guard (run at session close and by drift detection) surfaces the unresolved impact later.

## Skip rule

Minor edits (typo, metadata-only) skip the nudge. Use judgment; the rule is "significant changes only — create, status transition, resolve."
