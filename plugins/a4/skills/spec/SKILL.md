---
name: spec
description: "This skill should be used when the user has converged on the shape of an artifact (format, protocol, schema, renderer rule, CLI surface) and wants to commit it as a living specification. Writes the spec to `a4/spec/<id>-<slug>.md` with proper frontmatter and body, cites any related `./research/<slug>.md` artifacts as Obsidian wikilinks, optionally records ADR-style decision rationale inline as `## Decision Log` entries, and nudges affected wiki pages (architecture / context / domain / actors / nfr). Triggers: 'document this format', 'write up the spec', 'capture this shape', 'this is the spec', 'spec this out', or after the user and LLM converge on a prescriptive shape. Accepts either no argument (extract spec from recent conversation) or a short summary / title (used as a seed). Also handles re-invocation on an existing draft spec to activate it. Requires an `a4/` workspace."
argument-hint: <optional: short spec summary or title>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Spec Recorder

Documents a converged-on shape (format, protocol, schema, renderer rule, CLI surface, etc.) into `a4/spec/<id>-<slug>.md`, cites supporting research if any, optionally records the decision rationale inline, and nudges affected wiki pages. This skill does not facilitate the design itself — it captures an already-converged shape from the current session.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing the spec file at `status: draft`, activating an existing draft via `transition_status.py`, citing research from `./research/<slug>.md` (Obsidian wikilink style in body prose), recording append-only `## Decision Log` entries that explain why the spec landed the way it did, performing the in-situ wiki nudge, setting `status` via dialogue.
- **Out:** no research (that's `/a4:research`). No reviewer for the spec *content itself* — whether the chosen shape is correct is the user's own thinking, not machine-critiqued. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/spec/` exists; create with `mkdir -p` if missing.

## Step 1: Detect mode — new record, activate existing, or revise existing

Three modes dispatch from the seed + recent conversation:

- **(a) Activate existing.** The user is referring to a spec already recorded earlier as `draft`. Signals: `$ARGUMENTS` contains a spec id (`12`, `spec/12`), slug fragment, or title that matches an existing `a4/spec/*.md` at `status: draft`; or the recent conversation referenced a specific draft spec by path/id. Detect by `Glob a4/spec/*.md` + frontmatter read; confirm with the user before proceeding (one light question: "Activate `spec/<id>-<slug>`?"). If confirmed, skip Steps 2–5 and jump to **Step 6: Activate via writer**.
- **(b) Revise existing.** The user wants to extend or amend a live spec. Signals: `$ARGUMENTS` references an `active` spec; or the conversation produced a refinement or new rule for an existing spec. The skill edits the spec body in place and appends a `## Decision Log` entry with today's date and the substance of the change. The frontmatter is left at `status: active` — `transition_status.py` is not invoked.
- **(c) New record.** Default. The seed is a topic/title for a spec not yet on disk. Continue with Step 2.

If the user's phrasing is ambiguous, ask once which mode they mean.

## Step 2: Extract the spec

Two input modes:

- **No argument.** Read recent conversation context. Identify the shape that converged — what artifact it describes, the prescriptive rules (grammar, fields, formats, examples), and any decisions taken along the way that explain why the shape landed this way. If no clear shape emerged, ask the user which one to record.
- **Short summary / title.** Use `$ARGUMENTS` as a seed. Still draw the full content (context, prescriptive rules, decisions, alternatives, open questions) from recent conversation — the argument is a hint, not the source.

Draft the following in a scratch summary (do not write to disk yet):

- **Title** — a short, human-readable phrase (becomes `title:` and the H1). Example: "Reading-order tree footnote layout".
- **Decision** — the chosen shape as a one-liner (becomes `decision:` frontmatter). Example: "Caller annotations rendered as bracketed footnote tokens with two-space padding."
- **Context** — why the spec exists, what scope it covers, what artifact it describes.
- **Specification** — the prescriptive content. Grammar, fields, format rules, examples. This is the heart of the spec — the part downstream code, validators, and review items must conform to.
- **Decision Log** (optional) — append-only notes on the decisions that shaped the spec. Each entry: short date-prefixed line summarizing what was chosen and why. Empty is fine for a fresh spec; entries accrete over time as the spec is revised.
- **Body outline** — the set of `##` headings that best fit this spec's shape. `## Context` and `## Specification` are **required**; beyond those, include only sections the conversation actually produced content for (e.g., `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Consequences`, `## Examples`). Do not emit placeholder sections.
- **Supersedes** — when the conversation references a prior spec being replaced, search `a4/spec/*.md` for the prior spec and propose `supersedes: [spec/<prior-id>-<slug>]`. The `transition_status.py` cascade flips the prior spec(s) to `superseded` on `→ active`.
- **Related research** — candidate `./research/<slug>.md` files (see Step 3).

Present this draft to the user before proceeding. Iterate until the user confirms the substance is right.

## Step 3: Discover related research

Offer two sources for `[[research/<slug>]]` body citations:

1. **Auto-scan.** `Glob ./research/*.md` (relative to project root). For each candidate, compare the file's `topic:` frontmatter or slug to the spec's title/topic. Propose plausible matches to the user.
2. **User-specified.** If the user mentioned a research file during the conversation (by slug, topic, or path), include it verbatim.

Confirm the final list with the user. The list may be empty — specs do not require prior research.

Research citations are recorded by `register_research_citation.py` (Step 5b below), which atomically writes them in four places: the spec's `research:` frontmatter list and `## Research` body section, plus the research file's `cited_by:` frontmatter list and `## Cited By` body section. Do **not** hand-edit any of those four — always invoke the registrar so forward and reverse stay in sync.

## Step 4: Decide on status via dialogue

Interpret from the user's natural-language signals about confidence and commitment:

- Signals for `active` — "this is the spec", "lock this in", "downstream should conform to this", "확정", "이걸로 가자".
- Signals for `draft` — "let's record this but I want to sit with it", "still somewhat open", "tentative", "두고 보자", "아직 여지 있음".

When the signal is ambiguous, ask once with a light phrasing that does not feel like a binary form: *"Activate now, or leave as `draft` for now?"*

**Record the signal — do not write it yet.** The file is always born at `status: draft` in Step 5. If the signal is `active`, Step 6 calls `transition_status.py` to flip it. This keeps every status change on a spec file flowing through the single writer.

## Step 5: Allocate id, slug, and write the file

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/spec/<id>-<slug>.md`.

4. Use the `Write` tool. Content:

```markdown
---
id: <id>
title: "<title>"
status: draft
decision: "<one-line shape summary>"
supersedes: []
research: []
related: []
labels: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
# <title>

## Context

<Why this spec exists; what artifact it describes; the scope it covers. Reference any related research in prose: "See [[research/<slug>]] for the comparison.">

## Specification

<The prescriptive content. Grammar, fields, format rules, examples. Use sub-headings (`###`) freely to break up large specs.>

<Additional `##` sections as the conversation produced them — e.g., Decision Log, Open Questions, Rejected Alternatives, Consequences, Examples.>
```

Body structure rules and the full frontmatter field schema (including the `transition_status.py`-enforced `## Context` + `## Specification` requirement, the prescriptive principle, and the append-only `## Decision Log` rule) are in [`frontmatter-schema.md §Spec`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md). Read that file before drafting the body and frontmatter; it shapes Step 2's body outline.

Report the full file path: "Spec recorded at `<path>` as `draft`."

## Step 5b: Register research citations

For each research artifact confirmed in Step 3, invoke the registrar to atomically record the citation in four places (spec frontmatter `research:`, spec body `## Research`, research frontmatter `cited_by:`, research body `## Cited By`):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
  "<project-root>/a4" \
  "research/<slug>" \
  "spec/<id>-<slug>"
```

Idempotent — if a side already records the citation, that side is left alone. Skip the step entirely when Step 3's research list is empty. Run once per (research, spec) pair when there are multiple research artifacts.

The registrar bumps the research file's `updated:` field and never touches its `status:` — research lifecycle (`draft | final | standalone | archived`) stays the user's call.

## Step 6: Activate via writer (if signal was `active`)

Invoke only when the user signaled `active` in Step 4 (new-record mode) **or** the whole invocation is in activate-existing mode from Step 1 (a).

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" "<project-root>/a4" \
  --file spec/<id>-<slug>.md \
  --to active \
  --reason "<one-line shape summary>" \
  --json
```

The writer:

1. Enforces mechanical validation (title no placeholder; `## Context` and `## Specification` sections present). If validation fails, the exit code is `2` and `validation_issues` lists the gaps — fix them and re-run (never use `--force` here).
2. Flips `status: draft → active`, bumps `updated:`, appends a `## Log` entry `<today> — draft → active — <reason>`.
3. If `supersedes:` is non-empty, walks each same-family target and flips it `{active|deprecated} → superseded` in the same invocation. Targets already `superseded` are skipped; targets at `draft` are reported as `not-supersedable` and left alone. Cross-family entries are silently skipped.

If the writer returns `ok: true`, report the primary flip plus any cascades. If it returns validation issues, surface them verbatim to the user and do not retry blindly — the gap usually means the body needs another pass in Step 5.

## Step 7: In-situ wiki nudge

After writing (or activating) the spec, apply the in-situ wiki nudge per [`references/wiki-nudge.md`](references/wiki-nudge.md): map the spec scope to the affected wiki page(s), confirm with the user, edit with footnote + `## Changes` entry, and defer to a `kind: gap` review item when the user does not want to apply it now. Skip silently on a fresh workspace (no `a4/*.md` wiki pages).

## Step 8: Report

Summarize to the user:

- Spec path and id.
- Final status (`draft` or `active`), and if activated this invocation, any supersedes cascades the writer performed.
- Research cited in body (list of wikilinks, if any).
- Wiki pages updated or deferred review items opened (with ids).
- Reminder: the file (and any cascaded supersedes-target edits) is left in the working tree — commit at the user's convenience.

## Non-goals

- **Do not research.** If the spec needs more investigation, stop and tell the user to run `/a4:research` first.
- **Do not review whether the shape is correct.** Whether the chosen shape is the right one is the user's own thinking; no machine critique pass exists for that.
- **Do not commit.** Leave files in the working tree.
- **Do not hand-edit `status:`.** All status changes on spec files flow through `transition_status.py`; this skill never writes `status: active` directly nor uses `Edit`/`Write` to change an existing spec's status. (Setting `status: deprecated` is the user's manual call via `transition_status.py`; the skill does not retire specs unprompted.)
- **Do not auto-populate `supersedes:`.** The user sets it explicitly in Step 2 if this spec replaces prior ones.
- **`## Decision Log` is append-only.** Earlier entries are never edited or removed. Corrections are added as new entries that explain why the prior reasoning no longer holds.
