---
sequence: 3
timestamp: 2026-04-29_2250
timezone: KST +0900
topic: a4-xml-body-format
previous: 2-2026-04-28_1449-per-type-and-wiki-authoring-rules.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-29_2250. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Two closely-related goals advanced this session:

1. **Ship the body-section format switch.** The previous handoff (`2-…-per-type-and-wiki-authoring-rules.md`) had the a4 plugin emitting body sections as XML-style `<tag>…</tag>` blocks. The user requested converting all skill outputs to plain markdown — using H2 (`## Title Case`) headings instead. XSDs become pure human reference; no runtime body validator.
2. **Identify the next refactor target.** After the heading-form shipped, the user asked whether `references/frontmatter-schema.md` had grown over-loaded and whether content properly belonging to per-type authoring guides was mixed in. They also asked for the list of files referencing `frontmatter-schema.md`. The user agreed the proposed split should proceed as a **separate** session, not in this one.

## Current State

- Branch: `main`. Worktree clean except for an untracked, session-unrelated `.claude/scheduled_tasks.lock`.
- Local `main` is **32 commits ahead of `origin/main`** as of this handoff. Push has not been requested by the user.
- The body-section conversion landed in commit **`b9225d62c`** — `feat(a4)!: switch body sections from <tag> blocks to ## Title Case headings`. 97 files changed (+1050 / −1201), `scripts/validate_body.py` deleted.
- `.claude-plugin/marketplace.json` bumped a4 plugin to **`7.0.0`** (breaking change) in that same commit.
- The frontmatter-schema decomposition is **not started** — only diagnosed. The user explicitly chose to defer it to a separate session.

## Changes Made

All substantive changes are in commit `b9225d62c`. Inspect via `git show b9225d62c -- '<path>'` for exact contents. High-level summary:

1. **Body convention rewrite.** `references/body-conventions.md` rewritten as the central rule for column-0 H2 Title Case headings, kebab→Title Case mapping table, link form (markdown `[text](relative/path.md)`), `## Change Logs` audit trail, `## Log` (now hand-maintained, optional), Wiki Update Protocol.
2. **`transition_status.py` body-write removal.** Stripped `_LOG_BLOCK_RE`, `_format_log_block`, `append_log_entry`, `_format_log_line`, the `import re`, and the body-modification call in `_apply_status_change`. The writer now updates only `status:` and `updated:`. `## Log` is documentation-only, hand-maintained when authors want a body audit trail.
3. **`validate_body.py` deleted.** Body shape is documentation-only; XSDs are no longer consumed by any runtime validator.
4. **`extract_section.py` rewritten.** Self-contained H2 scanner with `_slugify` helper that accepts both `Change Logs` and `change-logs` query forms. No longer imports from the deleted `validate_body`.
5. **`generate_section_enum.py` updated.** Added `_heading_form(slug)` converter; `_format_bullet` emits Title Case heading form so the rule-file enum reads `R{## Context, ## Specification} O{## Change Logs, …}`.
6. **All 14 XSDs (`scripts/body_schemas/*.xsd`) re-headered** with a uniform comment block clarifying they are pure human reference, element names use kebab-case (XML grammar artifact), body uses Title Case H2 headings.
7. **15 `references/*-authoring.md` files converted.** Every `<tag>…</tag>` body-section block replaced with `## Title Case`. "Writer-owned `<log>`" framing replaced with "optional, hand-maintained `## Log`".
8. **43 skills/SKILL.md and skill references converted.** Same conversion across `skills/{arch,auto-bootstrap,auto-usecase,domain,drift,idea,roadmap,run,spark-brainstorm,spec,task,usecase}/`.
9. **11 agent definitions converted** under `agents/`.
10. **3 docs files converted** (`docs/iterate-mechanics.md`, `docs/pipeline-shapes.md`, `docs/wiki-authorship.md`).
11. **`rules/a4-section-enum.md` rewritten** to lead with `body-conventions.md` reference and emit per-type bullets in heading form.
12. **`marketplace.json`**: a4 version `6.0.0` → `7.0.0`.

For exact diffs:

```bash
git show b9225d62c --stat
git show b9225d62c -- plugins/a4/scripts/transition_status.py
git show b9225d62c -- plugins/a4/references/body-conventions.md
git show b9225d62c -- plugins/a4/references/frontmatter-schema.md
```

## Key Files

- **`plugins/a4/references/frontmatter-schema.md`** (524 lines) — **next session's main subject.** This is the file flagged as over-loaded. Currently mixes frontmatter contract + lifecycle prose + body-section table + artifact-directory policy + close-guard duplication.
- **`plugins/a4/references/body-conventions.md`** (180 lines) — receiving doc for body-side rules; already authoritative for heading form. Likely target for the `## Body sections per type` table currently in frontmatter-schema.
- **`plugins/a4/references/<type>-authoring.md`** (14 files, 58–157 lines each) — per-type authoring contracts. Receivers for lifecycle prose, kind semantics, artifact policies that should not live in frontmatter-schema.
- **`plugins/a4/scripts/transition_status.py`** — single status writer. Touched this session to remove `## Log` body writes; do not regress this contract.
- **`plugins/a4/scripts/extract_section.py`**, **`scripts/generate_section_enum.py`** — both rely on the kebab→Title Case mapping. If you change the mapping in `body-conventions.md`, sync these.
- **`plugins/a4/CLAUDE.md`** — declares directory-role split (`references/` = substantive data, `rules/` = pointer-only, `docs/` = workflow). The frontmatter-schema decomposition must respect this split: substance moves to `references/<type>-authoring.md`, not to `rules/` or `docs/`.

## Related Links

- **Project-root `CLAUDE.md`** (`/Users/myungo/GitHub/studykit-plugins/CLAUDE.md`) — declares: plugin versions live in `marketplace.json` only; `frontmatter-schema.md` is a hard prerequisite read before editing a4 frontmatter or validators. Cited from this handoff because the next session must respect both rules.
- **`plugins/a4/CLAUDE.md`** — directory layout + "required reading before editing" map. Read first before touching anything in `plugins/a4/`.
- **Prior handoff** `.handoff/2-2026-04-28_1449-per-type-and-wiki-authoring-rules.md` — captured the state immediately before the XML→markdown switch.
- **Prior handoff** `.handoff/1-2026-04-28_1411-a4-spec-authoring-rule.md` — earlier still; for full thread context.

## Decisions and Rationale

1. **H2 with Title Case + spaces** (`## Change Logs`, not `## Change-Logs`). User chose option (b) explicitly. Kebab-case lives only in XSD element names because XML grammar forbids spaces.
2. **XSDs as pure human reference, no runtime consumer.** `validate_body.py` deleted; `body_schemas/<type>.xsd` retained for human readers and for `generate_section_enum.py` to project the enum into the rule file.
3. **`transition_status.py` no longer writes `## Log`.** Status flips touch only `status:` and `updated:`. Authors who want a body audit trail append bullets manually. Rationale: keep the writer minimal, avoid coupling status mechanics to body structure.
4. **Frontmatter-schema decomposition deferred.** User chose to handle the split in a dedicated session rather than chaining it onto the just-completed conversion. This handoff captures the diagnosis so the next session can pick it up cold.
5. **No push.** `main` is 32 commits ahead of `origin/main`. The user has not asked to push and the persona forbids nudging. Leave the branch local until they request.

## Important Dialog

- User on heading form: *"1. A . Heading 첫글자는 대문자로. H1 써도 될꺼같은데 이건 고민중 / 2. 그냥 사람 참고용. xsd만 보면 어떤 heading 있다 정도만 사용할 예정. validate_body.py로 검증하지 않음. / 3. heading 으로 만들기. transition_status.py는 heading 블록을 갱신하지 않음."* — locked Title Case + XSD-as-reference + writer doesn't touch body.
- User on log block: *"transition_status.py의 log-block 작성 로직에서 제거."* — explicit instruction; the writer's body-write call is gone.
- User on the new question: *"frontmatter-schema.md 너무 많은 내용을 포괄하고 있는건 아닌지. 각 문서 authoring에만 있으면 되는 내용이 같이 있는건지 검토. frontmatter-schema.md 를 참조하는 파일목록 나열"* — triggered the diagnosis below.
- User on next-step framing: *"별도 작업으로 진행"* — split is approved as a separate session, not in this one.
- Persona constraints carried throughout the session: respond in Korean (존댓말), files in English, no `git push` nudging, conversation-first (don't switch to planning unprompted), one topic at a time.

## Validation

- **Manual verification done in this session:**
  - `transition_status.py --help` was confirmed to load after the body-write removal (run during the conversion session).
  - `git status` after the b9225d62c commit was clean (worktree empty modulo unrelated lock file).
  - 97 files changed / +1050 / −1201 / `validate_body.py` deleted (visible in `git show b9225d62c --stat`).
- **Not run this session:**
  - `uv run plugins/a4/scripts/validate.py` — full workspace validate. Recommended next session before any new edits.
  - `uv run plugins/a4/scripts/generate_section_enum.py --check` — confirms `rules/a4-section-enum.md` is in sync with `body_schemas/`. Run before splitting frontmatter-schema, since the split may touch the section table.
  - No automated tests exist for the conversion; spot-check by opening a few converted authoring docs and confirming H2 headings render correctly.

## Known Issues and Risks

1. **`main` is 32 commits ahead of `origin/main`.** Significant divergence. If the user pushes, force-with-lease may not be needed (no upstream rewrites), but a plain push will be a large fan-out. No automatic push.
2. **Untracked `.claude/scheduled_tasks.lock`** in the worktree. Session-unrelated; left alone. Not in this handoff's commit.
3. **Frontmatter-schema decomposition is unstarted.** The diagnosis below is the only artifact; cross-references in 29 files will need updating once the split happens.
4. **Possible content duplication between `frontmatter-schema.md §Review` close-guard and `review-authoring.md §Close guard`.** The next session should diff them and pick a single home (review-authoring, per the directory-role rule in `plugins/a4/CLAUDE.md`).
5. **`rules/a4-section-enum.md` projection** — generated from `body_schemas/<type>.xsd` via `generate_section_enum.py`. If the section table moves from `frontmatter-schema.md` into `body-conventions.md`, the generator does not need to change, but verify with `--check`.

## Next Steps

In priority order for the next session:

1. **Re-read context.** Open `plugins/a4/CLAUDE.md`, `plugins/a4/references/frontmatter-schema.md`, `plugins/a4/references/body-conventions.md`. Then skim each per-type authoring file to confirm what is already there before moving content in.
2. **Decide split granularity** with the user: (a) one type at a time (incremental), (b) one bulk pass, or (c) further audit first. The user previously deferred this choice to "the next session start."
3. **Execute the planned moves** (target ~280–320 lines for `frontmatter-schema.md`, down from 524):
   - UC lifecycle prose (notable rules, transition-meaning table) → `usecase-authoring.md`.
   - Task `kind` semantics + lifecycle meaning + initial-status policy → distribute across `task-feature/bug/spike/research-authoring.md` (or one shared "task-common" reference if duplication becomes painful).
   - Task artifacts convention + curation (~50 lines) → `task-*-authoring.md` or a new `task-artifacts.md`.
   - Spec body-structure narrative + `## Decision Log` policy + lifecycle notable rules → `spec-authoring.md`.
   - Review close guard → consolidate in `review-authoring.md` (verify duplication first).
   - Idea "deliberately excluded fields" rationale → `idea-authoring.md` (create if absent) or condense to a one-liner.
   - `## Body sections per type` whole table → `body-conventions.md` or per-authoring `## Body` sections.
   - Spark-decide retirement note → drop or move to a CHANGELOG-style location.
4. **Keep in `frontmatter-schema.md`:** Scope, Universal rules (entire), Structural relationship fields, each type's frontmatter table only, Reference XSDs, Validator behavior + cross-file consistency, Known deferred items, Cross-references.
5. **Update inbound cross-references** in the 29 files listed below so links continue to resolve to the correct target after content moves.
6. **Run validators** after the split: `uv run plugins/a4/scripts/validate.py` and `uv run plugins/a4/scripts/generate_section_enum.py --check`.
7. **Bump `marketplace.json`** if the split is treated as a breaking documentation refactor. Likely a minor bump (7.0.0 → 7.1.0) since the YAML contract itself is unchanged — confirm with the user.

## Open Questions

1. **Split granularity** — incremental per-type vs. one bulk pass. User explicitly left this for the next session ("별도 작업으로 진행").
2. **Idea-authoring file existence** — does `references/idea-authoring.md` already exist? If not, the "deliberately excluded fields" rationale needs either a new file or a condensed inline form.
3. **Where the `## Body sections per type` table belongs** — `body-conventions.md` (single global table) vs. distributed per-authoring `## Body` sections. Both are defensible; ask the user.
4. **Whether to delete the spark-decide retirement note outright** — it is a historical breadcrumb at this point. Drop it or move to a CHANGELOG?
5. **Version-bump policy** for documentation refactors that don't change the YAML contract — minor or patch?

## Useful Commands and Outputs

```bash
# Inspect this session's main commit (97 files, +1050/−1201).
git show b9225d62c --stat

# Selected file changes from that commit:
git show b9225d62c -- plugins/a4/references/frontmatter-schema.md
git show b9225d62c -- plugins/a4/references/body-conventions.md
git show b9225d62c -- plugins/a4/scripts/transition_status.py
git show b9225d62c -- .claude-plugin/marketplace.json

# Recent a4 history (note ! = breaking).
git log --oneline -5
# b9225d62c feat(a4)!: switch body sections from <tag> blocks to ## Title Case headings
# 206c2f0ca feat(a4)!: simplify frontmatter schema across the issue families
# 2cfead766 feat(a4)!: unify task byproducts under artifacts/task/<kind>/<id>-<slug>/
# ff0dafab7 feat(a4)!: fold research into task kinds, drop spec↔research stored-reverse
# 4e6e826cc refactor(a4): split references/ (data) and docs/ (workflow); slim rules/ to pointers

# Validate before and after the next refactor.
uv run plugins/a4/scripts/validate.py
uv run plugins/a4/scripts/generate_section_enum.py --check

# Files referencing frontmatter-schema.md (29 total — update cross-refs after split):
grep -rln "frontmatter-schema" plugins/a4/

# Per-doc line counts (baseline before next session's split):
wc -l plugins/a4/references/*-authoring.md plugins/a4/references/frontmatter-schema.md plugins/a4/references/body-conventions.md
```

### Inbound references to `frontmatter-schema.md` (29 files)

```
plugins/a4/CLAUDE.md
plugins/a4/README.md
plugins/a4/agents/usecase-composer.md
plugins/a4/agents/workspace-assistant.md
plugins/a4/docs/iterate-mechanics.md
plugins/a4/docs/pipeline-shapes.md
plugins/a4/docs/skill-modes.md
plugins/a4/docs/wiki-authorship.md
plugins/a4/references/actors-authoring.md
plugins/a4/references/architecture-authoring.md
plugins/a4/references/body-conventions.md
plugins/a4/references/bootstrap-authoring.md
plugins/a4/references/context-authoring.md
plugins/a4/references/domain-authoring.md
plugins/a4/references/nfr-authoring.md
plugins/a4/references/review-authoring.md
plugins/a4/references/roadmap-authoring.md
plugins/a4/references/spec-authoring.md
plugins/a4/references/task-bug-authoring.md
plugins/a4/references/task-feature-authoring.md
plugins/a4/references/task-research-authoring.md
plugins/a4/references/task-spike-authoring.md
plugins/a4/references/usecase-authoring.md
plugins/a4/rules/a4-workspace-policies.md
plugins/a4/scripts/a4_hook.py
plugins/a4/scripts/generate_status_diagrams.py
plugins/a4/scripts/status_model.py
plugins/a4/scripts/validate_frontmatter.py
plugins/a4/skills/validate/SKILL.md
```
