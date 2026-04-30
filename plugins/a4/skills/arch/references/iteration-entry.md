# Architecture Iteration Entry

Skill-specific addendum on top of the shared iterate mechanics in `../../../workflows/iterate-mechanics.md`. Read that file first for filter / backlog presentation / writer call / footnote / discipline rules.

## Backlog filter

Open review items whose `target:` list contains `architecture`.

## Architecture-specific staleness signals

Surface alongside the backlog:

1. **New or changed UCs.** Compare `architecture.md`'s `## Change Logs` entries against current UC files. UCs not yet cited in any change-log entry are "needs coverage" candidates.
2. **UC ↔ actor / domain drift.** For each `## Components` Information Flow subsection in `architecture.md`, check that the referenced UCs and components still exist as current files / component sections.

## Architecture impact propagation rule

When one area changes, surface cross-area impacts to the user — do not silently assume they're fine:

- **Technology stack change** → do components need restructuring? Do test tools need changing?
- **Component change** → do information flows still hold? Do interface contracts need updating?
- **Test strategy change** → does this affect how components are designed for testability?

After surfacing impacts, recommend a starting point — backlog item, specific new UC, or phase to revisit.
