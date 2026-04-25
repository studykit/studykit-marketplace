---
title: "/a4:usecase vs /a4:auto-usecase selection criteria"
status: draft
decision: "TBD — define when compass and the user should pick `/a4:usecase` (interactive Socratic interview) over `/a4:auto-usecase` (autonomous generation), and document the criterion in `compass/SKILL.md` and the two skills' descriptions."
supersedes: []
related: []
tags: [usecase, auto-usecase, compass, selection]
created: 2026-04-25
updated: 2026-04-25
---

# /a4:usecase vs /a4:auto-usecase selection criteria

## Context

a4 has two entry skills for creating UCs and the foundation wiki pages (`context.md`, `actors.md`, `domain.md`, `nfr.md`):

- **`/a4:usecase`** — Socratic interviewer that asks one question at a time and writes UC files as the conversation produces them. New workspaces start by writing `context.md` and growing the workspace through dialogue.
- **`/a4:auto-usecase`** — autonomous generator that runs subagents (composer, reviewer, reviser, explorer) without user interaction. Accepts an idea, brainstorm text, **or source-code path** as the argument; produces a complete draft UC set in one batch.

Tier B 7's compass refresh (see [[plugins/a4/spec/2026-04-25-compass-routing-refresh]]) made the choice clearer in the brownfield branch — code-bearing projects route to `/a4:auto-usecase` because of its Step 2b code-analysis support. But for greenfield workspaces, compass Step 2.1 catalog still presents both skills without a selection rule. The user picks based on instinct.

The pipeline-restructure thread's inventory pass (see [[plugins/a4/.handoff/pipeline-restructure/2026-04-25_1804_compass-and-run-fallback-shipped]]) flagged this as a missing criterion. The two skills' descriptions distinguish "interactive interview" vs "no interview / autonomous", but neither describes when each is preferable. A user choosing without guidance may pick the autonomous path for speed, lose the Socratic challenge mode, and end up with a draft that misses the angles dialog would have surfaced — or pick the interactive path for thoroughness on a domain where their understanding is already concrete and waste cycles answering questions they could have answered in one batch.

## Open Questions

- **What axis distinguishes the two?** Candidates:
  - **Idea concreteness.** Vague / exploratory → `/a4:usecase`; concrete / well-formed → `/a4:auto-usecase`. The dialog adds value where the user is still discovering what to build.
  - **User availability.** Sync collaboration available → `/a4:usecase`; user wants to step away → `/a4:auto-usecase`. Auto-generation is the "kick it off, review later" path.
  - **Existing source material.** Has a brainstorm doc / requirements doc / code → `/a4:auto-usecase`; only has a verbal idea → `/a4:usecase`.
  - **Domain familiarity.** Familiar domain → `/a4:auto-usecase` (autonomous defaults are trustworthy); unfamiliar / novel domain → `/a4:usecase` (challenge modes earn their keep).
- **Catalog presentation.** Should compass Step 2.1 add a "When to pick" sentence per skill, or a chooser question ("Do you have written material to extract from? Y → auto-usecase; N → usecase")?
- **Migration path.** If the user picks one and changes their mind, can they migrate? `/a4:auto-usecase`'s expansion mode handles partial-set extension, so `usecase → auto-usecase` is supported. The reverse — running `/a4:usecase iterate` after `/a4:auto-usecase` — is also supported because `/a4:usecase` is the interactive iteration path. Confirm that this two-way path is intentional and documented.
