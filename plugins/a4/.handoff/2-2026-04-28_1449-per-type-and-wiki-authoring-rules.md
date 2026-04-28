---
sequence: 2
timestamp: 2026-04-28_1449
timezone: KST +0900
topic: a4-xml-body-format
previous: 1-2026-04-28_1411-a4-spec-authoring-rule.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-28_1449. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Complete the path-scoped authoring-rule suite under
`plugins/a4/rules/`. The prior handoff
(`1-2026-04-28_1411-a4-spec-authoring-rule.md`) shipped the first
substantive rule (`a4-spec-authoring.md`) and listed four follow-ups
in priority order:

1. `a4-task-authoring.md`
2. `a4-usecase-authoring.md`
3. `a4-review-authoring.md`
4. Per-wiki-page authoring rules (×7)

This session lands all four. The `rules/` directory is now the
finished surface for hand-edited per-artifact authoring guidance:
12 files (1 generator-owned section enum + 11 hand-edited authoring
rules: 4 issue-family + 7 wiki-page).

## Current State

- Branch: `main`. Pre-handoff commit `645176ee0` (this session) on
  top of `597104de9 docs(handoff): unify handoff workflow`. The 10
  newly added rule files plus the marketplace bump and CLAUDE.md
  pattern restructure all live in that single commit.
- Working tree carries one user-driven change unrelated to this
  session's work product: a deletion of
  `plugins/a4/.handoff/1-2026-04-28_1411-a4-spec-authoring-rule.md`
  (the prior handoff). The file is still tracked at HEAD; the
  deletion is unstaged. **Left untouched** — it is consistent with
  the recent user pattern of removing stale snapshots
  (`48a58aa2e docs(handoff): remove stale session snapshots`) but
  was not part of this session's authoring work and should be
  committed separately if the user intends to retire the old
  snapshot.
- Marketplace version: `3.2.0 → 3.6.0` (single minor bump per rule
  landed; finalized as one delta in `645176ee0`). Bumps from
  individual sessions if you walk the conversation:
  - `3.3.0` after `a4-task-authoring.md`
  - `3.4.0` after `a4-usecase-authoring.md`
  - `3.5.0` after `a4-review-authoring.md`
  - `3.6.0` after the seven wiki-page rules (single batch)
  Only the final value is recorded in the commit.

## Changes Made

### Files created (10)

#### Issue-family rules (folder-scoped, `paths: ["a4/<type>/**/*.md"]`)

- **`plugins/a4/rules/a4-task-authoring.md`**. Sections cover the
  three-mode authoring path (`/a4:task` single, `/a4:roadmap` batch
  at `pending`, `/a4:task discard`); required `kind:` field
  (`feature | spike | bug`); orthogonal `implements:` / `spec:` and
  the `kind: feature` no-anchor smell check (content-aware upward
  propagation from `references/spec-triggers.md`); 6-state lifecycle
  (`open | pending | progress | complete | failing | discarded`)
  with writer-only `progress`/`failing`, allowed initial states
  `open | pending | complete`, no `pending → open` reverse, UC
  cascade rules (`discarded` cascade, `revising` task reset);
  `complete` initial-status preflight (path existence check + the
  one sanctioned hand-write to `<log>`); body shape (4 required +
  `<interface-contracts>` / `<change-logs>` / `<log>` /
  `<why-discarded>` optional); spike sidecar at
  `spike/<id>-<slug>/`; "Don't" list of 11 items.

- **`plugins/a4/rules/a4-usecase-authoring.md`**. Sections cover the
  authoring path (`/a4:usecase` Socratic interview, `/a4:auto-usecase`
  forward draft); abstraction discipline (UCs stay user-level —
  internal mechanics belong to architecture/specs); frontmatter
  contract with `actors:` slug references and the auto-maintained
  `implemented_by:`; 8-state lifecycle (`draft | ready | implementing
  | revising | shipped | superseded | discarded | blocked`) with the
  `draft` initial-only rule, the `implementing → draft` and post-
  `shipped` invariants, the `ready → implementing` `implemented_by:`-
  non-empty gate, the `implementing → shipped` all-tasks-`complete`
  gate; body shape (4 required `<goal>`/`<situation>`/`<flow>`/
  `<expected-outcome>` + `<validation>`/`<error-handling>`/
  `<dependencies>`/`<change-logs>`/`<log>` optional); the in-situ
  wiki-nudge permission table (`context.md`/`actors.md`/`nfr.md` are
  in-situ for `usecase`; `domain.md`/`architecture.md` are
  defer-to-review-item); UC splitting protocol (no supersede
  mechanism — that requires a shipped predecessor); "Don't" list of
  10 items.

- **`plugins/a4/rules/a4-review-authoring.md`**. The unique rule of
  the four — review items have **no dedicated authoring skill**.
  Sections cover the four emission paths (reviewer agents, drift
  detector with reserved `drift:` / `drift-cause:` labels, defer
  paths in single-edit skills, task-implementer architectural-choice
  exit B5); frontmatter contract with `kind: finding | gap |
  question`, `target:` (omit for cross-cutting, never invent
  placeholders), `source:` convention, `wiki_impact:` as bare
  basenames; UC `discarded` cascade; 4-state lifecycle (`open →
  in-progress → resolved | discarded`) with `open` initial-only,
  drift dedup tombstone semantics on `discarded` (resolved does not
  block re-emission); close guard (warning + override) requiring a
  `<change-logs>` bullet on each `wiki_impact` page when resolving;
  body shape (only `<description>` required — bodies are hand-off
  notes, not essays); "Don't" list of 10 items.

#### Wiki-page rules (single-file-scoped, `paths: ["a4/<basename>.md"]`)

Same shape across all seven, differing in primary author and the
authorship-allowance specifics from `references/wiki-authorship.md`:

- **`plugins/a4/rules/a4-architecture-authoring.md`**. `/a4:arch`
  only — most-depended-on wiki, no in-situ edits from other skills.
  Required body: `<overview>`, `<components>`, `<technology-stack>`,
  `<test-strategy>`. Optional: `<component-diagram>`,
  `<external-dependencies>`, `<change-logs>`. **Don'ts** include "no
  Launch & Verify content" (lives in bootstrap), "no roadmap /
  milestone schedule" (lives in roadmap), "no rejected-options list
  in `<technology-stack>`" (lives in specs), "no silent component
  rename" (cascade impact via `<interface-contracts>` links).

- **`plugins/a4/rules/a4-context-authoring.md`**.
  `/a4:usecase` only. Required: `<original-idea>` (verbatim user
  input — never paraphrase), `<problem-framing>`. Optional:
  `<screens>` (UI screen-navigation grouping), `<change-logs>`.

- **`plugins/a4/rules/a4-domain-authoring.md`**. `/a4:domain` primary
  + `/a4:arch` limited in-situ (the b3 split: add concept, 1:1
  rename, definition wording wording allowed; structural changes —
  splits/merges/relationships/state — go through review item).
  Required: `<concepts>`. Optional: `<relationships>`,
  `<state-transitions>`, `<change-logs>`.

- **`plugins/a4/rules/a4-actors-authoring.md`**. `/a4:usecase`
  primary + `/a4:arch` limited (system-actor add only; never modify
  a `person`-type actor). Required: `<roster>` (slug + type +
  role/privileges + description columns). Optional: `<change-logs>`.
  Slug discipline: renames cascade to UC frontmatter and warrant a
  review item.

- **`plugins/a4/rules/a4-nfr-authoring.md`**. `/a4:usecase` primary
  + `/a4:arch` footnote-only (annotation pointing to the
  architectural decision that satisfies an NFR; no new NFRs, no
  edits to existing NFR text). Required: `<requirements>` (table
  with measurable criteria — no aspirational phrasing). Optional:
  `<change-logs>`. File is optional; only created when at least one
  NFR exists.

- **`plugins/a4/rules/a4-roadmap-authoring.md`**. `/a4:roadmap` only.
  Required: `<plan>` (single section, organized internally with H3+
  headings: milestone narrative, dependency graph, Shared Integration
  Points, **a one-line Launch & Verify pointer to bootstrap.md**).
  Optional: `<change-logs>`. Stop-on-upstream-issue policy is loud:
  no partial roadmap when arch / UC review items are open.

- **`plugins/a4/rules/a4-bootstrap-authoring.md`**.
  `/a4:auto-bootstrap` is the **only** writer; no other skill edits
  in-situ (hand-edits defeat the verification contract). Required:
  `<environment>`, `<launch>`, `<verify>`. Optional:
  `<change-logs>`. The rule emphasizes that `<verify>` is the single
  source of truth — read directly by `/a4:run`, `task-implementer`,
  `test-runner` — never duplicated into `architecture.md`'s
  `<test-strategy>` (which records the *strategy*, not the
  executable contract) or `roadmap.md` (which only links to
  bootstrap).

### Files modified

- **`plugins/a4/CLAUDE.md`** — restructured the
  `rules/a4-<type>-authoring.md` bullet under "Per-section reads and
  path-scoped rules" to document the two flavors side by side
  (issue-family with folder glob, wiki-page with single-file scope)
  with explicit instance lists for each.
- **`.claude-plugin/marketplace.json`** — bumped a4 from `3.2.0` to
  `3.6.0`. (See Current State for the per-rule breakdown.)

### Files explicitly NOT modified

- `commands/install-rules.md` and `commands/uninstall-rules.md`
  iterate `${CLAUDE_PLUGIN_ROOT}/rules/*.md`, so they pick up all
  ten new rules automatically. No edits required.
- `.githooks/pre-commit` — none of the new rules are
  generator-owned, so no drift block was added.
- `plugins/a4/scripts/generate_section_enum.py` and
  `plugins/a4/scripts/extract_section.py` — unchanged.
- All seven `body_schemas/*.xsd` — unchanged. The wiki-page rules
  consolidate but do not extend the schemas.

## Key Files

- `plugins/a4/rules/` — now contains 12 files. The directory is the
  finished surface for the path-scoped-rule effort started in commit
  `e46511acf` (infrastructure) and continued through `a3593d91f`
  (first rule), `645176ee0` (this commit, ten rules). Future
  additions to this directory follow the two flavors documented in
  `plugins/a4/CLAUDE.md`.
- `plugins/a4/CLAUDE.md` — the working notes for plugin developers;
  now documents both rule flavors (issue-family folder-scoped,
  wiki-page single-file-scoped) and lists every current instance.
- `plugins/a4/references/wiki-authorship.md` — the authoritative
  source for wiki-page authorship boundaries that the seven
  wiki-page rules mirror. Every cross-stage edit allowance the
  wiki-page rules name (`/a4:arch` system-actor add, `/a4:arch` NFR
  footnote, `/a4:arch` domain b3) is a verbatim restatement of this
  reference.
- `plugins/a4/references/frontmatter-schema.md` — the per-type field
  schemas the rules consolidate. Lifecycle tables, transition
  graphs, validator behavior all originate here.
- `plugins/a4/scripts/body_schemas/<type>.xsd` — the source of truth
  for each rule's "Required vs Optional sections" content. The
  rules restate; the XSDs validate.

## Decisions and Rationale

- **Single pre-handoff commit instead of one-per-rule.** The four
  rules (and their CLAUDE.md / marketplace bumps) were authored
  iteratively in one session; bundling them into one commit produces
  a clean diff and a single coherent message ("per-type and per-wiki
  authoring rules"). Splitting into 4 commits would invent fake
  granularity — the ten rules are conceptually one batch (the
  finished suite). Trade-off: rolling back a single rule requires
  manual file revert rather than `git revert`. Acceptable given
  these are additive markdown files with no runtime effect on the
  plugin core.
- **Wiki-page rules use single-file `paths:` not folder glob.** Each
  wiki page is a singleton in `a4/`, so `paths: ["a4/architecture.md"]`
  is the correct scope. Using `paths: ["a4/*.md"]` would auto-load
  every wiki rule whenever any wiki was opened, which is wrong (each
  rule is page-specific). The 7-file structure is the right
  fidelity.
- **`a4-review-authoring.md` is the odd one out — no authoring
  skill.** Review items are emitted by reviewers / drift / defer /
  task-implementer rather than authored interactively. The rule is
  framed as "how the schema looks when something else writes you"
  rather than "how to write one yourself." This is a meaningful
  shape change vs the other three issue-family rules but is a
  faithful reflection of the workspace model.
- **Restate, don't replace, even more aggressively for wiki-page
  rules.** Wiki pages have minimal frontmatter (`type` + `updated`)
  and a small set of body sections, so the wiki-page rules lean
  heavily on the authorship table from `wiki-authorship.md`. The
  rules are short by issue-family standards but consolidate the
  *what to do / not do at this page* into one auto-loadable file.
- **`/a4:arch` cross-edit allowances are restated in three of the
  seven wiki rules** (`actors`, `domain`, `nfr`). Without
  restatement, a fresh LLM reading `a4/actors.md` would not know
  that `/a4:arch` may legitimately add a system-actor row. The
  authorship table in `wiki-authorship.md` is the authority; the
  rule duplicates the relevant slice for auto-load convenience.
- **Bootstrap rule has the strictest "single writer" framing.** The
  `<verify>` section is read by three downstream consumers
  (`/a4:run`, `task-implementer`, `test-runner`) directly — any
  hand-edit that bypasses verification produces a stale executable
  contract. The rule's "Don't" list reflects this with a "no skill
  other than `/a4:auto-bootstrap` writes here" rule.
- **Roadmap rule's strongest "Don't" is "no Launch & Verify
  content here."** Bootstrap owns Launch & Verify outright; roadmap
  carries only a one-line link pointer. The rule emphasizes this
  because the natural temptation is to inline build/test commands
  alongside milestone narrative.
- **Marketplace version `3.2.0 → 3.6.0` (single net delta).** New
  rule files are additive features without breaking changes. Each
  rule conceptually warrants a minor bump; in commit form the four
  bumps are folded into one.
- **`topic: a4-xml-body-format` reused.** This session is the
  natural continuation of the path-scoped-rule thread — the prior
  handoff explicitly named all four follow-ups. New topic
  considered and rejected for the same reason as the prior session.
- **Working-tree deletion of the prior handoff was not swept into
  the pre-handoff commit.** Per `/handoff` guidance ("do not sweep
  in unrelated user changes just because they are pending"), the
  deletion is left as the user's decision to commit separately.
  See Known Issues and Risks.

## Important Dialog

- User asked in 한국어 to proceed with each follow-up in turn,
  using one-word confirmations (`진행`, `y`, `진행`). Auto mode
  active throughout — no interactive scope clarifications, no
  stop-and-ask checkpoints.
- After completing the three issue-family rules, user asked
  "4번은 뭐지?" (what is #4) — confirming the wiki-page rules are
  worth doing despite the prior handoff calling them "lower
  priority." User confirmed `진행` and the seven wiki-page rules
  followed.
- User did not specify `additional requirements` for the
  handoff, so this file follows the defaults.

## Validation

- `uv run plugins/a4/scripts/generate_section_enum.py --check` →
  `OK — section enum in a4-section-enum.md matches body_schemas/.`
  exit `0`. Section-enum drift check passes (the new rules do not
  affect this generator).
- `uv run plugins/a4/scripts/validate_frontmatter.py plugins/a4/rules/`
  → `OK — 12 file(s) scanned, no violations.` exit `0`. The
  validator scans frontmatter shape; `name` / `description` /
  `paths` keys are tolerated (validator is lenient on unknown fields
  per the schema's "Unknown fields" rule).
- Pre-handoff commit verified: `git rev-parse HEAD` →
  `645176ee0c51e02e2e35cd815bbf0637ddf1d63c`.
- `git status --short` after the pre-handoff commit shows only the
  pre-existing user-driven deletion of
  `plugins/a4/.handoff/1-2026-04-28_1411-a4-spec-authoring-rule.md`
  (left untouched — see Known Issues).
- **Skipped:** `validate_body.py`, `transition_status.py`. The new
  rules are static markdown under `plugins/a4/rules/`; none of the
  workspace-side body validators apply.
- **Skipped:** Live `/a4:install-rules` rerun against a throwaway
  project. Justification: the install command iterates
  `${CLAUDE_PLUGIN_ROOT}/rules/*.md` mechanically — the same loop
  that handles `a4-section-enum.md` and `a4-spec-authoring.md`
  handles the ten new rules identically. The infrastructure was
  end-to-end verified in commit `e46511acf` (per the prior handoff
  thread).

## Known Issues and Risks

- **Pre-existing handoff-file deletion is unstaged.** The user
  deleted `plugins/a4/.handoff/1-2026-04-28_1411-a4-spec-authoring-rule.md`
  from the working tree before / during this session. The file
  remains tracked at HEAD (committed in `716628f70`). This deletion
  was not part of this session's scope and was deliberately not
  staged into the pre-handoff commit. The user can:
  - Commit the deletion separately (`git rm` + commit) — consistent
    with the recent pattern of `48a58aa2e docs(handoff): remove
    stale session snapshots`.
  - Restore the file from HEAD if the deletion was unintentional
    (`git checkout HEAD -- plugins/a4/.handoff/1-...`).
- **Restated content drifts independently from references.** Each
  of the ten new rules duplicates fragments of `frontmatter-schema.md`,
  `wiki-authorship.md`, and the per-type XSDs / SKILL.md flow. When
  any of those references change, the affected rules must be
  revised by hand. There is no drift check. Mitigation: every rule
  has a Cross-references footer that names the upstream sources, so
  a quick rule-vs-reference scan after a substantive reference
  change is feasible.
- **`paths:` frontmatter is not yet validated.** No script confirms
  that `paths:` is a list of valid glob strings. If a future rule
  has a typo'd path glob, it will silently fail to auto-load. The
  `rules/` directory is small enough that visual review catches
  mistakes; not addressed.
- **Wiki-rule authorship-allowance drift risk.** The `/a4:arch`
  system-actor / domain b3 / NFR-footnote allowances are restated
  in three of the seven wiki-page rules. If `wiki-authorship.md`
  loosens or tightens these allowances, the three rules and any
  affected `arch` SKILL.md sections must be updated together. Same
  mitigation as above (cross-reference footer).
- **No multi-file rule install verification.** The marketplace
  version bumped but no end-to-end test confirms that rolling
  install / uninstall iterates all ten new files cleanly in a fresh
  project. Risk is low (the install loop is tested) but not zero.

## Next Steps

In priority order, carrying over from the prior handoff and
incorporating the now-finished suite:

1. **Optional: `--multi` mode for `extract_section.py`.** The only
   suggested follow-up from the prior handoff that did not land
   this session. Speculative — only do if real usage shows churn
   from extracting the same multiple sections per file in a
   tight loop.

2. **Validation script for `paths:` frontmatter on rule files.**
   A small linter that confirms each `paths:` entry parses as a
   glob and does not collide with another rule's scope. Lifts the
   risk surfaced under Known Issues.

3. **`a4-idea-authoring.md` and `a4-spark-authoring.md`?** The
   `idea/` and `spark/` families were not covered by either prior
   handoff's follow-up list. Idea is pre-pipeline quick-capture
   (`type: idea`, body largely free with optional `<notes>` /
   `<why-this-matters>`); brainstorm carries `type: brainstorm`
   with required `<ideas>`. Both have skills (`/a4:idea`,
   `/a4:spark-brainstorm`). The argument **against** rules: the
   bodies are loosely structured and the workflows are short — the
   value of a path-scoped rule is lower. The argument **for**: for
   completeness and consistency with the rest of the family. Defer
   until a concrete pain point surfaces.

4. **`research/` family rule (`a4-research-authoring.md`).** The
   `research/<slug>.md` files live at project-root, not under
   `a4/`, and are not validated by `validate_frontmatter.py`. The
   `register_research_citation.py` registrar owns most schema
   correctness here. A rule could still be useful for the
   citation-format / cited_by-rules consolidation. Defer; lower
   priority than #2.

5. **Re-scan rules after the next substantive change to**
   `references/frontmatter-schema.md`, `wiki-authorship.md`, or
   `body-conventions.md`. The first such change is the natural
   trigger to read every rule and reconcile.

## Open Questions

- **Should the rules carry their own version field for staleness
  checks?** Each rule consolidates one or more references; if a
  reference advances, the rule's restated content lags. A
  `rule_version:` + matching reference checksum could surface
  drift. Not addressed; pursue only if drift becomes a measured
  problem.
- **Should `a4-review-authoring.md` keep its current shape or be
  re-framed as a "reviewer-emitter conventions" doc?** The rule
  reads less like an authoring guide and more like a schema
  reference because there is no authoring skill. The current
  shape is internally consistent with the others (path-scoped,
  same section structure) but could be revisited if the read
  experience proves awkward.
- **Wiki-page rules vs reference doc — long-term, which is
  primary?** Today `wiki-authorship.md` is the authority and the
  seven wiki-page rules restate slices of it. If wiki-page rules
  prove more useful in practice (auto-load, page-specific scope),
  they may eventually become the primary location with the
  reference doc consolidating to a cross-cutting summary. Carry-
  over; revisit once usage data exists.
- **Do path-scoped rules conflict in
  `<project-root>/.claude/rules/` if two plugins ship rules with
  the same basename?** Carried over from the prior handoffs (open
  question that has appeared twice). Not relevant while a4 is the
  only namespace using `a4-` prefixes, but worth formalizing
  before the marketplace grows.

## Useful Commands and Outputs

```bash
# Verify the new rule files all parse and live in the expected shape
ls plugins/a4/rules/
# Expect 12 entries: 1 a4-section-enum.md + 11 a4-*-authoring.md

# Section-enum drift check still clean (unaffected by new rules)
uv run plugins/a4/scripts/generate_section_enum.py --check

# Frontmatter validator on the rules directory
uv run plugins/a4/scripts/validate_frontmatter.py plugins/a4/rules/

# Pre-handoff commit
git show --stat 645176ee0
# 12 files changed, 2399 insertions(+), 9 deletions(-)

# Confirm prior handoff is still tracked at HEAD even though deleted in worktree
git cat-file -p HEAD:plugins/a4/.handoff/1-2026-04-28_1411-a4-spec-authoring-rule.md | head -3
```

Sample output from the section-enum check:

```
OK — section enum in a4-section-enum.md matches body_schemas/.
```

Sample output from the rules-frontmatter scan:

```
OK — 12 file(s) scanned, no violations.
```
