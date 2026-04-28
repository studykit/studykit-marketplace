---
name: a4-section-enum
description: Per-type section enum for a4 workspace files. Auto-loaded when reading anything under `a4/`.
paths: ["a4/**/*.md"]
---

# a4 — per-type section enum

Files under `<project-root>/a4/` declare `type:` in YAML frontmatter, and that value matches the body's root tag. Each body is a sequence of column-0 `<section>...</section>` blocks (lowercase kebab-case) with markdown content between the open and close lines.

**Folder ↔ type:**

- `usecase/`, `task/`, `spec/`, `review/`, `idea/`, `archive/` — folder name = `type:`.
- Wiki pages (`actors.md`, `architecture.md`, `bootstrap.md`, `context.md`, `domain.md`, `nfr.md`, `roadmap.md`) — basename = `type:` (e.g., `actors.md` → `type: actors`).
- `spark/<…>.brainstorm.md` → `type: brainstorm`.
- `task/<kind>/` — kind subfolder is part of the path (`task/feature/`, `task/spike/`, `task/bug/`, `task/research/`); `type:` is `task` regardless of kind.

**Per-type sections** (R = required, O = optional; unknown kebab-case tags are tolerated):

- actors        R{roster} O{change-logs}
- architecture  R{components, overview, technology-stack, test-strategy} O{change-logs, component-diagram, external-dependencies}
- bootstrap     R{environment, launch, verify} O{change-logs}
- brainstorm    R{ideas} O{change-logs, notes}
- context       R{original-idea, problem-framing} O{change-logs, screens}
- domain        R{concepts} O{change-logs, relationships, state-transitions}
- idea          R{} O{change-logs, log, notes, why-this-matters}
- nfr           R{requirements} O{change-logs}
- review        R{description} O{change-logs, log}
- roadmap       R{plan} O{change-logs}
- spec          R{context, specification} O{change-logs, consequences, decision-log, examples, log, open-questions, rejected-alternatives}
- task (feature/spike/bug)  R{acceptance-criteria, description, files, unit-test-strategy} O{change-logs, interface-contracts, log, why-discarded}
- task (research)           R{context} O{change-logs, findings, log, options, why-discarded}
- usecase       R{expected-outcome, flow, goal, situation} O{change-logs, dependencies, error-handling, log, validation}

## Maintenance

Body shape is documented in two co-equal places that must be edited together:

- `../references/<type>-authoring.md` — the binding contract for authors.
- `../scripts/body_schemas/<type>.xsd` — reference XSD that mirrors the same shape for human readers; not consumed by any runtime validator.

When you change one, update the other in the same change. The bullet list above is hand-maintained — keep it in sync with both sources.
