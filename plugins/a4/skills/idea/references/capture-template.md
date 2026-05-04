# Idea Capture Template

Write to `<project-root>/a4/idea/<id>-<slug>.md`:

```markdown
---
type: idea
id: <id>
title: <title>
status: open
promoted: []
related: []
labels: []
---
```

## Fields

- `type: idea` — literal; selects the per-type body shape documented at `references/<type>-authoring.md` (idea has no required body sections).
- `id:` — the integer from `allocate_id.py`, as a YAML int (no quotes).
- `title:` — the user's trimmed argument. If it contains characters that break bare YAML (colons, `#`, leading/trailing whitespace, quotes), wrap in double quotes and escape as needed.
- `status: open` — literal.
- `promoted: []`, `related: []`, `labels: []` — empty lists as placeholders. `[]` (not omitted) because these fields are part of the idea shape; their emptiness is noteworthy.

The body is empty on capture (idea has no required tags). Longer ideas can be edited in later — this skill writes the minimum.
