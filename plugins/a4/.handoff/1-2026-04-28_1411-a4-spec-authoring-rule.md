---
sequence: 1
timestamp: 2026-04-28_1411
timezone: KST +0900
topic: a4-xml-body-format
previous: 2026-04-28_1340_section-enum-and-extract-section-infra.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-28_1411. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Author the first per-type authoring guide promised by the prior
handoff: a hand-edited path-scoped rule at `a4/spec/**/*.md` that
consolidates spec-authoring guidance for any LLM about to read or
edit an `a4/spec/<id>-<slug>.md` file.

This is suggested follow-up #1 from the prior handoff
(`2026-04-28_1340_section-enum-and-extract-section-infra.md`). The
infrastructure piece — `rules/`, `/a4:install-rules`,
`/a4:uninstall-rules`, `extract_section.py`, the generator-owned
`a4-section-enum.md` — landed in commit `e46511acf`. This session
ships the first **substantive** rule on top of that infrastructure.

## Current State

- Branch: `main`. One pre-handoff commit already on disk:
  `a3593d91f` *feat(a4): add a4-spec-authoring path-scoped rule*.
- Working tree carries pre-existing user edits to
  `global/skills/handoff/SKILL.md` and
  `plugins/a4/skills/handoff/SKILL.md` (handoff workflow refactor —
  new filename format `<n>-<TIMESTAMP>-<slug>.md`, files written
  directly under `.handoff/` with no topic subdirectories). Those
  edits were **left untouched**; they are not part of this session
  and the user is mid-edit on them.
- This handoff file is the first under the new format/path scheme:
  written directly at `plugins/a4/.handoff/`, not inside the
  `a4-xml-body-format/` topic subdirectory used by the four prior
  handoffs on this thread. Sequence numbering restarts at `1` per
  the new convention — it counts files matching `<number>-*.md`
  directly under `.handoff/`, not legacy files in the topic
  subdirectory.
- Marketplace version: `3.1.0 → 3.2.0`.

## Changes Made

### Files created

- **`plugins/a4/rules/a4-spec-authoring.md`** (new). Hand-edited
  authoring rule, `paths: ["a4/spec/**/*.md"]`. Sections:
  - Preamble pointing to `frontmatter-schema.md §Spec`,
    `spec-triggers.md`, `body-conventions.md` for full background.
  - **When a spec is warranted** — the four conjunctive criteria
    (multiple options, non-trivial trade-off, non-recoverable from
    code, plausibly revisitable) extracted from
    `references/spec-triggers.md`.
  - **Conversational triggers B1–B6** — multi-option enumeration,
    trade-off language, uncertainty markers, prior-spec references
    (supersede candidates), task-implementer architectural-choice
    exit, mid-`/a4:run` architecture-impacting choice. Mirrors the
    triggers reference verbatim.
  - **Anti-patterns** — routine choices, framework-mandated,
    post-hoc justification, multiple decisions per spec, bug-fix
    "use the right tool". Surfaced because LLMs reading a spec
    folder are the audience most likely to over-author.
  - **How to author — always via `/a4:spec`** — explicit instruction
    to never hand-craft a spec with `Write`. Three modes: activate
    existing, revise existing, new record. `extract_section.py`
    pointer for the read-not-author case.
  - **Frontmatter contract** — full YAML template with field-by-field
    rules. Captures the registrar-owned `research:` field, the
    `related:` vs `research:` distinction, plain-string path form
    (no brackets, no `.md`), date format.
  - **Lifecycle and writer ownership** — the transition graph plus
    the two automatic flips (`active → superseded` cascade, no
    reverse from `deprecated`). Restates "all status changes flow
    through `transition_status.py`."
  - **Body shape** — required `<context>` + `<specification>`,
    optional `<decision-log>` (append-only, ADR replacement) /
    `<open-questions>` / `<rejected-alternatives>` / `<consequences>`
    / `<examples>` / `<research>` (registrar-owned) /
    `<change-logs>` / `<log>` (writer-owned). Notes that
    `<migration-plan>` is not used (migration → tasks).
  - **Body-link form** — markdown links in body, plain strings in
    frontmatter list paths.
  - **Common validator errors** — `body-stray-content`,
    `body-xsd` for missing required sections, `body-tag-invalid`,
    same-tag nesting, H1 in body. Includes the manual validator
    invocation.
  - **Don't list** — eight imperative bullets condensing the
    writer-ownership / supersession / decision-log / one-decision-
    per-spec / no-post-hoc rules.
  - **After authoring** — wiki nudge summary (LLM doesn't run it
    when reading a spec, but should know it exists).
  - **Cross-references** — links to the four reference docs and
    the spec skill.

### Files modified

- **`plugins/a4/CLAUDE.md`** — added a third bullet to the
  "Per-section reads and path-scoped rules" section documenting the
  `a4-<type>-authoring.md` family pattern (hand-edited per-type
  authoring guides scoped to `a4/<type>/**/*.md`, no generator
  backing, no pre-commit drift check). Names `a4-spec-authoring.md`
  as the first instance.
- **`.claude-plugin/marketplace.json`** — bumped a4 from `3.1.0` to
  `3.2.0` (new feature: new path-scoped rule).

### Files explicitly NOT modified

- `commands/install-rules.md` and `commands/uninstall-rules.md`
  iterate `${CLAUDE_PLUGIN_ROOT}/rules/*.md`, so they pick up the
  new rule automatically. No edits required.
- `.githooks/pre-commit` — the new rule is hand-edited (not
  generator-owned), so no drift block was added.
- `plugins/a4/scripts/generate_section_enum.py` and
  `plugins/a4/scripts/extract_section.py` — unchanged.

## Key Files

- `plugins/a4/rules/a4-spec-authoring.md` — the new rule. The
  source of truth for "how to author a spec" guidance that
  auto-loads in installed user projects.
- `plugins/a4/rules/a4-section-enum.md` — the prior rule. Different
  shape: generator-owned bullet block, sentinel-comment markers,
  pre-commit drift check. The two files together establish the
  generator-owned vs hand-edited split that future rules will
  follow.
- `plugins/a4/CLAUDE.md` — the working notes for plugin developers;
  now documents both rule shapes side by side.
- `plugins/a4/skills/spec/SKILL.md` — the authoring skill that
  installs the spec; the new rule consistently routes LLMs back to
  it for authoring (vs hand-editing).
- `plugins/a4/references/frontmatter-schema.md` §Spec,
  `references/spec-triggers.md`, `references/body-conventions.md`,
  `scripts/body_schemas/spec.xsd` — the four canonical sources
  consolidated by the rule. The rule restates rather than replaces;
  references are still the authority.

## Decisions and Rationale

- **Hand-edited, not generator-owned.** Authoring guides are prose
  shaped by judgment about anti-patterns, "don't" rules, and which
  schema details deserve emphasis at the rule layer vs the
  reference layer. None of that is mechanically derivable from
  `body_schemas/spec.xsd` or the SKILL.md, so a generator would
  produce something less useful than hand-prose. Trade-off: when the
  underlying schema or skill changes, the rule must be revised by
  hand — there is no drift check. Acceptable given the rate of
  change on these docs is low and the cross-reference list at the
  bottom of the rule names every upstream source.
- **Path scope `a4/spec/**/*.md`, not `a4/**/*.md`.** Authoring
  guidance is type-specific. A reader editing a usecase file does
  not need to load spec-authoring details; the cross-reference list
  inside each authoring rule keeps the rule's footprint tight.
  Future rules (`a4-task-authoring.md`,
  `a4-usecase-authoring.md`, …) follow the same scoping pattern.
- **Restate, don't replace.** The rule duplicates content from the
  references (B1–B6, anti-patterns, frontmatter table). This is
  intentional: rules auto-load while references must be opened
  explicitly, and an LLM about to edit a spec needs the rules
  *immediately available*, not behind a follow-up `Read`. The
  references remain the long-form source for the *why*; the rule is
  the short-form *what to do/not do*.
- **Two sections highlighted as "writer-owned" / "registrar-owned":**
  `status:` (`transition_status.py`) and `research:` /
  `<research>` / `<cited-by>` (`register_research_citation.py`).
  Plus `<log>` (writer-owned). Repeat-emphasized in three places —
  frontmatter contract, body shape, "Don't" list — because these
  are the most common LLM-attempted edits that should never happen
  manually.
- **No `<migration-plan>` mention beyond a one-line negative.** The
  rule explicitly says migration belongs in `task/<id>-<slug>.md`,
  matching `frontmatter-schema.md §Spec`. Reduces the chance of an
  LLM inventing a migration section because it sees migration
  language in the conversation.
- **Version bump `3.1.0 → 3.2.0` (minor).** New feature surface
  (one new rule file) without breaking changes. Same rationale as
  the prior session's `3.0.0 → 3.1.0` bump.
- **`topic: a4-xml-body-format` reused.** This session continues
  the path-scoped-rule thread that started under
  `a4-xml-body-format` (the prior handoff explicitly named per-type
  authoring guides as the next deliverable on that thread). New
  topic was considered and rejected — too narrow a fragmentation
  for a thread that has been broadly interpreted as "body format
  + rules infrastructure."
- **New handoff filename format.** Switched from
  `<TIMESTAMP>_<slug>.md` inside `<topic>/` subdirectory to
  `<n>-<TIMESTAMP>-<slug>.md` directly under `.handoff/`, per the
  uncommitted user edits to
  `plugins/a4/skills/handoff/SKILL.md`. Sequence starts at `1` —
  the four prior handoffs in `a4-xml-body-format/` are not
  recounted; the skill counts only `<n>-*.md` files at the top
  level of `.handoff/`.

## Important Dialog

- User asked in 한국어 for `a4-spec-authoring.md` to be written.
  Auto-mode active throughout — no interactive checkpoints, no
  scope clarifications. Single-shot rule authoring.
- Earlier in-session, user ran `/clear` then opened
  `plugins/a4/skills/handoff/SKILL.md` in the IDE. Those uncommitted
  edits redefined the handoff workflow (new filename format,
  flat `.handoff/` directory). Handoff was written under that new
  format because the user is the one driving the change.
- User did not specify any `additional requirements` for the
  handoff, so this file follows the defaults.

## Validation

- `uv run plugins/a4/scripts/generate_section_enum.py --check` →
  `OK — section enum in a4-section-enum.md matches body_schemas/.`
  exit `0`. Section-enum drift check passes (the new rule does not
  affect this generator).
- `git status --short` after the pre-handoff commit shows only the
  unrelated handoff SKILL.md edits and the unstaged new handoff
  file (this one). No accidental staging.
- `git rev-parse HEAD` after pre-handoff commit:
  `a3593d91f017426adacae7a891b52e6b00be7eb5`.
- **Skipped:** `validate_body.py`, `validate_frontmatter.py`,
  `transition_status.py`. The new rule does not add or modify any
  workspace file under `a4/` — it ships a static markdown rule under
  `plugins/a4/rules/`. None of the body/frontmatter validators
  apply to plugin rule files.
- **Skipped:** Live `/a4:install-rules` rerun against a throwaway
  `git init`'d project. Justification: the install command iterates
  `${CLAUDE_PLUGIN_ROOT}/rules/*.md` mechanically — the same loop
  that handled `a4-section-enum.md` will handle `a4-spec-authoring.md`
  identically. The prior handoff already verified the loop end-to-end.

## Known Issues and Risks

- **Restated content drifts independently.** The rule duplicates
  fragments of `frontmatter-schema.md §Spec` (lifecycle graph, field
  table) and `spec-triggers.md` (B1–B6, anti-patterns). When the
  references change, the rule must be revised by hand. There is no
  drift check. Mitigation: cross-reference footer names every source
  doc. Recommend a quick rule-vs-reference scan whenever a
  references doc lands a substantive change.
- **`paths:` frontmatter is not yet validated.** No script confirms
  that `paths:` is a list of valid glob strings. Today this is a
  hand-written field. If a future authoring rule has a typo'd path
  glob, it will silently fail to auto-load. Not addressed; the
  `rules/` directory is small enough that visual review catches
  mistakes.
- **Spec-trigger duplication risk.** B1–B6 also live in
  `spec-triggers.md`. If a new conversational trigger is added there
  (e.g., `B7`), the authoring rule will silently lag. Mitigation:
  same as above — cross-reference footer.
- **Pre-existing user edits to handoff SKILL.md are uncommitted.**
  `global/skills/handoff/SKILL.md` and
  `plugins/a4/skills/handoff/SKILL.md` were modified before this
  session began. They were intentionally not committed by this
  session because they are not part of this session's work. The
  user can commit them separately.

## Next Steps

In priority order, carrying over from the prior handoff's "suggested
follow-ups" with #1 now complete:

1. **`a4-task-authoring.md`** — second per-type authoring guide.
   Same shape as `a4-spec-authoring.md`. Source material:
   `plugins/a4/skills/task/SKILL.md`,
   `references/frontmatter-schema.md §Task`,
   `references/spec-triggers.md` (the upward-propagation section
   for the `kind: feature` smell check),
   `scripts/body_schemas/task.xsd`. Tasks are the most-written type
   in steady state, so rule auto-load value is highest here. Bump to
   `3.3.0` on commit.

2. **`a4-usecase-authoring.md`** — third. UCs are rarer to write
   but when authored often need anti-patterns reinforced (e.g.,
   "UC scope vs spec scope"). Source: `skills/usecase/SKILL.md`,
   `references/frontmatter-schema.md §Usecase`,
   `references/wiki-authorship.md`,
   `scripts/body_schemas/usecase.xsd`.

3. **`a4-review-authoring.md`** — fourth. The `kind:
   finding | gap | question` discriminator and the
   `iterate-mechanics.md` resolution path are the high-value bits
   to consolidate. Source: `skills/review/SKILL.md`,
   `references/frontmatter-schema.md §Review`,
   `references/iterate-mechanics.md`,
   `scripts/body_schemas/review.xsd`.

4. **Per-wiki-page authoring rules.** `a4-architecture-authoring.md`,
   `a4-context-authoring.md`, etc. Lower priority than the issue-
   family rules because wiki pages are most often edited via the
   wiki-nudge step of an issue skill — the issue rule already covers
   that flow. Worth doing only if direct wiki editing turns out to
   be common.

5. **Optional: `--multi` mode for `extract_section.py`.** Carried
   over from the prior handoff. Speculative; only do if real usage
   shows churn.

## Open Questions

- **Should authoring rules cite the SKILL.md as the canonical
  source, or restate it?** This session's rule chose a hybrid: it
  routes the LLM to `/a4:spec` for authoring but restates schema
  details so a read/edit context does not require the SKILL.md. The
  alternative (rule defers everything to the skill) is tighter but
  less useful when the user opens an existing spec and wants quick
  guidance. Decided in favor of the hybrid, but reconsider when the
  second authoring rule lands.
- **Should rules carry their own version field?** The plugin
  version reflects all rule changes, but rules ship independently
  of skills and an installed user might be on a stale rule symlink
  if the plugin is offline. Not addressed; symlinks resolve through
  the live plugin path so this is a non-issue under normal use.
- **Do path-scoped rules conflict in `<project-root>/.claude/rules/`
  if two plugins ship rules with the same basename?** Carried over
  from the prior handoff (open question #2 there). Not relevant
  while a4 is the only namespace using `a4-` prefixes, but worth
  formalizing if the marketplace grows.

## Useful Commands and Outputs

```bash
# Verify the new rule file shape (frontmatter + path scope)
head -5 plugins/a4/rules/a4-spec-authoring.md

# Section-enum drift check still clean (unaffected by new rule)
uv run plugins/a4/scripts/generate_section_enum.py --check

# List all path-scoped rules (now two)
ls plugins/a4/rules/

# After installing rules in a user project, verify auto-load scope
# (rule should load when reading any a4/spec/*.md, not other a4/ files)
ls <project-root>/.claude/rules/

# Pre-handoff commit
git show --stat a3593d91f
```

Sample output from the section-enum check:

```
OK — section enum in a4-section-enum.md matches body_schemas/.
```
