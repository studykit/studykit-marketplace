---
timestamp: 2026-04-28_0252
topic: a4-xml-body-format
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-28_0252. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# a4 body format: from markdown headings to XSD-validated XML tags

## Session outcome

The a4 plugin's body-format model was redesigned and the **mechanics**
(scripts + XSDs) landed on `main` at commit `7ba8591a5`. Reference docs
and SKILL.md authoring guides still describe the **prior** format and
have not yet been rewritten — that is the open work for the next
session.

The redesigned model in one paragraph:

- Every workspace markdown file declares `type: <root>` in its YAML
  frontmatter. The body is a sequence of column-0 `<tag>...</tag>`
  blocks (lowercase + kebab-case) with markdown content between the
  open/close lines. Per-type XSD files at
  `plugins/a4/scripts/body_schemas/<type>.xsd` define the required and
  optional sections for that root. Validation parses the body, builds
  a synthetic XML document with each section's content wrapped in
  CDATA, and runs `xmlschema.XMLSchema11.iter_errors`. The XSD's
  `<xs:openContent>` accepts arbitrary additional sibling tags via
  `<xs:any notQName="...">` — the notQName lists the declared section
  names so duplicates of those are rejected by the library while
  unknown tags are tolerated.

The redesign also retires three Obsidian-specific conventions that the
old body format depended on:

- `[[wikilinks]]` and `![[embeds]]` — replaced by standard markdown
  links `[text](relative/path.md)` (with `.md` retained, navigable in
  GitHub / VSCode / any markdown renderer).
- `[^N]` footnote audit trail — replaced by a `<change-logs>` section
  containing dated bullet entries with markdown links to the causing
  issue.
- Obsidian dataview rendered views — out of scope; reverse-link data
  remains materialized in frontmatter (`usecase.implemented_by`,
  `research.cited_by`) by their owning scripts, which is the actual
  load-bearing mechanism. UI-level navigation (backlink panel, graph)
  is no longer assumed.

H1 (`# Title`) is **forbidden in body** — title belongs to the
frontmatter `title:` field. H3+ headings stay as markdown inside a
section tag.

## Architectural decisions made (and the why)

The redesign happened through dialogue. These five decisions were
each course-corrected during the session and matter when reading the
landed code:

1. **No Python source-of-truth for the schemas.** The first
   implementation tried `body_section_model.py` + an XSD regenerator.
   The user rejected this — XSDs *are* the model. The handful of XSDs
   are short enough to hand-edit and there is no need for a generator
   layer that would have to be kept in sync. The thin
   `body_schemas.py` registry helper exposes only `schema_path(type)`
   and `all_types()` — no schema knowledge duplicated in Python.

2. **No code-side duplicate detection.** A second iteration added a
   Python pass that re-parsed the XSD with ElementTree to detect
   duplicate-of-known section names. The user rejected this — "use
   the XML schema validation library". The fix was to add
   `notQName="..."` to each XSD's openContent so the library handles
   it. **All schema enforcement now lives in the XSDs.** Python only
   scans for column-0 tag boundaries (which XML parsing can't do
   because the file is not XML at the file level — markdown content
   inside sections may contain `<` characters, code fences, etc.) and
   does the frontmatter `type:` lookup.

3. **Hand-written XSDs, not auto-generated.** The XSDs originally
   carried an "Auto-generated from body_section_model.py" header from
   a prior aborted approach. The headers were rewritten to "a4 body
   XML schema. Source of truth ... Hand-edited". Edit a section by
   hand-editing the XSD; do not look for a generator script.

4. **Drop Obsidian, drop dataview, drop wikilinks, drop footnotes.**
   This was the user's explicit go-ahead after a tradeoff discussion.
   The reverse-link materialization in frontmatter (the actual value)
   stays; only the Obsidian-flavored UI affordances go.

5. **No migration script.** The user explicitly opted out:
   `migrate_body 는 필요없음. migration 안할거임.` Existing files
   under user-project workspaces will fail validation under the new
   format until they are rewritten by hand. There is no
   `migrate_body.py` and there will not be one.

## State of mechanics — what landed in commit `7ba8591a5`

| File | Status |
|---|---|
| `plugins/a4/scripts/body_schemas/*.xsd` (14 files) | Source-of-truth XSDs. Each declares a root element matching `type:`, an `<xs:all>` of required (no `minOccurs`) + optional (`minOccurs="0"`) section elements typed as `markdownContent` (mixed content, opaque), and an `<xs:openContent mode="interleave">` whose `<xs:any notQName="...">` lists every declared section name and uses `processContents="skip"`. |
| `plugins/a4/scripts/body_schemas.py` | Slim registry helper: `schema_path(type_)` and `all_types()`. |
| `plugins/a4/scripts/validate_body.py` | Rewritten end-to-end. Inline-deps add `xmlschema>=3.4`. Rules: `body-type-missing`, `body-type-unknown`, `body-stray-content`, `body-tag-invalid`, `body-tag-unclosed`, `body-xsd`. CLI is unchanged: `<a4-dir>` or `<a4-dir> <file>`, `--json`. |
| `plugins/a4/scripts/transition_status.py` | Body validation now delegates to `validate_body.run()` for spec `draft → active`, usecase `ready → implementing`, and usecase `revising → ready`. The `## Log` appender was rewritten as a canonical `<log>` block writer (rebuilds the block from existing bullets + the new entry, with stable blank-line discipline). Unused `body` parameter removed from `validate_transition` and downstream signatures. |
| `plugins/a4/scripts/register_research_citation.py` | 4-place citation now writes `<research>` (on the spec) and `<cited-by>` (on the research file) tag blocks. Bullet entries are standard markdown links with the relative path between the two files, computed via `os.path.relpath`. Idempotent re-run still works. |

Inline-script dependency change: scripts that import from
`validate_body` (currently `transition_status.py`) carry
`xmlschema>=3.4` in their PEP 723 metadata.

### File-format conventions enforced by the landed code

- **Tag form**: `^<name>$` and `^</name>$` on column 0, regex
  `^[a-z][a-z0-9-]*$` for names, no attributes, no self-closing.
  Anything else inside the body that has non-whitespace content =
  `body-stray-content` violation.
- **Blank-line discipline around tags**: the auto-emitted blocks
  always have `<tag>\n\n{content}\n\n</tag>`. The validator does not
  *require* the blank lines (CommonMark would, but that's a renderer
  concern), but the writers maintain them so files render predictably.
- **CDATA wrapping**: handled internally by `_build_xml`. Markdown
  content with literal `<` / `>` / `]]>` is preserved by
  splitting `]]>` into `]]]]><![CDATA[>` segments.
- **Frontmatter `type:` field**: required on every file; resolves to a
  schema in `body_schemas/`. Missing or unknown → validation error.

### Verified behavior (manual test fixtures, not committed)

The session ran fixtures under `/tmp/a4-test/` and `/tmp/a4-cite-test/`
(now ephemeral) covering:

- valid spec passes
- spec missing `<specification>` → `body-xsd` ("Tag 'specification' expected")
- spec with H1 in body → `body-stray-content`
- spec with `<context>...` unclosed → `body-tag-unclosed` + `body-xsd`
- spec with `<Context>` (capital) → `body-tag-invalid` + `body-stray-content` for `</Context>`
- spec with two `<specification>` blocks → `body-xsd` ("Unexpected child")
- spec with a custom `<benchmarks>` tag (single + duplicate) → passes
- spec without `type:` → `body-type-missing`
- spec with `type: bogus` → `body-type-unknown`
- `register_research_citation` first run, second-research run on same
  spec, idempotent re-run, post-run validation pass

Worth recreating these fixtures as a checked-in pytest-style suite in
the next session — they were thrown away.

## Open work

The following were enumerated and explicitly queued for the next
session. They are tracked as task list items #7 and #8.

### Doc rewrite (#7) — `frontmatter-schema.md` and every SKILL.md

`plugins/a4/references/frontmatter-schema.md` is the canonical schema
authority and is currently **out of sync** with the landed mechanics.
Every SKILL.md that prescribes body structure references the schema
and must be updated alongside it. Specifically:

- Replace "## X 섹션" / "## Heading" prose with `<x>` tag prose.
- Add the new universal rule: "every file has frontmatter `type:`
  matching the body root tag; missing or unknown is a validation
  error".
- Drop the Obsidian wikilink format rule from the universal section
  (frontmatter paths stay plain strings as today; body links become
  standard markdown).
- Drop the footnote `[^N]` + `## Changes` audit-trail prose; replace
  with the `<change-logs>` tag convention (bullet entries, dated +
  link to causing issue).
- Per-family tables: replace "required body sections" rows that named
  `## Heading` with rows that name `<tag>`.
- Update the "Status writers" table for any rows whose mechanics
  changed (the spec `draft → active` body validation now reads as
  "validate_body XSD pass" rather than "Context + Specification
  headings present"). The skill caller column does not change.
- All SKILL.md files that show body templates need their templates
  rewritten to the new shape:
  - `plugins/a4/skills/spec/SKILL.md` — Step 5 file template; the
    `## Decision Log` / `## Open Questions` / `## Rejected
    Alternatives` / `## Consequences` / `## Examples` / `## Research`
    listings.
  - `plugins/a4/skills/usecase/SKILL.md` — UC body sections.
  - `plugins/a4/skills/task/SKILL.md` — task body sections.
  - `plugins/a4/skills/arch/SKILL.md` — architecture.md template
    (Overview, Technology Stack, Component Diagram, Components, Test
    Strategy, Changes).
  - `plugins/a4/skills/idea/SKILL.md`, `roadmap/SKILL.md`,
    `research/SKILL.md`, the review-related skills, `drift/SKILL.md`,
    `compass/SKILL.md` if they describe body structure.

The XSDs (committed) are now the authoritative section-name list for
each `type`. When updating doc tables, read each XSD to confirm the
current required/optional split.

### Reference shuffle (#8) — replace `obsidian-conventions.md`

- Delete `plugins/a4/references/obsidian-conventions.md`.
- Add `plugins/a4/references/body-conventions.md` (~30 lines) that
  documents:
  - Tag form: lowercase kebab-case, column-0, no attributes.
  - Blank-line discipline around tags (writers emit it; validator
    tolerates absence; renderers care).
  - Link form: standard markdown `[text](path.md)` for internal,
    `[text](https://...)` for external; `.md` retained on internal
    links.
  - `<change-logs>` and `<log>` section conventions: bullets only,
    dated entries, append-only.
  - Cross-link path: `frontmatter-schema.md` and SKILL.md files
    should cite this doc by relative path.
- Search all SKILL.md and references for `obsidian-conventions.md`
  citations and rewrite them to point at `body-conventions.md`.

### Plugin-level CLAUDE.md (the "Conventions" section)

`plugins/a4/CLAUDE.md` currently says:

> Obsidian markdown throughout. Body uses `[[wikilinks]]` and
> `![[embeds]]`. Frontmatter paths are plain strings (no brackets, no
> `.md`).

Replace with:

> Tagged-XML body format. Each file declares `type:` in frontmatter
> matching its body root tag; sections are column-0
> `<tag>...</tag>` blocks (lowercase, kebab-case) with markdown
> content. Body links are standard markdown
> `[text](relative/path.md)`. Frontmatter list paths stay plain
> strings without `.md`.

### Marketplace version bump

When #7 and #8 land, bump the a4 version in
`.claude-plugin/marketplace.json`. The current version (3.0.0) was
set by commit `67ae5d513` for the prior model. The new format is a
breaking change → 4.0.0.

## Side notes / gotchas the next session will hit

- **Pyright noise.** `validate_body.py`, `transition_status.py`, and
  `register_research_citation.py` show Pyright "Import could not be
  resolved" diagnostics for `xmlschema`, sibling Python modules, and
  the local `markdown` shadowing the stdlib name. These are runtime-
  fine — uv resolves PEP 723 deps at script run time and the sibling
  imports work because `sys.path` includes the script directory.
  Ignore the diagnostics.

- **Existing handoff topics nearby.** `plugins/a4/.handoff/` already
  has `pipeline-restructure`, `run-parallel-isolation`,
  `status-model-consolidation`. None overlap with this thread; the
  body-format redesign is a fresh topic.

- **The conversation that produced this design** ran very long and
  course-corrected three or four times. The narrative arc was:
  (a) propose `validate_references.py` to catch
  cross-reference drift; (b) realize the bigger problem is the body
  format itself; (c) iterate through markdown-with-tags, tags-only,
  then XSD-validated; (d) drop the Python source-of-truth idea after
  user feedback; (e) drop the Python duplicate-detection workaround
  after user feedback. The landed shape is the result of those
  corrections, not the first sketch. Revisiting "should we go back
  to..." is unlikely to be productive — the user is decisive on the
  current shape.

- **XSD 1.1 features are required.** `xs:openContent` is XSD 1.1
  only. The schemas declare `vc:minVersion="1.1"`. The xmlschema
  Python library must use `XMLSchema11` (not `XMLSchema`) — this is
  done in `validate_body._xsd_errors`.

- **`<xs:all>` ordering does not matter.** The schemas list elements
  alphabetically per group (required first, then optional) by
  convention but XSD 1.1's `<xs:all>` is order-insensitive. Authors
  can place sections in any order in the body.

- **`validate_references.py` (REF rules) was put on hold.** The
  original session goal was to add a cross-reference / convention
  drift detector. After diagnosing the underlying body format as the
  larger issue, that work was deferred. With the format change
  consolidating tag enums into XSDs and dropping
  Obsidian-specifics, several originally proposed REF rules
  (REF001-redux, REF007 wikilink-form) become moot or trivial. Worth
  re-scoping after #7 and #8 land.

## Recommended next-session opening

1. Read this handoff in full.
2. Read commit `7ba8591a5` (`git show 7ba8591a5`) to see the landed
   code shape.
3. Read each XSD under `plugins/a4/scripts/body_schemas/` to confirm
   the section enums.
4. Start #7: open `plugins/a4/references/frontmatter-schema.md` and
   make a top-down pass replacing heading prose with tag prose, using
   the XSDs as the canonical section-name list.
5. Once #7's per-family tables are updated, propagate to each
   SKILL.md whose body template now mismatches.
6. Land #8 (`body-conventions.md`) as a follow-up commit.
7. Bump marketplace.json to 4.0.0 in the same PR or a final commit.
