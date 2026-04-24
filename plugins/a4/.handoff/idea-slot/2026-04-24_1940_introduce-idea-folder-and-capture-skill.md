---
timestamp: 2026-04-24_1940
topic: idea-slot
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1940. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: `a4/idea/` slot + `/a4:idea` quick-capture skill — `idea-slot` thread opened

This is the first handoff on the `idea-slot` thread. It resolves an item parked in the `a4-redesign` thread (2026-04-23_2119 handoff) that was never picked up before that thread closed at 2026-04-24_1859.

## Why this thread exists (and why it is *not* a continuation of `a4-redesign`)

The `a4-redesign` thread was declared closed at 2026-04-24_1859 with "13/13 ADR Next Steps complete, No new thread is queued." That closure was point-in-time accurate **with respect to the ADR**, but the 2026-04-23_2119 handoff had separately parked three items that never entered the ADR's Next Steps list:

> 3. **Inbox slot design.** Whether to adopt callgraph-service's `ideas.md` file pattern verbatim, add a `a4/inbox.md` with the same `active | promoted | discarded` schema, and how compass's INDEX surfaces it.
> 4. **Experiments / PoC slot.**
> 5. **DECISIONS.md / ADR layer.**

Item 5 was implicitly resolved by the 2026-04-23 spec-as-wiki-and-issues ADR (via the `decision/` folder). Item 3 was the load-bearing parked item that silently disappeared from the agenda. This session resolves item 3. Item 4 (experiments) remains parked.

A new thread (`idea-slot`) rather than reopening `a4-redesign` because:
- `a4-redesign` was explicitly closed with an authoritative statement "no new thread is queued."
- This session's work is narrowly scoped (one new file type, one new skill, minimal schema/doc updates) and does not alter any a4-redesign ADR decision.
- The 2026-04-24_1859 closure handoff's instruction is explicit: "If the user starts a new topic, begin a fresh thread (new `topic:` slug, new subfolder under `plugins/a4/.handoff/`)."

## Pre-handoff commit

- **`1d33edbe2`** — `feat(a4): introduce idea/ folder and /a4:idea quick-capture skill`. 11 files; new `plugins/a4/spec/2026-04-24-idea-slot.decide.md` + `plugins/a4/skills/idea/SKILL.md`; modifications to 3 scripts, 3 references, README, compass SKILL.md, marketplace.json (1.1.1 → 1.2.0).

Working tree was clean of unrelated drift at the start of this session.

## Primary reads for next session

If the next session needs context on anything this session touched:

1. **`plugins/a4/spec/2026-04-24-idea-slot.decide.md`** — the authoritative ADR. Context, boundary-with-review rationale, schema, rejected alternatives (13 entries), Next Steps (all `[x]`).
2. **`plugins/a4/skills/idea/SKILL.md`** — the `/a4:idea <line>` quick-capture skill. `disable-model-invocation: true`; user-triggered only.
3. **`plugins/a4/references/frontmatter-schema.md`** — now includes an `## Idea` section + updated scope table + updated `promoted` relationship field entry.
4. This handoff.

## What this session accomplished

### Design decisions (recorded here so the next session doesn't relitigate)

1. **Idea is a fifth issue-type folder, not a single-file accumulator.** The user initially was open to either form. The conversation explored callgraph-service's `ideas.md` pattern (single file, line entries) versus per-item files extensively — including a dedicated "입도(granularity)" clarification round — before the user chose Jira-issue-style per-item files: `a4/idea/<id>-<slug>.md`.
2. **Capture cost is held to ~30 seconds via the `/a4:idea` skill.** The main concern about per-item files (friction defeats the quick-capture purpose) is addressed by the skill absorbing id allocation + slug generation + frontmatter. The user types the idea as a one-line argument; everything else is automated.
3. **Boundary with `review/` is drawn on progress-dependency, not content.** Rule of thumb: "If ignoring this blocks or degrades current spec work, it is a review item. If not, it is an idea." Review items carry `target:` and are bound to the current spec; ideas are independent by definition (no `target:` in the schema).
4. **Schema is deliberately minimal.** User explicitly rejected `priority` and `source`. Also excluded: `target` (would blur the review boundary), `kind` (only one kind of idea), `milestone` (ideas are pre-scheduling). Required fields: `id`, `title`, `status`, `created`, `updated`. Optional: `promoted`, `related`, `labels`.
5. **Status vocabulary matches spark/brainstorm.** `open | promoted | discarded`. Consistency beats novelty.
6. **Body is free-form.** User chose free-form over any required template. Optional suggested sections (`## Why this matters`, `## Notes`) are documented as convention but not validated.
7. **Folder named `idea/`, not `inbox/`.** `inbox` is a container metaphor that fits the single-file accumulator model; `idea/` matches the singular-issue-type-noun convention already used by `usecase/`, `task/`, `review/`, `decision/`.
8. **Promotion is manual today.** No `/a4:idea-promote` skill. When an idea graduates, the user edits `status:` and `promoted:` by hand and creates the target artifact separately. A promotion skill may be added later if repeated manual promotion becomes a pain point — explicitly deferred.

### Files changed (11 files, one commit)

**New**:
- `plugins/a4/spec/2026-04-24-idea-slot.decide.md` — ADR.
- `plugins/a4/skills/idea/SKILL.md` — the `/a4:idea <line>` skill.

**Modified scripts**:
- `plugins/a4/scripts/allocate_id.py` — `ISSUE_FOLDERS` tuple gains `"idea"`; docstring updated. Id uniqueness now includes idea files.
- `plugins/a4/scripts/validate_frontmatter.py` — `ISSUE_FOLDERS` gains `"idea"`; new `idea` entry in `SCHEMAS` (required: id/title/status/created/updated; status enum: open/promoted/discarded; int: id; date: created/updated; path-list: promoted/related).
- `plugins/a4/scripts/index_refresh.py` — `ISSUE_FOLDERS` gains `"idea"`; `TERMINAL_STATUSES["idea"] = {"promoted", "discarded"}`; `IN_PROGRESS_STATUSES["idea"] = set()`; new `section_open_ideas` function rendering both a dataview block and static fallback; wired into `render_index` between `section_recent_activity` and `section_spark`. Open issues table gains an idea row; Recent activity and Open issues dataview FROM clauses updated.

**Modified docs**:
- `plugins/a4/references/frontmatter-schema.md` — scope table now lists `a4/idea/` under the Issue family; new `## Idea` section below `## Decision`; `promoted` relationship entry updated to list both `spark/brainstorm` and `idea` as sources.
- `plugins/a4/references/obsidian-conventions.md` — issue-bodies bullet includes `idea/*.md`.
- `plugins/a4/references/obsidian-dataview.md` — "Seven INDEX sections; six carry a dataview block" → "Eight … seven"; new `### Open ideas` subsection with the INDEX block; Open issues and Recent activity FROM clauses updated; these match `index_refresh.py` verbatim per the sync-requirement note at the top of that file.
- `plugins/a4/skills/compass/SKILL.md` — Step 0 folder enumeration now includes `idea`.
- `plugins/a4/README.md` — layout diagram gains `idea/<id>-<slug>.md`; skills table gains `/a4:idea`; Wiki-vs-issues bullet list gains an "Ideas vs. reviews" entry stating the boundary; INDEX sections list updated.

**Version bump**:
- `.claude-plugin/marketplace.json` — a4 `1.1.1 → 1.2.0`. **Minor** bump because a new user-facing skill + new file type is feature-additive, not breaking.

### Verification run (not committed)

Sanity-checked each script at a temporary workspace (`/tmp/a4-idea-test`, since deleted):

- `allocate_id.py` — correctly returns `max(id) + 1` across mixed `usecase/` + `idea/` files. `--list` and `--check` include the idea folder.
- `validate_frontmatter.py` — valid idea passes; `status: foo` rejected with the correct enum-violation error and exit 2.
- `index_refresh.py --dry-run` — renders the Open issues table with an `idea` row; renders the new `## Open ideas (N)` section with a proper dataview block and static fallback; idea files appear in Recent activity.

## Design questions resolved during the session

### Why not `a4/inbox.md` single-file accumulator?

The callgraph-service pattern (one file, per-line entries like `- [active] idea`) was discussed in detail, including the friction-cost argument for it. The user ultimately chose per-item files for these reasons:
- Consistency with the other four issue types — all follow `<folder>/<id>-<slug>.md`.
- Enables dataview queries per idea (status, labels, related) the same way other issues are queryable.
- Scales cleanly as the idea count grows — a single file with hundreds of entries would become unwieldy.
- The friction-cost concern is solved at the skill layer: `/a4:idea <line>` makes capture feel single-line despite producing a per-item file.

### Why not reuse `review/` with `kind: idea`?

The boundary is sharp enough to warrant a distinct type:
- Review lifecycle (`open | in-progress | resolved | dismissed`) says "you work on it." Idea lifecycle (`open | promoted | discarded`) says "you graduate or drop it — the idea itself is not worked on, its target artifact is."
- Review items are bound to current progress via `target:`. Ideas are independent by definition and must not carry `target:`.
- INDEX surfaces reviews alongside drift alerts (both demand attention on the current spec). Ideas belong on a different surface (a backlog of possibilities).

### Why no `source:` field?

`source:` on review items distinguishes `self` / `drift-detector` / `<reviewer-agent-name>` — all of which are meaningfully different and drive different compass behaviors. For ideas, effectively everything collapses to `self` (user-authored capture). The field would carry no information. If a future flow needs to distinguish (e.g., ideas imported from an external feedback system), the field can be added then without schema migration — `validate_frontmatter.py` ignores unknown fields.

### Why no `priority:`?

Prioritization happens at the graduation target, not at the idea. When an idea becomes a usecase/task, that target has its own priority machinery. Putting `priority` on ideas would create two knobs that must be kept in sync and implies a ranking that is premature at capture time (the whole point of capture is "I don't want to decide yet").

### Why no explicit `discarded_reason:`?

Considered for parity with `spark-brainstorm`'s `discarded_reason:` (which, notably, is a documented field no skill actually writes). Ideas are cheap to discard; requiring a reason adds friction on the discard path, which is the second-most common terminal transition. A body `## Why discarded` is suggested but optional.

### Why not include `/a4:idea-promote <id>`?

YAGNI. Manual promotion is:
1. Open the idea file.
2. Change `status: open` → `status: promoted`.
3. Set `promoted: [<target-path>]`.
4. Bump `updated:`.
5. Create the target artifact separately.

Four field edits and a file write. Not worth a skill until repeated manual promotion becomes a pain point. Explicitly deferred; new ADR if/when it surfaces.

## What this session did NOT do

- **Experiments / PoC slot** (item 4 from the 2026-04-23_2119 parked list). Distinct from the inbox/idea problem — experiments are execution-phase artifacts (PoCs, temporary investigations), not pre-capture thoughts. Conflating would dilute both. Remains parked.
- **`/a4:idea-promote` skill.** Deferred until pain surfaces.
- **Auto-promote detection** (spotting that a new usecase title matches an existing idea title and prompting the user to close the idea). Premature.
- **Pre-existing idea data migration.** No legacy idea data exists in any known a4 workspace, so nothing to migrate. If a future workspace imports ideas from an external source (e.g., a callgraph-service `ideas.md`), a one-shot splitter can be written then.
- **Compass Step 3 diagnosis layer for ideas.** Ideas are a backlog, not a next-action surface. Compass's Step 3 diagnoses *actionable* work (drift, open reviews, active tasks, blocked items). Open ideas are visible via INDEX's dedicated section but intentionally not surfaced as "next action" candidates.
- **Body template for ideas.** User chose free-form. Suggested optional sections are documented as convention, not enforced.
- **Separate ADR for the skill.** `/a4:idea` is tooling that implements the ADR's capture UX — not itself a design decision warranting its own ADR. Documented in the idea-slot ADR and this handoff.

## How the hooks + validator treat ideas (no config needed)

The session-scoped validation hooks added in the `a4-redesign` thread (`plugins/a4/hooks/`) automatically cover ideas:

- `record-edited-a4.sh` (PostToolUse) records any edited `.md` under `$CLAUDE_PROJECT_DIR/a4/` — includes `a4/idea/**/*.md` with no code change because the filter is path-based, not type-based.
- `validate-edited-a4.sh` (Stop) runs `validate_frontmatter.py` + `validate_body.py` in single-file mode on each recorded file. Both validators now know the `idea` schema (via the changes in this session), so violations are caught automatically.
- `/a4:validate` (user-triggered workspace-wide check) also includes `idea/` via `ISSUE_FOLDERS`.

Workspace-wide id uniqueness is still enforced by `validate_frontmatter.py` at the `/a4:validate` level (hook runs single-file mode, which skips that check per the prior session's design). An idea colliding with a usecase id would be caught at the next `/a4:validate` or compass run.

## Working-tree state at handoff time

After the pre-handoff commit:

```
1d33edbe2 feat(a4): introduce idea/ folder and /a4:idea quick-capture skill
f1aeb632e docs(handoff): snapshot a4-redesign validate-skill-and-stop-hook session state
```

Branch: `main`. This handoff's own commit sits on top.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/idea-slot/2026-04-24_1940_introduce-idea-folder-and-capture-skill.md   # this file
```

## Non-goals for the next session

- Do not re-open the "single-file accumulator vs per-item files" decision. User explicitly chose per-item files after a detailed granularity discussion; reversing would require equally detailed justification and likely a new ADR.
- Do not add `priority` / `source` / `target` / `kind` / `milestone` to the idea schema. Each exclusion is documented in the ADR with specific rationale.
- Do not merge `idea/` into `review/`. The boundary is the whole point.
- Do not mark any ADR Next Step as re-opened. All 8 steps are `[x]` at handoff time.
- Do not pick up the Experiments / PoC slot (item 4 from 2026-04-23_2119) under the `idea-slot` thread. If/when that work starts, open a new thread with its own topic.
- Do not add auto-commit to `/a4:idea`. All other a4 skills leave output in the working tree for the user to commit.

## Files intentionally NOT modified

- `plugins/a4/skills/{usecase,arch,plan,auto-*,spark-*,handoff,drift,validate,web-design-mock}/` — none interact with the idea schema or the idea folder. No change needed.
- `plugins/a4/scripts/{drift_detector,read_frontmatter,extract_section,inject_includes,validate_body}.py` — drift detector only cares about wiki↔review links; body validator's wikilink resolution already treats any `a4/<folder>/*.md` as valid. No changes.
- `plugins/a4/hooks/**` — path-based filtering picks up `a4/idea/**` automatically. No changes.
- `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` — the master ADR. Not re-opened. The idea slot is additive; no ADR decision is revised.
- `plugins/a4/spec/2026-04-24-skill-naming-convention.decide.md` — the naming-convention ADR. The new `idea` skill name is bare (interactive/orchestration default), which matches the convention without modification.
- Prior handoffs in `plugins/a4/.handoff/a4-redesign/` — 15 files preserved unchanged per DO NOT UPDATE policy.

## Files to read first next session

If the next session resumes on a new topic unrelated to ideas, this block is probably not needed — read only what the new topic requires.

If the next session needs to understand what this thread landed:

1. **`plugins/a4/spec/2026-04-24-idea-slot.decide.md`** — authoritative design summary.
2. **`plugins/a4/skills/idea/SKILL.md`** — the quick-capture skill.
3. **`plugins/a4/references/frontmatter-schema.md` `## Idea` section** — operational schema.
4. **`plugins/a4/README.md`** — user-facing summary including the idea-vs-review boundary.
5. This handoff.

## Known future-work candidates (NOT ADR items, NOT scheduled)

- **`/a4:idea-promote <id> → <target-type>` skill.** Automate the five-step manual promotion. Open this when repeated manual promotion becomes annoying.
- **Auto-promote suggestion in `/a4:usecase`.** When authoring a new usecase, suggest closing any open idea whose title sits close to the new usecase's title. Premature until usage reveals title-match frequency.
- **Idea-source field** for ideas imported from external systems (customer feedback, ticket imports). Not needed for single-user local workflow. Add when an external-source use case materializes.
- **Experiments / PoC slot** (item 4 from 2026-04-23_2119 parked list). A separate thread, not a follow-up to this one.

These are ideas, not commitments. Recording here so they are visible but not pending.
