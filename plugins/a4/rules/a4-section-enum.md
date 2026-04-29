---
name: a4-section-enum
description: Per-type section enum for a4 workspace files. Auto-loaded when reading anything under `a4/`.
paths: ["a4/**/*.md"]
---

# a4 — per-type section enum

Files under `<project-root>/a4/` declare `type:` in YAML frontmatter, and that value drives which body sections are expected. Each body is a sequence of column-0 H2 markdown headings in Title Case (e.g., `## Context`, `## Specification`, `## Change Logs`) with markdown content between successive headings. See [`../references/body-conventions.md`](../references/body-conventions.md) for the full rule set, the kebab-case → Title Case mapping, blank-line discipline, and `## Change Logs` / `## Log` audit-trail conventions.

**Folder ↔ type:**

- `usecase/`, `task/`, `spec/`, `review/`, `idea/`, `archive/` — folder name = `type:`.
- Wiki pages (`actors.md`, `architecture.md`, `bootstrap.md`, `context.md`, `domain.md`, `nfr.md`, `roadmap.md`) — basename = `type:` (e.g., `actors.md` → `type: actors`).
- `spark/<…>.brainstorm.md` → `type: brainstorm`.
- `task/<kind>/` — kind subfolder is part of the path (`task/feature/`, `task/spike/`, `task/bug/`, `task/research/`); `type:` is `task` regardless of kind.

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
- task (feature/spike/bug)  R{## Acceptance Criteria, ## Description, ## Files, ## Unit Test Strategy} O{## Change Logs, ## Interface Contracts, ## Log, ## Why Discarded}
- task (research)           R{## Context} O{## Change Logs, ## Findings, ## Log, ## Options, ## Why Discarded}
- usecase       R{## Expected Outcome, ## Flow, ## Goal, ## Situation} O{## Change Logs, ## Dependencies, ## Error Handling, ## Log, ## Validation}

## Maintenance

Body shape is documented in two co-equal places that must be edited together:

- `../references/<type>-authoring.md` — the binding contract for authors.
- `../scripts/body_schemas/<type>.xsd` — reference XSD that mirrors the same shape for human readers; pure human reference, not consumed at runtime. Element names in the XSD use lowercase kebab-case (an XML grammar artifact); apply the kebab → Title Case mapping in [`../references/body-conventions.md`](../references/body-conventions.md) when authoring the body.

When you change one, update the other in the same change. The bullet list above is hand-maintained — keep it in sync with both sources.
