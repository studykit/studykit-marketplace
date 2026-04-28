---
name: spec
description: "This skill should be used when the user has converged on the shape of an artifact (format, protocol, schema, renderer rule, CLI surface) and wants to commit it as a living specification. Writes the spec to `a4/spec/<id>-<slug>.md` with proper frontmatter and body, soft-links any related research tasks (a4/task/research/<id>-<slug>.md) via standard markdown body links and optional `related:` frontmatter entries, optionally records the decision rationale inline as `<decision-log>` entries, and nudges affected wiki pages (architecture / context / domain / actors / nfr). Triggers: 'document this format', 'write up the spec', 'capture this shape', 'this is the spec', 'spec this out', or after the user and LLM converge on a prescriptive shape. Accepts either no argument (extract spec from recent conversation) or a short summary / title (used as a seed). Also handles re-invocation on an existing draft spec to activate it. Requires an `a4/` workspace."
argument-hint: <optional: short spec summary or title>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
---

# Spec Recorder

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/references/spec-authoring.md`. This skill orchestrates capture + activate + wiki nudge.

Documents a converged-on shape (format, protocol, schema, renderer rule, CLI surface, etc.) into `a4/spec/<id>-<slug>.md`, soft-links supporting research tasks if any, optionally records the decision rationale inline, and nudges affected wiki pages. This skill does not facilitate the design itself — it captures an already-converged shape from the current session.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing the spec file at `status: draft`, activating an existing draft via `transition_status.py`, soft-linking research tasks (`a4/task/research/<id>-<slug>.md`) via standard markdown body links and optional `related:` frontmatter entries, recording append-only `<decision-log>` entries, performing the in-situ wiki nudge, setting `status` via dialogue.
- **Out:** no investigation (use `/a4:task` with `kind=research` first if research is needed). No reviewer for the spec *content itself*. No commit.

## Pre-flight

1. Resolve the project root: `git rev-parse --show-toplevel`. If not a git repo, abort with a clear message.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/spec/` exists; create with `mkdir -p` if missing.

## Workflow

### Step 1: Detect mode

Three modes (new record, activate existing, revise existing): `references/mode-detection.md`.

### Steps 2–6: Extract, discover research, decide status, write, activate

Procedure: `references/extract-and-write.md`. Covers extracting the converged shape, discovering related research tasks, deciding `draft` vs `active` from dialogue, allocating id + writing the file (with optional `related:` entries pointing at the research tasks and inline body links), and activating via `transition_status.py`.

### Step 7: In-situ wiki nudge

Apply per `references/wiki-nudge.md`: map the spec scope to the affected wiki page(s), confirm with the user, edit with a `<change-logs>` entry on the modified page (dated bullet + markdown link to this spec), and defer to a `kind: gap` review item when the user does not want to apply it now. Skip silently on a fresh workspace (no `a4/*.md` wiki pages).

### Step 8: Report

Summarize to the user:

- Spec path and id.
- Final status (`draft` or `active`), and if activated this invocation, any supersedes cascades the writer performed.
- Research tasks linked in body / `related:` (list of relative-path links, if any).
- Wiki pages updated or deferred review items opened (with ids).
- Reminder: the file (and any cascaded supersedes-target edits) is left in the working tree — commit at the user's convenience.

## Non-goals

- **Do not research.** If the spec needs more investigation, stop and tell the user to run `/a4:task kind=research <topic>` first.
- **Do not review whether the shape is correct.** Whether the chosen shape is the right one is the user's own thinking; no machine critique pass exists.
- **Do not commit.** Leave files in the working tree.
- **Do not auto-populate `supersedes:`** or retire specs unprompted. The user sets `supersedes:` in Step 2; `→ deprecated` is a manual user call via `transition_status.py`.

(Frontmatter / body / lifecycle / writer-only field rules — including the `<decision-log>` append-only invariant and the `status:` writer-only rule — live in the spec authoring reference, not here.)
