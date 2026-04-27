---
timestamp: 2026-04-28_0356
topic: a4-xml-body-format
previous: 2026-04-28_0252_body-xml-mechanics.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-28_0356. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# a4 body format: docs aligned with the landed XSD mechanics

## Session outcome

Open work item #7 ("doc rewrite for `frontmatter-schema.md` and every
SKILL.md") **and** #8 ("replace `obsidian-conventions.md` with
`body-conventions.md`") from the prior handoff have both landed in
commit `423831f50` on `main`. Working tree is clean. The branch is
6 ahead of `origin/main` and has not been pushed.

The mechanics shipped in `7ba8591a5` (XSDs + `validate_body.py` +
`transition_status.py` body-validation hookup) are now consistent with
every doc reachable from the plugin.

## What landed in `423831f50`

42 files changed (+901 / -698), one new file, one deletion. The commit
is doc-only — no script or schema changes.

### New file

- `plugins/a4/references/body-conventions.md` (~200 lines). Covers tag
  form (column-0 `<tag>...</tag>`, lowercase kebab-case, no attributes,
  no nesting, blank-line discipline), the link form rule (standard
  markdown `[text](relative/path.md)` with `.md` retained), the
  `<change-logs>` audit-trail format and Wiki Update Protocol (when /
  how / defer / close guard), and the `<log>` writer-ownership rule.
  Replaces `obsidian-conventions.md`.

### Deleted file

- `plugins/a4/references/obsidian-conventions.md`.

### Rewritten

- `plugins/a4/references/frontmatter-schema.md` — full rewrite. New
  universal `type:` rule (every file declares `type:` matching its body
  root tag, resolves to a per-type XSD). New "Body sections per type"
  section with three tables (wiki / issues / spark+research) sourced
  from the XSDs. The path-references rule says "no brackets, no `.md`"
  with `body-conventions.md` cited for body links. The validator-
  behavior section is split into a frontmatter-rules table and a
  body-rules table (with the six body rules: `body-type-missing`,
  `body-type-unknown`, `body-stray-content`, `body-tag-invalid`,
  `body-tag-unclosed`, `body-xsd`).
- `plugins/a4/CLAUDE.md` Conventions block restated. The new rule:
  "Tagged-XML body format. Each file declares `type:` in frontmatter
  matching its body root tag; sections are column-0 `<tag>...</tag>`
  blocks (lowercase, kebab-case) with markdown content. Body links are
  standard markdown `[text](relative/path.md)`. Frontmatter list paths
  stay plain strings without `.md`." References list now includes
  `body-conventions.md` and drops `obsidian-conventions.md`.

### Body templates rewritten in every SKILL.md

Each skill's "compose / write the file" template now uses tag form
(column-0 `<tag>` / `</tag>` blocks with markdown content between).
Required vs optional sections in each template match the relevant XSD
under `plugins/a4/scripts/body_schemas/`.

| Skill | Template uses |
|---|---|
| `spec/SKILL.md` | `<context>`, `<specification>`; optional `<decision-log>`, `<open-questions>`, `<rejected-alternatives>`, `<consequences>`, `<examples>`, `<research>` (registrar-owned) |
| `usecase/SKILL.md` | `<goal>`, `<situation>`, `<flow>`, `<expected-outcome>`; optional `<validation>`, `<error-handling>`, `<dependencies>`, `<change-logs>`, `<log>` |
| `task/SKILL.md` | `<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`; optional `<interface-contracts>`, `<log>`, `<change-logs>`, `<why-discarded>` |
| `arch/SKILL.md` | `<overview>`, `<technology-stack>`, `<components>`, `<test-strategy>`; optional `<external-dependencies>`, `<component-diagram>`, `<change-logs>` |
| `domain/SKILL.md` | `<concepts>`; optional `<relationships>`, `<state-transitions>`, `<change-logs>` |
| `roadmap/SKILL.md` | `<plan>` (carries Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points as H3+ headings); optional `<change-logs>` |
| `auto-bootstrap/SKILL.md` + `references/bootstrap-md-template.md` | `<environment>`, `<launch>`, `<verify>` (verified commands / smoke scenario / test isolation flags as H3+ subsections); optional `<change-logs>` |
| `idea/SKILL.md` | empty body on capture; optional `<why-this-matters>`, `<notes>`, `<change-logs>`, `<log>` |
| `research/SKILL.md` | `<context>`; `<options>` for `comparative` mode, `<findings>` for `single` mode; optional `<cited-by>` (registrar-owned), `<change-logs>` |
| `spark-brainstorm/SKILL.md` | `<ideas>`; optional `<notes>`, `<change-logs>` |
| `auto-usecase/SKILL.md` | composer agent emits the same UC template as `/a4:usecase` |

`drift/SKILL.md`, `validate/SKILL.md`, `handoff/SKILL.md`,
`run/SKILL.md` reference the new tag form where they describe other
skills' artifacts.

### Per-skill `references/*.md` updated

`spec/references/wiki-nudge.md`, `task/references/discard.md`,
`usecase/references/{iteration-entry, review-report, session-closing}.md`,
`auto-bootstrap/references/{bootstrap-md-template, issue-handling}.md`,
`roadmap/references/planning-guide.md`,
`run/references/{failure-classification, uc-ship-review}.md` —
all updated to:

- replace `## Heading` references with `<tag>` references
- replace footnote / `## Changes` audit-trail prose with `<change-logs>`
- replace `[[wikilinks]]` with standard markdown links
- drop "Obsidian dataview" / "Obsidian transclusion" mentions

### Cross-cutting reference docs updated

- `iterate-mechanics.md` — Section 4 now describes the `<change-logs>`
  bullet form; the discipline list (§5) names `<log>` instead of `## Log`.
- `wiki-authorship.md` — bootstrap row now describes "the `<verify>`
  section (verified commands, smoke scenario, test isolation flags) is
  read directly by `/a4:run`"; the roadmap row says "links to bootstrap"
  rather than "Obsidian transclusion". The cross-stage feedback section
  cites `<change-logs>` instead of footnote.
- `pipeline-shapes.md` — AC source tables, mandatory citation rules,
  and common-omission examples updated to tag form.
- `spec-triggers.md` — single mention of `## Open Questions` rewritten
  to `<open-questions>` section.

### Agent files updated

`usecase-composer.md`, `usecase-reviser.md`, `usecase-reviewer.md`,
`arch-reviewer.md`, `domain-reviewer.md`, `roadmap-reviewer.md`,
`task-implementer.md`, `test-runner.md`, `workspace-assistant.md` —
review-item templates now use `type: review` frontmatter + a single
`<description>` body section (with bolded paragraph labels —
**Summary.** / **Evidence.** / **Suggestion.** etc. — instead of
separate `## Heading` blocks). All `## Log` references switched to
`<log>`. Body cross-references switched from `[[...]]` to standard
markdown links.

## Architectural decisions made this session

Two choices required judgment beyond simple find-and-replace:

1. **Wiki page `kind:` becomes `type:`.** The prior schema had
   wiki pages declare `kind: <name>` (with the validator enforcing
   `kind == filename`). The new universal rule is "every file declares
   `type:` matching its body root tag", which already does the same job
   for wiki pages. Decision: drop `kind:` from wiki frontmatter and use
   only `type:`. Issues that have an *orthogonal* sub-categorization
   (`task.kind: feature|spike|bug`, `review.kind: finding|gap|question`)
   keep `kind:` *and* gain `type:` — the two fields mean different
   things on those families.

   This is a doc-only assertion right now. `validate_frontmatter.py`
   still expects wiki `kind:` (see "Open: validator code change"
   below). The doc captures the target shape so the next session can
   land the validator change consistently.

2. **Source attribution stays inline, not a new tag.** `auto-usecase`'s
   `## Source` convention (input / research / code / implicit) used to
   be its own `## Source` section on every UC. The new format has no
   `<source>` tag in `usecase.xsd`, and adding one would force every
   `/a4:usecase`-authored UC to include it (the XSD couldn't restrict
   the requirement to auto-usecase output). Decision: source attribution
   becomes a one-line blockquote at the start of `<situation>`, not a
   separate tag. Updated in `auto-usecase/SKILL.md` and the composer
   agent. The XSD remains untouched.

## Open work for the next session

The handoff originally listed three follow-ups (#7, #8, marketplace
bump). #7 and #8 are done. Two items remain.

### Marketplace 4.0.0 bump

`.claude-plugin/marketplace.json` still names a4 at 3.0.0 (set by
`67ae5d513` for the prior body model). The new format is a breaking
change. Bump to 4.0.0 in a small standalone commit:

```
docs(a4)!: bump marketplace version to 4.0.0
```

The exclamation mark + breaking-change body explanation matches the
existing convention seen on `67ae5d513`. The breaking-change description
should name (a) the body format switch (XSDs replace headings) and
(b) the wiki-page `kind:` → `type:` rename.

Verify after the bump:

```bash
grep -n '"name"\|"version"' .claude-plugin/marketplace.json
```

The block for `a4` should show `"version": "4.0.0"`.

### Validator code change — wiki `kind:` → `type:`

The doc says wiki pages drop `kind:` in favor of `type:`, but
`plugins/a4/scripts/validate_frontmatter.py` still requires `kind:` on
wiki files (see lines 66, 146–147, 298–306 of that file as of
`423831f50`). Touchpoints:

- `SCHEMAS["wiki"]` — change `required={"kind", "updated"}` to
  `required={"type", "updated"}`; change `enums={"kind": WIKI_KINDS}`
  to `enums={"type": WIKI_KINDS}`.
- The dispatch logic that picks the schema family (around line
  146–154) currently reads `fm.get("kind")` for wiki dispatch and
  `fm.get("type")` for spark dispatch. Unify on `type:` for both.
- The wiki-basename check (around line 298–306) — replace the
  `kind-filename-mismatch` rule with `type-filename-mismatch` (or
  rename more conservatively).
- `WIKI_KINDS` in `common.py` may want to be renamed to `WIKI_TYPES`.
- Issue / spark schemas: add `type:` as a required-with-fixed-value
  field (or a soft validator that warns on mismatch but doesn't block).
  The body validator already requires `type:` — the frontmatter
  validator could just trust that. Decide whether to keep the rule
  duplicated or rely on `validate_body.py` for the type assertion.
- Update tests under `plugins/a4/tests/` accordingly. Run
  `uv run plugins/a4/scripts/validate_frontmatter.py <a4-dir>` against
  fixtures after the change.

This is a real code change, not a doc edit — keep it in its own commit
separate from the marketplace bump:

```
refactor(a4)!: replace wiki `kind:` with `type:` in validate_frontmatter
```

Once both land, the marketplace bump can be the final commit in the
breaking-change set.

## State of the working tree at handoff time

- HEAD: `423831f50 docs(a4)!: rewrite docs for tagged-XML body format`
- Working tree: clean (`git status` reports no changes).
- Branch: `main`, 6 ahead of `origin/main` — none of the body-format
  work has been pushed yet.
- Recent commit chain:
  ```
  423831f50 docs(a4)!: rewrite docs for tagged-XML body format        ← this session
  bbb859912 docs(handoff): snapshot a4-xml-body-format session state  ← prior handoff
  7ba8591a5 feat(a4)!: validate body XML against per-type XSD
  67ae5d513 docs(a4)!: align reference docs and bump a4 to 3.0.0
  721bcb4a8 refactor(a4)!: introduce /a4:spec skill, retire /a4:adr
  1ed60c19c refactor(a4)!: replace adr family with spec in workspace model
  ```
- Memory: nothing was added to `memory/` this session. The user
  preferences for this session are captured in the existing memory
  index (no changes required).

## Recommended next-session opening

The user explicitly asked to **restart fresh in the next session**.
That means: do not try to continue this conversation's thread; just
read this handoff and pick the next concrete piece of work.

1. Read this handoff in full.
2. Read commit `423831f50` (`git show 423831f50 --stat | head -50`)
   to see the doc shape that landed.
3. Pick one of:
   - **Marketplace bump** (1-line edit, standalone commit). Quick and
     fully self-contained. Good "first thing" task.
   - **Validator `kind:` → `type:` migration** (code change in
     `validate_frontmatter.py` + `common.py` + tests). Larger; do this
     before pushing if you want the schema and validator to ship in the
     same breaking-change wave.
4. After the validator change, run the full validator pass against an
   existing user-project workspace (or a fresh fixture) to confirm:
   ```bash
   uv run plugins/a4/scripts/validate.py <a4-dir>
   ```
   The aggregator runs frontmatter + body + status-consistency; all
   three should report `OK` on a workspace whose files have been
   migrated to `type:` + tag form.
5. Do **not** attempt to migrate user-project workspaces. Per the
   prior handoff's explicit decision (`migrate_body 는 필요없음`),
   workspaces predating the new format will fail validation until
   rewritten by hand. There is no migration script and there will not
   be one.

## Side notes / gotchas

- **`.handoff/` files are point-in-time snapshots.** Three prior
  handoff files in this same `a4-xml-body-format/` topic still mention
  `## Changes` / `[[wikilinks]]` / `obsidian-conventions.md`. Those
  references are intentionally stale per the handoff banner — do not
  edit them.
- **Pyright still complains.** The Pyright noise on `validate_body.py`
  / `transition_status.py` / `register_research_citation.py` (Import
  could not be resolved on `xmlschema`, sibling modules, the local
  `markdown` module) is unchanged from the prior handoff. Runtime is
  fine; ignore the diagnostics.
- **`research-reviewer.md`'s `## Research Review Report`** is the
  agent's own output template heading, not body content of an a4
  workspace file. Left as-is — it's the agent's report format, not a
  body-section tag.
- **Section headers in the reference docs themselves** (e.g.,
  `## Examples` in `commit-message-convention.md`,
  `### Examples` in `wiki-authorship.md`) are headings within the
  reference doc as a markdown document, not body-section names that
  validate_body.py would care about. They were intentionally left
  unchanged.

## Recommended commit-set after the next session lands

1. `refactor(a4)!: replace wiki kind: with type: in validate_frontmatter`
   — code + tests.
2. `docs(a4)!: bump marketplace version to 4.0.0` — `.claude-plugin/marketplace.json`.
3. `docs(handoff): snapshot a4-xml-body-format session state` —
   the next session's `/handoff` output, on top of the chain.

After the chain settles, push to `origin/main` (currently 6 ahead).
The user will decide when to push; do not push without their say-so.
