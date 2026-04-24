---
timestamp: 2026-04-24_2005
topic: experiments-slot
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2005. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: task `kind` enum + project-root `spike/` sidecar — `experiments-slot` thread opened

This is the first handoff on the `experiments-slot` thread. It resolves item 4 (Experiments / PoC slot) from the 2026-04-23_2119 handoff's parked-list, the last unresolved item from that list. The `idea-slot` thread (closed at 2026-04-24_1940) handled item 3 and explicitly deferred item 4 — this thread picks it up.

## Why this thread exists (and why it is *not* a continuation of `idea-slot`)

The `idea-slot` 2026-04-24_1940 handoff explicitly recorded:

> Do not pick up the Experiments / PoC slot (item 4 from 2026-04-23_2119) under the `idea-slot` thread. If/when that work starts, open a new thread with its own topic.

A new thread (`experiments-slot`) rather than reopening `idea-slot` because:

- `idea-slot` was scoped narrowly to the inbox/idea problem; experiments are execution-phase artifacts (not pre-capture thoughts), per that handoff's explicit boundary.
- This session's work is narrowly scoped (one new schema field, one directory convention, no skill, no validator/INDEX/drift cross-cutting changes) and does not alter any idea-slot decision.
- Consistent with the 2026-04-24_1859 closure handoff's standing instruction: new topic → new thread.

## Pre-handoff commit

- **`f71bc9205`** — `feat(a4): add task kind enum and spike sidecar convention`. 5 files changed; 1 new ADR at `plugins/a4/spec/2026-04-24-experiments-slot.decide.md`; modifications to validator, frontmatter-schema reference, README, marketplace.json (1.2.0 → 1.3.0).

Working tree was clean of unrelated drift at the start of this session.

## Primary reads for next session

If the next session needs context on what this session landed:

1. **`plugins/a4/spec/2026-04-24-experiments-slot.decide.md`** — the authoritative ADR. Context, success criteria, decision (4 subsections), rejected alternatives (15 entries), Next Steps (all `[x]`), discussion log.
2. **`plugins/a4/references/frontmatter-schema.md` `## Task` section** — operational schema. Now includes `kind` field row, kind semantics table, and "Spike sidecar convention" subsection documenting the `spike/<id>-<slug>/` convention.
3. **`plugins/a4/README.md` `## Document Layout (a4/)` and `### Wiki vs. issues`** — user-facing summary including the project-root layout that places `spike/` as a sibling of `a4/`, plus the spike-vs-feature task bullet.
4. This handoff.

## What this session accomplished

### Design decisions (recorded here so the next session doesn't relitigate)

1. **No new a4 issue-type folder.** The boundary between "spike" and "regular task" is not sharp enough to warrant a new folder. Spike lifecycle (`pending → implementing → complete/failing`) is identical to task lifecycle; only the *nature* of the work differs. Captured by adding a frontmatter field, not a new file type.
2. **`kind` is required on task, not optional.** Three values (`feature | spike | bug`). Required-with-author-default-typing is more honest than optional-with-implicit-default — distinguishing implicit-default from spike-or-bug at read time would require body inspection in the optional case, so required field is cheap.
3. **`feature` chosen** over `general` and `default` for the regular-task kind value. Jira/agile convention; semantically peer to `spike` and `bug`.
4. **PoC code lives outside `a4/`, at project-root `spike/<task-id>-<slug>/`.** This preserves the markdown-only contract of the `a4/` workspace — a contract that all current a4 scripts (validator, INDEX-refresh, drift-detector) implicitly rely on. Workspace boundary clarified in the ADR: `a4/` is the **documentation** workspace; `spike/` is a sibling code/data sidecar; both are inside the **project repo** (which is what the user meant by "워크스페이스").
5. **Archive convention: manual `git mv` to `spike/archive/<task-id>-<slug>/`.** Self-contained under `spike/` rather than a project-root `archive/`. No automation skill — same precedent as idea-slot's deferred `/a4:idea-promote` (build the skill only when manual cost surfaces as actual pain).
6. **task `files:` field reused for spike code paths.** The existing `files:` field is documented as "source paths the task writes or modifies" — that already covers spike code. No new `poc_files:` field. After archive, user manually updates paths from `spike/<id>-<slug>/...` → `spike/archive/<id>-<slug>/...`.
7. **No INDEX/compass/drift changes.** Spikes are tasks; they appear in existing "Open issues" task aggregates. Filtering by `kind:` is a dataview query the user can write inline if needed. A dedicated "Open spikes" section would imply spikes deserve special operational attention beyond `status: pending`, which they don't.
8. **Existing-task migration intentionally not addressed.** Required `kind:` will fail validation on any existing task file without it. The `a4-redesign` ADR's standing rule (legacy data stays as-is; new model applies forward) plus this plugin's own `a4/` using legacy layout means this is intentional. If a real-workspace migration need surfaces, a one-shot `add_kind_feature.py` script can be written then.

### Files changed (5 files, one commit)

**New:**
- `plugins/a4/spec/2026-04-24-experiments-slot.decide.md` — the ADR.

**Modified:**
- `plugins/a4/scripts/validate_frontmatter.py` — task `Schema`: `required` gains `kind`; `enums` gains `kind: {feature, spike, bug}`. No other changes.
- `plugins/a4/references/frontmatter-schema.md` — Task table gains `kind` row (required, enum); existing `files` row description extended to clarify spike-vs-feature/bug semantics; new `### Kind semantics` and `### Spike sidecar convention` subsections after the table; pointer to the new ADR at section bottom.
- `plugins/a4/README.md` — Document Layout diagram now shows `<project-root>/` with `a4/` and `spike/` as siblings, including `spike/archive/<task-id>-<slug>/`; new "Spike vs. feature task" bullet under `### Wiki vs. issues` with pointer to ADR.
- `.claude-plugin/marketplace.json` — a4 `1.2.0 → 1.3.0`. **Minor** bump (additive schema field + additive directory convention; technically breaking for any pre-existing task files without `kind:`, but per the project's standing legacy policy, no migration is in scope).

### Verification run (not committed)

Sanity-checked the validator at a temporary workspace (`/tmp/a4-experiments-test`, since deleted) with five task scenarios:

| Scenario | Expected | Actual |
|----------|----------|--------|
| task without `kind` | reject (missing-required) | rejected as `missing-required` on `kind` |
| `kind: feature` | accept | accepted |
| `kind: spike` (with `files: [spike/3-spike/try1.py]`) | accept | accepted |
| `kind: bug` | accept | accepted |
| `kind: random` | reject (enum-violation) | rejected as `enum-violation` on `kind` with `not in ['bug', 'feature', 'spike']` |

Exit code 2 returned with the two expected violations on the bad scenarios; clean run on the three valid ones.

## Design questions resolved during the session

### Why not a new `a4/spike/` or `a4/experiment/` folder?

The folder-introduction calculus differs from idea-slot. Ideas needed their own folder because:
- Their lifecycle vocabulary differed (`open | promoted | discarded` vs review's `open | in-progress | resolved | dismissed`).
- They explicitly excluded `target:` (idea is independent), unlike review which centers on `target:`.

Spikes have neither asymmetry vs. tasks:
- Same lifecycle (`pending | implementing | complete | failing`).
- Same use of `files:`, `depends_on`, `justified_by`.
- Same id allocation.
- Only the *nature* of the work (throwaway code vs. production code) differs.

A field-level distinction (`kind:`) costs one frontmatter line and zero new file types. A folder-level distinction would force divergence in id allocation, INDEX rendering, validator schema, and dataview queries — overkill for a one-attribute difference.

### Why `kind` required, not optional?

Optional `kind:` with omission-implies-feature was considered. Two arguments against:

1. **Cognitive cost is the same.** A reader scanning frontmatter would always have to check whether `kind` is present to determine the task's kind; "absent = feature" is just an arbitrary mapping, not a free read.
2. **Author cost is trivial.** One extra line per task. The validator catches forgetting; tooling can default a generated task to `kind: feature`.

Required-with-author-default-typing is more honest about the schema's commitment.

### Why `feature` and not `general`/`default`?

Three options weighed:
- `feature` — Jira/agile convention; pairs naturally with `spike` and `bug`; semantically rich.
- `general` — closest direct translation of "일반"; semantically neutral and accurate but bland; doesn't carry the "this is the typical implementation work" signal.
- `default` — meta-naming; awkward as a domain term ("kind: default" reads as "I haven't decided what kind").

`feature` wins on familiarity and semantic richness.

### Why is `spike/` outside `a4/`?

The `a4/` workspace has been markdown-only since the redesign. Every script (`validate_frontmatter.py`, `index_refresh.py`, `drift_detector.py`, `validate_body.py`) globs `*.md` and assumes markdown bodies. Putting code files under `a4/` would force every script to learn skip-rules for non-markdown files, and would erode a contract that future tools also rely on.

Putting code at project-root `spike/` keeps the markdown-only contract intact and zero-cost — no script changes, no dataview surprise. The cross-reference is one-way (task `files:` field points outward) and lossless.

### Why archive instead of delete?

Spike outcomes inform later decisions. The original code is the receipt — six months later, "the test passed because of one specific JWT library version" is much easier to verify by re-reading the actual code than by reconstructing it from a writeup. Disk cost is negligible (kilobytes per spike). `git rm` is irreversible in working memory; `git mv` to archive is reversible (the user can promote a snippet back to production later).

### Why nest `archive/` under `spike/` instead of project-root `archive/`?

Self-containment. The whole "experiments" footprint is one directory. A future project-root `archive/` would have to define a multi-tenant policy (what else lives there? old configs? deprecated feature flags? prior plugin versions?) — out of scope. `spike/archive/` is the natural sub-state of the `spike/` umbrella.

### Why no `/a4:spike-new` or `/a4:spike-archive` skills?

Same logic as idea-slot's deferred `/a4:idea-promote`:

- **`spike-new`**: Spike task creation is not a 30-second hot-path the way idea capture is. A spike implies hours-to-days of work ahead — frontmatter cost is dominated by the spike itself.
- **`spike-archive`**: Manual archive is one `git mv` plus a few `files:` path edits. Skill-worthy only if the manual pattern repeats often enough to be felt.

Both are recorded in the ADR's "deliberately deferred" list; revisit when pain surfaces.

### Why no compass cleanup-nag for "complete spike with non-archived PoC files"?

Useful but premature. Compass currently diagnoses workspace state from `a4/` only. Teaching it to inspect the project-root `spike/` directory adds a cross-contract dependency (compass would have to know about a non-`a4/` convention). Add when manual archive discipline proves insufficient.

### Why no INDEX "Open spikes" section?

Spikes are tasks. They appear in existing INDEX aggregates (Open issues task row, Recent activity). Filtering by `kind:` is a dataview query the user can write inline. A dedicated section would imply spikes deserve special operational attention beyond `status: pending`, which they don't — a spike-in-progress is just an in-progress task whose code happens to be throwaway.

## What this session did NOT do

- **`/a4:spike-new` skill.** Deferred until pain surfaces.
- **`/a4:spike-archive` skill.** Deferred until pain surfaces.
- **Compass spike-cleanup surfacing.** Deferred.
- **INDEX "Open spikes" section.** Not added; spikes appear in existing task aggregates.
- **`drift_detector.py`, `validate_body.py`, `index_refresh.py` changes.** None needed — these tools operate on `a4/` only and don't care about `kind:`.
- **Hook changes.** None needed — `record-edited-a4.sh` and `validate-edited-a4.sh` are path-based and already cover task files.
- **Existing-task migration tooling.** Per the standing legacy policy, intentionally not in scope.
- **`spike/` `.gitignore` policy.** Not added — PoC history has value; users can ignore selectively if they want (e.g., large datasets).
- **Body template for spike tasks.** Free-form, like other tasks. Suggested optional shape (`## Hypothesis`, `## What I tried`, `## Result`) is not documented as a convention — let usage drive whether to formalize.
- **`a4/skills/task/`.** No `task/` skill exists in this plugin (only `auto-usecase` for autonomous use case generation). If a future `/a4:task-new` skill is added, it should default `kind: feature` and accept `--kind spike|bug` as an option.

## How the hooks + validator treat the new schema (no config needed)

The session-scoped validation hooks (`plugins/a4/hooks/`) automatically cover the new requirement:

- `record-edited-a4.sh` (PostToolUse) records any edited `.md` under `$CLAUDE_PROJECT_DIR/a4/` — covers `a4/task/**/*.md` with no change.
- `validate-edited-a4.sh` (Stop) runs `validate_frontmatter.py` in single-file mode. Now flags any new or edited task file missing `kind:` or with `kind:` outside `{feature, spike, bug}`. Existing task files in legacy workspaces are untouched until the user edits them — the hook is touch-triggered, not workspace-wide.
- `/a4:validate` (manual workspace-wide) catches every missing-kind across the whole workspace at once — the appropriate place to surface migration debt for legacy task files.

The `spike/` directory at project root is **not** validated by any a4 script. It is treated as ordinary repo content (git-tracked, no schema, no INDEX surfacing).

## Working-tree state at handoff time

After the pre-handoff commit:

```
f71bc9205 feat(a4): add task kind enum and spike sidecar convention
a7e43efd2 docs(handoff): snapshot idea-slot session state
1d33edbe2 feat(a4): introduce idea/ folder and /a4:idea quick-capture skill
```

Branch: `main`. This handoff's own commit sits on top.

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/experiments-slot/2026-04-24_2005_task-kind-and-spike-sidecar.md   # this file
```

## Non-goals for the next session

- Do not re-open the "task with kind enum" vs "new folder" decision. The boundary analysis is documented in the ADR's Rejected Alternatives; reversing requires equally detailed justification and a new ADR.
- Do not change `kind` from required to optional. The reasoning for required is documented; making it optional reintroduces the absent-implies-feature ambiguity that the required form was designed to eliminate.
- Do not add other `kind` values (`story`, `chore`, `refactor`, etc.) without a real downstream consumer. The enum can be widened later without breaking existing files; widening preemptively invites bikeshedding.
- Do not move PoC code under `a4/`. The markdown-only contract of `a4/` is load-bearing for several scripts and has been deliberately preserved.
- Do not auto-archive on `status: complete`. The user wants to retain manual control over the `git mv`; auto-archive is destructive in working memory.
- Do not add any of the deferred items (`/a4:spike-new`, `/a4:spike-archive`, compass cleanup-nag, INDEX section) without first observing the manual cost the deferral was designed to test.
- Do not pick up further parked items as continuations of this thread. The 2026-04-23_2119 parked list is now fully resolved (item 3 in idea-slot, item 4 here, item 5 implicitly via the `decision/` folder). If a new parked-item-style gap surfaces later, open a new thread.

## Files intentionally NOT modified

- `plugins/a4/skills/{usecase,arch,plan,auto-bootstrap,auto-usecase,compass,spark-brainstorm,spark-decide,handoff,drift,validate,idea,index,web-design-mock}/` — none interact with the task `kind` field. No change needed. (No `task/` skill exists.)
- `plugins/a4/scripts/{allocate_id,drift_detector,extract_section,index_refresh,inject_includes,read_frontmatter,validate_body}.py` — id allocation is folder-based and `kind`-agnostic; drift detector cares about wiki↔review only; INDEX-refresh aggregates by folder/status, not `kind`; body validator's wikilink resolution is unchanged. No changes.
- `plugins/a4/hooks/**` — path-based filtering already covers task files; no `kind`-aware logic needed at the hook layer.
- `plugins/a4/references/{obsidian-conventions,obsidian-dataview}.md` — no changes. `kind` is queryable via existing dataview patterns; no new INDEX block was added (deliberately).
- `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` — the master ADR. Not re-opened. The kind addition is additive at the schema level; the experiments-slot ADR is a follow-up rather than a revision.
- `plugins/a4/spec/2026-04-24-skill-naming-convention.decide.md` — no skills added or renamed.
- `plugins/a4/spec/2026-04-24-idea-slot.decide.md` — closed thread artifact; not edited.
- Prior handoffs in `plugins/a4/.handoff/{a4-redesign,idea-slot}/` — preserved unchanged per DO NOT UPDATE policy.

## Files to read first next session

If the next session resumes on a new topic unrelated to experiments/spikes, this block is probably not needed — read only what the new topic requires.

If the next session needs to understand what this thread landed:

1. **`plugins/a4/spec/2026-04-24-experiments-slot.decide.md`** — authoritative ADR.
2. **`plugins/a4/references/frontmatter-schema.md` `## Task` section + `### Kind semantics` + `### Spike sidecar convention`** — operational schema and convention.
3. **`plugins/a4/README.md` `## Document Layout (a4/)` and `### Wiki vs. issues`** — user-facing summary.
4. **`plugins/a4/scripts/validate_frontmatter.py` task Schema entry (~lines 74–84)** — the actual enforcement.
5. This handoff.

## Known future-work candidates (NOT ADR items, NOT scheduled)

- **`/a4:spike-archive <task-id>` skill.** Automate `git mv spike/<task-id>-<slug> spike/archive/` plus `files:` path rewrite. Open this when manual archive feels repetitive.
- **`/a4:spike-new <title>` skill.** Defaults `kind: spike`, allocates id, scaffolds the spike directory at `spike/<id>-<slug>/`. Open this only if a "spike" hot-path emerges (currently doesn't seem to).
- **Compass cleanup-nag for "complete spike with non-archived PoC".** Cross-contract diagnostic that would have compass inspect `spike/` to flag stale active spike directories. Deferred until manual cleanup proves insufficient.
- **`kind` enum widening.** Adding `story`, `chore`, `refactor`, etc. Only if a downstream consumer (skill, dataview query, INDEX section) actually needs the distinction.
- **One-shot `add_kind_feature.py` migration script.** For backfilling `kind: feature` into legacy task files when a real workspace migration is needed. Currently no such workspace exists.

These are ideas, not commitments. Recording here so they are visible but not pending.
