---
name: spec
description: "This skill should be used when the user has converged on the shape of an artifact (format, protocol, schema, renderer rule, CLI surface) and wants to commit it as a living specification. Writes the spec to `a4/spec/<id>-<slug>.md` with proper frontmatter and body, cites any related `./research/<slug>.md` artifacts as standard markdown links, optionally records ADR-style decision rationale inline as `<decision-log>` entries, and nudges affected wiki pages (architecture / context / domain / actors / nfr). Triggers: 'document this format', 'write up the spec', 'capture this shape', 'this is the spec', 'spec this out', or after the user and LLM converge on a prescriptive shape. Accepts either no argument (extract spec from recent conversation) or a short summary / title (used as a seed). Also handles re-invocation on an existing draft spec to activate it. Requires an `a4/` workspace."
argument-hint: <optional: short spec summary or title>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Spec Recorder

> **Authoring contract:** the contract for `a4/spec/**/*.md` — frontmatter, body sections, `<decision-log>` append-only rule, lifecycle, supersedes cascade, registrar-owned `research:` — lives in [`rules/a4-spec-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-spec-authoring.md). Spec-trigger detection (when a moment is spec-worthy) lives in [`references/spec-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md). This skill orchestrates capture + activate + wiki nudge.

Documents a converged-on shape (format, protocol, schema, renderer rule, CLI surface, etc.) into `a4/spec/<id>-<slug>.md`, cites supporting research if any, optionally records the decision rationale inline, and nudges affected wiki pages. This skill does not facilitate the design itself — it captures an already-converged shape from the current session.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing the spec file at `status: draft`, activating an existing draft via `transition_status.py`, citing research from `./research/<slug>.md` (standard markdown links in body prose, registered atomically by `register_research_citation.py`), recording append-only `<decision-log>` entries that explain why the spec landed the way it did, performing the in-situ wiki nudge, setting `status` via dialogue.
- **Out:** no research (that's `/a4:research`). No reviewer for the spec *content itself* — whether the chosen shape is correct is the user's own thinking, not machine-critiqued. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/spec/` exists; create with `mkdir -p` if missing.

## Step 1: Detect mode — new record, activate existing, or revise existing

Three modes dispatch from the seed + recent conversation:

- **(a) Activate existing.** The user is referring to a spec already recorded earlier as `draft`. Signals: `$ARGUMENTS` contains a spec id (`12`, `spec/12`), slug fragment, or title that matches an existing `a4/spec/*.md` at `status: draft`; or the recent conversation referenced a specific draft spec by path/id. Detect by `Glob a4/spec/*.md` + frontmatter read; confirm with the user before proceeding (one light question: "Activate `spec/<id>-<slug>`?"). If confirmed, skip Steps 2–5 and jump to **Step 6: Activate via writer**.
- **(b) Revise existing.** The user wants to extend or amend a live spec. Signals: `$ARGUMENTS` references an `active` spec; or the conversation produced a refinement or new rule for an existing spec. The skill edits the spec body in place and appends a `<decision-log>` entry with today's date and the substance of the change. The frontmatter is left at `status: active` — `transition_status.py` is not invoked.
- **(c) New record.** Default. The seed is a topic/title for a spec not yet on disk. Continue with Step 2.

If the user's phrasing is ambiguous, ask once which mode they mean.

## Step 2: Extract the spec

Two input modes:

- **No argument.** Read recent conversation context. Identify the converged shape — what artifact it describes, the prescriptive rules, and any decisions explaining why the shape landed this way. If no clear shape emerged, ask the user which one to record.
- **Short summary / title.** Use `$ARGUMENTS` as a seed; still draw the full content from recent conversation.

Draft a scratch summary covering the fields and sections defined in [`rules/a4-spec-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-spec-authoring.md) (`title`, `decision` one-liner, required `<context>` + `<specification>`, optional sections only when the conversation produced content for them, candidate `supersedes:` if the conversation referenced a predecessor). Do **not** emit placeholder sections.

Present the draft to the user before proceeding. Iterate until the substance is confirmed.

## Step 3: Discover related research

Offer two sources for citations:

1. **Auto-scan.** `Glob ./research/*.md` (relative to project root). For each candidate, compare the file's `topic:` frontmatter or slug to the spec's title/topic. Propose plausible matches.
2. **User-specified.** If the user named a research file during the conversation, include it verbatim.

Confirm the final list with the user. Empty is fine — specs do not require prior research. Step 5b runs the registrar.

## Step 4: Decide on status via dialogue

Interpret confidence/commitment from the user:

- `active` signals — "this is the spec", "lock this in", "확정", "이걸로 가자".
- `draft` signals — "tentative", "still open", "두고 보자", "아직 여지 있음".

If ambiguous, ask once: *"Activate now, or leave as `draft` for now?"*

**Record the signal — do not write it yet.** The file is always born at `status: draft` in Step 5; Step 6 flips it via the writer if `active` was signaled.

## Step 5: Allocate id, slug, and write the file

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/spec/<id>-<slug>.md`.

4. Use the `Write` tool. Frontmatter shape, required body sections (`<context>`, `<specification>`), optional sections (`<decision-log>`, `<open-questions>`, `<rejected-alternatives>`, `<consequences>`, `<examples>`), and tag-form rules are defined in [`rules/a4-spec-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-spec-authoring.md). Initial `status:` is always `draft`; `decision:` is the one-liner that Step 6 will quote in the activate transition. Do **not** hand-write `<research>` — Step 5b registers it.

Report the full file path: "Spec recorded at `<path>` as `draft`."

## Step 5b: Register research citations

For each research artifact confirmed in Step 3, invoke the registrar:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
  "<project-root>/a4" \
  "research/<slug>" \
  "spec/<id>-<slug>"
```

Idempotent. Skip entirely when Step 3's list is empty; run once per (research, spec) pair otherwise. The registrar owns the four-place atom (spec `research:` + `<research>`, research `cited_by:` + `<cited-by>`) and bumps the research file's `updated:`.

## Step 6: Activate via writer (if signal was `active`)

Invoke only when the user signaled `active` in Step 4, or the whole invocation is in activate-existing mode from Step 1 (a).

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" "<project-root>/a4" \
  --file spec/<id>-<slug>.md \
  --to active \
  --reason "<one-line shape summary>" \
  --json
```

The writer's lifecycle / validation / supersedes-cascade behavior is defined in [`rules/a4-spec-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-spec-authoring.md) §Lifecycle. On `ok: true`, report the primary flip plus any cascades. On `exit 2`, surface `validation_issues` verbatim and return to Step 5 — never retry with `--force`.

## Step 7: In-situ wiki nudge

After writing (or activating) the spec, apply the in-situ wiki nudge per [`references/wiki-nudge.md`](references/wiki-nudge.md): map the spec scope to the affected wiki page(s), confirm with the user, edit with a `<change-logs>` entry on the modified page (dated bullet + markdown link to this spec), and defer to a `kind: gap` review item when the user does not want to apply it now. Skip silently on a fresh workspace (no `a4/*.md` wiki pages).

## Step 8: Report

Summarize to the user:

- Spec path and id.
- Final status (`draft` or `active`), and if activated this invocation, any supersedes cascades the writer performed.
- Research cited in body (list of relative-path links, if any).
- Wiki pages updated or deferred review items opened (with ids).
- Reminder: the file (and any cascaded supersedes-target edits) is left in the working tree — commit at the user's convenience.

## Non-goals

- **Do not research.** If the spec needs more investigation, stop and tell the user to run `/a4:research` first.
- **Do not review whether the shape is correct.** Whether the chosen shape is the right one is the user's own thinking; no machine critique pass exists for that.
- **Do not commit.** Leave files in the working tree.
- **Do not auto-populate `supersedes:`** or retire specs unprompted. The user sets `supersedes:` in Step 2; `→ deprecated` is a manual user call via `transition_status.py`.

(Frontmatter / body / lifecycle / writer-only field rules — including the `<decision-log>` append-only invariant and the `status:` writer-only rule — live in the spec authoring rule, not here.)
