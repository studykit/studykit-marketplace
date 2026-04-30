# Domain Iteration Entry

Skill-specific addendum on top of the shared iterate mechanics in `../../../dev/iterate-mechanics.md`. Read that file first.

## Backlog filter

Open review items whose `target:` list contains `domain`.

## Domain-specific staleness signals

Surface alongside the backlog:

1. **New or changed UCs since last update.** Compare `domain.md`'s `## Change Logs` entries against current UC files. UCs not yet reflected in any domain entry are "needs concept review" candidates. The drift detector emits `kind: gap` review items for staleness.
2. **Stale concept signal.** If `a4/domain.md`'s `updated:` is older than the most recent UC file's `updated:` by ≥ 3 UC additions, surface this as a likely review trigger even when no review item exists.

## Domain impact propagation rule

When one area changes, surface cross-area impacts to the user:

- **Concept added/renamed** → do relationships still hold? Do any state diagrams use the old name?
- **Relationship change** → does the class diagram + body text still agree?
- **State transition added** → is the underlying concept's glossary entry still accurate?

After surfacing impacts, recommend a starting point — backlog item, specific concept, or end-to-end phase rerun.
