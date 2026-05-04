# Breakdown Iteration Entry

Skill-specific addendum. Walk open review items targeting this stage as a stage-specific mailbox: filter, present as priority table, edit `status` directly.

## Backlog filter

Open review items whose `target:` list contains a task path under one of the four issue family folders (`task/`, `bug/`, `spike/`, `research/`).

`target: roadmap` is no longer accepted (the type was retired with the prior `roadmap` skill). Older review items still carrying `target: roadmap` are stale; surface them to the user with a recommendation to retarget at `task/<id>-<slug>` or `architecture` and close.

## Breakdown-specific work between writer calls

- **Re-emit revised task files** in place of hand-edits when the resolution restructures dependency or scope. Allocate fresh ids only for genuinely new tasks; re-use existing ids when the resolution is a body / frontmatter edit on an existing task.
- **Scoped breakdown-reviewer rerun** — after revising tasks for a finding, run `breakdown-reviewer` once over the revised subset (not the full task set) and only proceed if the scoped review passes. This is the inline review loop unique to this skill.
- **Cascade awareness** — if a task's `depends_on` changes, downstream tasks may also need adjustments; surface those to the user before resolving.
- **Drift escalation** — if multiple iterations surface the same root cause (e.g., the upstream UC keeps producing ambiguous AC), the right move is `/a4:usecase iterate` upstream rather than further task revisions.
