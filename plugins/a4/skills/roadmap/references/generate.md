# Step 3: Generate Roadmap + Tasks

Enter plan mode (the `EnterPlanMode` Claude Code primitive). Design:

## 1. Implementation strategy

Component-first / feature-first / hybrid. Detailed guidance: `./planning-guide.md`.

## 2. Milestones

Group tasks into named deliverable sets (`v1.0`, `beta`, `phase-1`). Milestones drive roadmap narrative sequencing.

## 3. Tasks (one per executable unit)

- Derive from architecture components + UC flows.
- Size: covers 1–5 related UCs, touches 1–3 components, independently testable, ≤ ~500 lines.
- File mapping (source files + unit test files following the bootstrap/codebase convention).
- Dependencies (`depends_on:` using plain `task/<id>-<slug>` strings).
- Unit test scenarios + isolation strategy.
- Acceptance criteria derived from UC flows, validation, error handling.
- Milestone assignment (`milestone:` field).
- `kind: feature` (the batch generator emits feature for UC-derived work).

## 4. Shared Integration Points

Identify any file appearing in 3+ tasks' file lists. Define the integration pattern.

## 5. Launch & Verify

**Do not author content here.** `bootstrap.md` is the single source of truth (per `../../../docs/wiki-authorship.md`); roadmap.md links to it. `/a4:run` reads `bootstrap.md` directly.

## Write artifacts

Exit plan mode.

**`a4/roadmap.md` body** — write `<plan>` with H3 subsections (Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points) per `../../../references/roadmap-authoring.md` §Body shape. Launch & Verify is a one-line link to `[bootstrap](bootstrap.md)` — never inline content. Shared Integration Points is emitted only when a file appears in 3+ tasks. Append a `<change-logs>` bullet citing the driving wiki/issue.

**Per-task files** — allocate ids via `allocate_id.py`, write `a4/task/feature/<id>-<slug>.md` per `../../../references/task-feature-authoring.md` (`kind: feature`, `status: pending`). The roadmap's Milestones subsection references them via standard markdown links pointing into `feature/<id>-<slug>.md`.

## Refresh reverse links

After all task files are written, refresh the reverse link on each UC so `ready → implementing` will pass mechanical validation:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/refresh_implemented_by.py" \
  "$(git rev-parse --show-toplevel)/a4"
```

This back-scans every task's `implements:` list and writes `implemented_by: [...]` onto each referenced UC. The script is idempotent.
