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
- Dependencies (`depends_on:` using plain `<type>/<id>-<slug>` strings, where `<type>` is the dependent task's family — typically `task/<id>-<slug>` for the batch path).
- Unit test scenarios + isolation strategy.
- Acceptance criteria derived from UC flows, validation, error handling.
- Milestone assignment is captured in the roadmap milestone narrative (links from each milestone to the UCs it ships); tasks themselves do not carry a `milestone:` field.
- `type: task` (the batch generator emits feature for UC-derived work).

## 4. Shared Integration Points

Identify any file appearing in 3+ tasks' file lists. Define the integration pattern.

## 5. Launch & Verify

**Do not author content here.** `bootstrap.md` is the single source of truth (per `../../../docs/wiki-authorship.md`); roadmap.md links to it. `/a4:run` reads `bootstrap.md` directly.

## Write artifacts

Exit plan mode.

**`a4/roadmap.md` body** — write `## Plan` with H3 subsections (Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points) per `../../../references/roadmap-authoring.md` §Body shape. Launch & Verify is a one-line link to `[bootstrap](bootstrap.md)` — never inline content. Shared Integration Points is emitted only when a file appears in 3+ tasks. Append a `## Change Logs` bullet citing the driving wiki/issue.

**Per-task files** — allocate ids via `allocate_id.py`, write `a4/task/<id>-<slug>.md` per `../../../references/task-authoring.md` (`type: task`, `status: pending`). The roadmap's Milestones subsection references them via standard markdown links pointing into `task/<id>-<slug>.md`.

The UC ↔ task reverse view (which tasks implement a UC) is computed on demand by `search.py` and roadmap surfaces — there is no UC frontmatter field to refresh.
