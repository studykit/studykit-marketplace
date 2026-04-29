# Roadmap Iteration Entry

Skill-specific addendum on top of `../../../docs/iterate-mechanics.md`. Read that file first for filter / backlog presentation / writer call / footnote / discipline rules.

## Backlog filter

Open review items whose `target:` list contains `roadmap` or any `task/*` path.

## Roadmap-specific work between writer calls

- **Re-emit revised roadmap / task files** in place of hand-edits when the resolution restructures milestones, dependency graph, or task split.
- **Scoped roadmap-reviewer rerun** — after revising tasks for a finding, run `roadmap-reviewer` once over the revised subset (not the full roadmap) and only proceed if the scoped review passes. This is the inline review loop unique to roadmap.
- **Cascade awareness** — if a task's `depends_on` changes, downstream tasks may also need adjustments; surface those to the user before resolving.
