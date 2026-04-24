---
name: decision
description: "This skill should be used when the user has reached a decision through conversation with the LLM and wants to document it as an ADR. Writes the decision to `a4/decision/<id>-<slug>.md` with proper frontmatter and body, cites any related `./research/<slug>.md` artifacts as Obsidian wikilinks in body prose, and nudges affected wiki pages (architecture / context / domain / actors / nfr). Triggers: 'record this decision', 'document our decision', 'capture the decision', 'write this up as an ADR', 'let's make this a decision', or after the user and LLM converge on a choice. Accepts either no argument (extract decision from recent conversation) or a short summary / title (used as a seed). Requires an `a4/` workspace."
argument-hint: <optional: short decision summary or title>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Decision Recorder

Documents a decision that was reached through conversation into `a4/decision/<id>-<slug>.md`, cites supporting research if any, and nudges affected wiki pages. This skill does not facilitate the decision itself — it captures an already-converged conclusion from the current session.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing the decision file, citing research from `./research/<slug>.md` (Obsidian wikilink style in body prose), performing the in-situ wiki nudge, setting `status` and `decision:` one-liner via dialogue.
- **Out:** no research (that's `/a4:research`). No automated reviewer (research review is `/a4:research-review`; decision authorship is the user's own thinking, not machine-critiqued). No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/decision/` exists; create with `mkdir -p` if missing.

## Step 1: Extract the decision

Two input modes:

- **(a) No argument.** Read recent conversation context. Identify the decision that was reached — the topic, the chosen option, the rationale, and any alternatives discussed. If no clear decision emerged (conversation is still exploratory, multiple threads unresolved), ask the user which one to record.
- **(b) Short summary / title.** Use `$ARGUMENTS` as a seed. Still draw the full content (context, rationale, alternatives, next steps) from recent conversation — the argument is a hint, not the source.

Draft the following in a scratch summary (do not write to disk yet):

- **Title** — a short, human-readable phrase (becomes `title:` and the H1). Example: "Use Postgres for primary store".
- **Decision** — the chosen option as a one-liner (becomes `decision:` frontmatter). Example: "Adopt Postgres 16; defer MySQL and SQLite."
- **Context** — why the decision was needed, constraints, stakeholders.
- **Options considered** — the alternatives discussed, even those quickly dismissed.
- **Rationale** — why the chosen option won against the others.
- **Rejected alternatives** — each with a specific reason for rejection.
- **Next steps** — concrete follow-up actions.
- **Related research** — candidate `./research/<slug>.md` files (see Step 2).

Present this draft to the user before proceeding. Iterate until the user confirms the substance is right.

## Step 2: Discover related research

Offer two sources for `[[research/<slug>]]` body citations:

1. **Auto-scan.** `Glob ./research/*.md` (relative to project root). For each candidate, compare the file's `topic:` frontmatter or slug to the decision's title/topic. Propose plausible matches to the user.
2. **User-specified.** If the user mentioned a research file during the conversation (by slug, topic, or path), include it verbatim.

Confirm the final list with the user. The list may be empty — decisions do not require prior research.

Research is cited in **body prose only**, as Obsidian wikilinks (e.g., `See [[research/grpc-streaming]] for the comparison.`). Do **not** put research references in frontmatter — research lives outside the `a4/` workspace and is not an issue-family artifact.

## Step 3: Decide on status via dialogue

Do not default `status` mechanically. Interpret from the user's natural-language signals about confidence and commitment:

- Signals for `final` — "we've decided", "let's go with X", "this is settled", "record as final", "확정", "결정했어".
- Signals for `draft` — "let's record this but I want to sit with it", "still somewhat open", "tentative", "두고 보자", "아직 여지 있음".

When the signal is ambiguous, ask once with a light phrasing that does not feel like a binary form: *"Record as `final`, or leave as `draft` for now?"*

The user may flip status later by editing the file directly or by invoking this skill again on the same topic.

## Step 4: Allocate id and slug

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/decision/<id>-<slug>.md`.

## Step 5: Write the file

Use the `Write` tool. Content:

```markdown
---
id: <id>
title: "<title>"
status: <draft | final>
decision: "<one-line decision>"
supersedes: []
related: []
tags: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
# <title>

## Context

<Why this decision was needed; constraints; stakeholders. Reference any related research in prose: "See [[research/<slug>]] for the comparison.">

## Options Considered

- **<Option A>** — <brief summary>
- **<Option B>** — <brief summary>
- …

## Decision

<The chosen option and the rationale. Connect to any cited research.>

## Rejected Alternatives

- **<Option B>** — <specific reason for rejection>
- **<Option C>** — <specific reason for rejection>

## Next Steps

- <Concrete follow-up action>
- <Another action>
```

Sections are scope-dependent:

- **Required:** `## Context`, `## Decision`.
- **Typically present:** `## Options Considered`, `## Rejected Alternatives`, `## Next Steps`.
- **Omit** sections that do not apply. For example, a decision with only one considered option has no `## Rejected Alternatives`; a purely conceptual decision may have no `## Next Steps`.

Frontmatter fields follow `${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md §Decision`:

- `id` — integer from `allocate_id.py`.
- `title` — the title from Step 1.
- `status` — `draft` or `final` from Step 3.
- `decision` — the one-liner from Step 1.
- `supersedes` — if this replaces prior decisions, list their workspace-root-relative paths (`decision/<id>-<slug>`). Usually empty.
- `related` — soft cross-references to other issues inside `a4/` (other decisions, UCs, tasks). **Not** for research — research lives outside `a4/` and is cited in body only.
- `tags` — free-form labels.
- `created` / `updated` — today (`YYYY-MM-DD`).

Report the full file path: "Decision recorded at `<path>`."

## Step 6: In-situ wiki nudge

After writing the decision, check whether it affects existing wiki pages at `a4/` root. Discover candidates via `Glob a4/*.md`. Skip silently when no wiki pages exist (fresh workspace).

| Change type | Likely wiki target |
|-------------|--------------------|
| Technology / framework / library choice | `architecture.md` (Technology Stack, External Dependencies) |
| Process, scope, or constraint shift | `context.md` (Problem Framing, Success Criteria) |
| New actor or role | `actors.md` |
| New domain concept | `domain.md` |
| Non-functional requirement change | `nfr.md` |

For each applicable candidate, present the proposed update and ask the user to confirm. For every confirmed update:

1. Edit the wiki page — update the affected section, append a footnote marker `[^N]` inline (monotonic per file), and append a `## Changes` line `[^N]: <YYYY-MM-DD> — [[decision/<id>-<slug>]]` pointing to this decision.
2. Bump the wiki page's `updated:` frontmatter to today.

See `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md §Wiki Update Protocol` for footnote format.

If the user defers any update, open a review item instead so the gap does not disappear:

1. Allocate an id: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"`.
2. Write `a4/review/<id>-<slug>.md` with:
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: decision/<decision-id>-<slug>`
   - `wiki_impact: [<affected wiki basenames>]`

The wiki close guard (at session close) and drift detector (between sessions) re-surface unresolved impact later.

Use judgment — minor decisions (naming conventions, purely internal choices with no wiki-visible effect) skip the nudge.

## Step 7: Report

Summarize to the user:

- Decision path and id.
- Status (`draft` or `final`).
- Research cited in body (list of wikilinks, if any).
- Wiki pages updated or deferred review items opened (with ids).
- Reminder: the file is left in the working tree — commit at the user's convenience.

## Non-goals

- **Do not research.** If the decision needs more investigation, stop and tell the user to run `/a4:research` first.
- **Do not review the decision.** Decision authorship is the user's own thinking; no machine critique pass exists (unlike `/a4:research-review` for research artifacts).
- **Do not commit.** Leave files in the working tree.
- **Do not auto-populate `supersedes:`.** The user sets it explicitly in Step 1 if this decision replaces prior ones.
