# Cache Projection Boundary

Workflow cache projection details are implementation-owned.

This document exists only to protect documentation boundaries. It is not a
projection schema and must not list provider-specific cache files, sidecar names,
frontmatter fields, or pending-write shapes.

- Main-facing authoring docs describe only semantic authoring behavior that a
  content-writing assistant needs.
- `workflow-operator` instructions describe script selection, required inputs,
  result handoff, and the rule that provider/cache mutations go through workflow
  scripts.
- Contributor implementation work uses provider/cache code and tests as the
  source of truth for projection shape.
- If projection shape changes, update the relevant scripts and tests in the same
  change. Add comments near code when an invariant is non-obvious.
