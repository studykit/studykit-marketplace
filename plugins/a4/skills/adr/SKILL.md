---
name: adr
description: "This skill should be used when the user has reached a decision through conversation with the LLM and wants to document it as an ADR. Writes the ADR to `a4/adr/<id>-<slug>.md` with proper frontmatter and body, cites any related `./research/<slug>.md` artifacts as Obsidian wikilinks in body prose, and nudges affected wiki pages (architecture / context / domain / actors / nfr). Triggers: 'record this decision', 'document our decision', 'capture the decision', 'write this up as an ADR', 'let's make this a decision', or after the user and LLM converge on a choice. Accepts either no argument (extract decision from recent conversation) or a short summary / title (used as a seed). Also handles re-invocation on an existing draft ADR to finalize it. Requires an `a4/` workspace."
argument-hint: <optional: short decision summary or title>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# ADR Recorder

Documents a decision that was reached through conversation into `a4/adr/<id>-<slug>.md`, cites supporting research if any, and nudges affected wiki pages. This skill does not facilitate the decision itself — it captures an already-converged conclusion from the current session.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing the ADR file at `status: draft`, finalizing an existing draft via `transition_status.py`, citing research from `./research/<slug>.md` (Obsidian wikilink style in body prose), running the `adr-content-guard` agent immediately before finalization to flag prescriptive / implementation leakage, performing the in-situ wiki nudge, setting `status` via dialogue.
- **Out:** no research (that's `/a4:research`). No reviewer for the decision *content itself* — whether the chosen option is correct is the user's own thinking, not machine-critiqued. The content guard checks body shape (descriptive-not-prescriptive), not option choice. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/adr/` exists; create with `mkdir -p` if missing.

## Step 1: Detect mode — new record or finalize existing

Two modes dispatch from the seed + recent conversation:

- **(a) Finalize existing.** The user is referring to an ADR already recorded earlier as `draft`. Signals: `$ARGUMENTS` contains an ADR id (`12`, `adr/12`), slug fragment, or title that matches an existing `a4/adr/*.md` at `status: draft`; or the recent conversation referenced a specific draft ADR by path/id. Detect by `Glob a4/adr/*.md` + frontmatter read; confirm with the user before proceeding (one light question: "Finalize `adr/<id>-<slug>` as `final`?"). If confirmed, skip Steps 2–5 and jump to **Step 6: Finalize via writer**.
- **(b) New record.** Default. The seed is a topic/title for an ADR not yet on disk. Continue with Step 2.

If the user's phrasing is ambiguous between (a) and (b), ask once which they mean.

## Step 2: Extract the decision

Two input modes:

- **No argument.** Read recent conversation context. Identify the decision that was reached — the topic, the chosen option, the rationale, and any alternatives discussed. If no clear decision emerged (conversation is still exploratory, multiple threads unresolved), ask the user which one to record.
- **Short summary / title.** Use `$ARGUMENTS` as a seed. Still draw the full content (context, rationale, alternatives, next steps) from recent conversation — the argument is a hint, not the source.

Draft the following in a scratch summary (do not write to disk yet):

- **Title** — a short, human-readable phrase (becomes `title:` and the H1). Example: "Use Postgres for primary store".
- **Decision** — the chosen option as a one-liner (becomes `decision:` frontmatter). Example: "Adopt Postgres 16; defer MySQL and SQLite."
- **Context** — why the decision was needed, constraints, stakeholders.
- **Body outline** — the set of `##` headings that best fit this decision's shape. `## Context` and `## Decision` are **required**; beyond those, include only sections the conversation actually produced content for (e.g., `## Options Considered`, `## Rejected Alternatives`, `## Consequences`, `## Open Questions`). Do not emit placeholder sections.
- **Supersedes** — when the conversation references a prior ADR being replaced (B4 in [`references/adr-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/adr-triggers.md)), search `a4/adr/*.md` for the prior ADR and propose `supersedes: [adr/<prior-id>-<slug>]`. The `transition_status.py` cascade flips the prior ADR to `superseded` on `→ final`.
- **Related research** — candidate `./research/<slug>.md` files (see Step 3).

Present this draft to the user before proceeding. Iterate until the user confirms the substance is right.

## Step 3: Discover related research

Offer two sources for `[[research/<slug>]]` body citations:

1. **Auto-scan.** `Glob ./research/*.md` (relative to project root). For each candidate, compare the file's `topic:` frontmatter or slug to the decision's title/topic. Propose plausible matches to the user.
2. **User-specified.** If the user mentioned a research file during the conversation (by slug, topic, or path), include it verbatim.

Confirm the final list with the user. The list may be empty — ADRs do not require prior research.

Research citations are recorded by `register_research_citation.py` (Step 5b below), which atomically writes them in four places: the ADR's `research:` frontmatter list and `## Research` body section, plus the research file's `cited_by:` frontmatter list and `## Cited By` body section. Do **not** hand-edit any of those four — always invoke the registrar so forward and reverse stay in sync.

## Step 4: Decide on status via dialogue

Interpret from the user's natural-language signals about confidence and commitment:

- Signals for `final` — "we've decided", "let's go with X", "this is settled", "record as final", "확정", "결정했어".
- Signals for `draft` — "let's record this but I want to sit with it", "still somewhat open", "tentative", "두고 보자", "아직 여지 있음".

When the signal is ambiguous, ask once with a light phrasing that does not feel like a binary form: *"Record as `final`, or leave as `draft` for now?"*

**Record the signal — do not write it yet.** The file is always born at `status: draft` in Step 5. If the signal is `final`, Step 6 calls `transition_status.py` to flip it. This keeps every status change on an ADR file flowing through the single writer.

## Step 5: Allocate id, slug, and write the file

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/adr/<id>-<slug>.md`.

4. Use the `Write` tool. Content:

```markdown
---
id: <id>
title: "<title>"
status: draft
decision: "<one-line decision>"
supersedes: []
research: []
related: []
tags: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
# <title>

## Context

<Why this decision was needed; constraints; stakeholders. Reference any related research in prose: "See [[research/<slug>]] for the comparison.">

## Decision

<The chosen option and the rationale. Connect to any cited research.>

<Additional `##` sections as the conversation produced them — e.g., Options Considered, Rejected Alternatives, Consequences, Open Questions.>
```

Body structure rules and the full frontmatter field schema (including `framework`, the `transition_status.py`-enforced `## Context` + `## Decision` requirement, the descriptive-not-prescriptive principle, and the no-`[[task/...]]`-in-`## Consequences` rule) are in [`frontmatter-schema.md §ADR`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md). Read that file before drafting the body and frontmatter; it shapes Step 2's body outline.

Report the full file path: "ADR recorded at `<path>` as `draft`."

## Step 5b: Register research citations

For each research artifact confirmed in Step 3, invoke the registrar to atomically record the citation in four places (ADR frontmatter `research:`, ADR body `## Research`, research frontmatter `cited_by:`, research body `## Cited By`):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
  "<project-root>/a4" \
  "research/<slug>" \
  "adr/<id>-<slug>"
```

Idempotent — if a side already records the citation, that side is left alone. Skip the step entirely when Step 3's research list is empty. Run once per (research, adr) pair when there are multiple research artifacts.

The registrar bumps the research file's `updated:` field and never touches its `status:` — research lifecycle (`draft | final | standalone | archived`) stays the user's call.

## Step 6: Finalize via writer (if signal was `final`)

Invoke only when the user signaled `final` in Step 4 (new-record mode) **or** the whole invocation is in finalize-existing mode from Step 1.

### Step 6a: Run the content guard

Before calling the writer, invoke the `adr-content-guard` agent (via the Task tool) on the ADR file. The guard reads the body and reports prescriptive / implementation leakage per [`references/content-guard.md`](references/content-guard.md). Pass it:

- the workspace path (`<project-root>/a4`)
- the ADR file's relative path (`adr/<id>-<slug>`)

Surface the agent's report to the user:

- If verdict is `CLEAN`, proceed to Step 6b silently with a one-line note ("Content guard: clean.").
- If verdict is `LEAKAGE DETECTED`, print the report verbatim and ask the user to choose:
  - **Revise** — pause finalization; the user (with the LLM's help) edits the body to address the cited leaks, then re-runs `/a4:adr` in finalize-existing mode (Step 1 (a)). The guard re-runs.
  - **Override** — proceed to Step 6b as-is. Record the override reason verbatim from the user; the writer's `--reason` flag in Step 6b prepends `[guard override: <reason>]` so the `## Log` entry preserves the trace.

Never auto-edit the file based on the guard's suggestions. The user retains final authorship.

### Step 6b: Call the writer

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" "<project-root>/a4" \
  --file adr/<id>-<slug>.md \
  --to final \
  --reason "<one-line decision summary>" \
  --json
```

The writer:

1. Enforces mechanical validation (title no placeholder; `## Context` and `## Decision` sections present). If validation fails, the exit code is `2` and `validation_issues` lists the gaps — fix them and re-run (never use `--force` here).
2. Flips `status: draft → final`, bumps `updated:`, appends a `## Log` entry `<today> — draft → final — <reason>`.
3. If `supersedes:` is non-empty, walks each same-family target and flips it `final → superseded` in the same invocation. Targets already `superseded` are skipped; targets not at `final` (e.g., still `draft`) are reported as `not-terminal-active` and left alone. Cross-family entries are silently skipped.

If the writer returns `ok: true`, report the primary flip plus any cascades. If it returns validation issues, surface them verbatim to the user and do not retry blindly — the gap usually means the body needs another pass in Step 5.

## Step 7: In-situ wiki nudge

After writing (or finalizing) the ADR, apply the in-situ wiki nudge per [`references/wiki-nudge.md`](references/wiki-nudge.md): map the change type to the affected wiki page(s), confirm with the user, edit with footnote + `## Changes` entry, and defer to a `kind: gap` review item when the user does not want to apply it now. Skip silently on a fresh workspace (no `a4/*.md` wiki pages).

## Step 8: Report

Summarize to the user:

- ADR path and id.
- Final status (`draft` or `final`), and if finalized this invocation, any supersedes cascades the writer performed.
- Content guard outcome (only when finalization ran in this invocation): `clean`, `leakage detected — revised`, or `leakage detected — overridden by user`. For the override case, surface the override reason recorded in the `## Log` entry.
- Research cited in body (list of wikilinks, if any).
- Wiki pages updated or deferred review items opened (with ids).
- Reminder: the file (and any cascaded supersedes-target edits) is left in the working tree — commit at the user's convenience.

## Non-goals

- **Do not research.** If the decision needs more investigation, stop and tell the user to run `/a4:research` first.
- **Do not review whether the decision is correct.** Whether the chosen option is the right one is the user's own thinking; no machine critique pass exists for that (unlike `/a4:research-review` for research artifacts). The `adr-content-guard` agent in Step 6a checks body shape (prescriptive / implementation leakage) only, not option correctness.
- **Do not auto-edit based on guard output.** The guard returns suggestions; only the user (or the user-directed LLM in a follow-up turn) modifies the file. Override always remains available.
- **Do not commit.** Leave files in the working tree.
- **Do not hand-edit `status:`.** All status changes on ADR files flow through `transition_status.py`; this skill never writes `status: final` directly nor uses `Edit`/`Write` to change an existing ADR's status.
- **Do not auto-populate `supersedes:`.** The user sets it explicitly in Step 2 if this ADR replaces prior ones.
- **Do not write implementation, do not render reverse views.** See the ADR-content rules in [`frontmatter-schema.md §ADR`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) (descriptive-not-prescriptive principle; `## Consequences` carries no task wikilinks; `justifies:` is derived on demand and never written).
