---
name: a4-section-enum
description: Per-type section enum for a4 workspace files. Auto-loaded when reading anything under `a4/`.
paths: ["a4/**/*.md"]
---

# a4 — per-type section enum

Files under `<project-root>/a4/` declare `type:` in YAML frontmatter, and that value drives which body sections are expected. Each body is a sequence of column-0 H2 markdown headings in Title Case (e.g., `## Context`, `## Specification`, `## Change Logs`) with markdown content between successive headings. See [`../authoring/body-conventions.md`](../authoring/body-conventions.md) for the full rule set, the kebab-case → Title Case mapping, blank-line discipline, and `## Change Logs` / `## Log` audit-trail conventions.

**Folder ↔ type:**

- `usecase/`, `task/`, `bug/`, `spike/`, `research/`, `spec/`, `review/`, `idea/`, `brainstorm/`, `archive/` — folder name = `type:`.
- Wiki pages (`actors.md`, `architecture.md`, `bootstrap.md`, `context.md`, `domain.md`, `nfr.md`, `roadmap.md`) — basename = `type:` (e.g., `actors.md` → `type: actors`).

After a4 v12.0.0 the four task issue families (`task` / `bug` / `spike` / `research`) are flat sibling folders under `a4/` — there is no `kind:` field on tasks; the folder + `type:` together encode the kind. The `task` family is the default (regular implementation work), equivalent to Jira's "Task" issue type alongside Bug / Story.

**Per-type sections** (R = required, O = optional; unknown Title Case headings are tolerated):

- actors        R{## Roster} O{## Change Logs}
- architecture  R{## Components, ## Overview, ## Technology Stack, ## Test Strategy} O{## Change Logs, ## Component Diagram, ## External Dependencies}
- bootstrap     R{## Environment, ## Launch, ## Verify} O{## Change Logs}
- brainstorm    R{## Ideas} O{## Change Logs, ## Notes}
- context       R{## Original Idea, ## Problem Framing} O{## Change Logs, ## Screens}
- domain        R{## Concepts} O{## Change Logs, ## Relationships, ## State Transitions}
- idea          R{} O{## Change Logs, ## Log, ## Notes, ## Why This Matters}
- nfr           R{## Requirements} O{## Change Logs}
- review        R{## Description} O{## Change Logs, ## Log}
- roadmap       R{## Plan} O{## Change Logs}
- spec          R{## Context, ## Specification} O{## Change Logs, ## Consequences, ## Decision Log, ## Examples, ## Log, ## Open Questions, ## Rejected Alternatives}
- task, bug, spike  R{## Acceptance Criteria, ## Description, ## Files, ## Unit Test Strategy} O{## Change Logs, ## Interface Contracts, ## Log, ## Why Discarded}
- research      R{## Context} O{## Change Logs, ## Findings, ## Log, ## Options, ## Why Discarded}
- usecase       R{## Expected Outcome, ## Flow, ## Goal, ## Situation} O{## Change Logs, ## Dependencies, ## Error Handling, ## Log, ## Validation}

## Maintenance

Body shape is documented in `../authoring/<type>-authoring.md` — the binding contract for authors. The bullet list above is hand-maintained — keep it in sync with the per-type authoring files.
