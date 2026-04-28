---
name: a4-section-enum
description: Per-type section enum for a4 workspace files. Auto-loaded when reading anything under `a4/`.
paths: ["a4/**/*.md"]
---

# a4 — per-type section enum

Files under `<project-root>/a4/` declare `type:` in YAML frontmatter, and
that value matches the body's root tag. Each body is a sequence of
column-0 `<section>...</section>` blocks (lowercase kebab-case) with
markdown content between the open and close lines.

**Folder ↔ type:**

- `usecase/`, `task/`, `spec/`, `review/`, `idea/`, `archive/` — folder
  name = `type:`.
- Wiki pages (`actors.md`, `architecture.md`, `bootstrap.md`,
  `context.md`, `domain.md`, `nfr.md`, `roadmap.md`) — basename =
  `type:` (e.g., `actors.md` → `type: actors`).
- `spark/<…>.brainstorm.md` → `type: brainstorm`.

**Per-type sections** (R = required, O = optional; unknown kebab-case
tags are also accepted via the schema's openContent rule):

<!-- BEGIN section-enum -->
- actors        R{roster} O{change-logs}
- architecture  R{components, overview, technology-stack, test-strategy} O{change-logs, component-diagram, external-dependencies}
- bootstrap     R{environment, launch, verify} O{change-logs}
- brainstorm    R{ideas} O{change-logs, notes}
- context       R{original-idea, problem-framing} O{change-logs, screens}
- domain        R{concepts} O{change-logs, relationships, state-transitions}
- idea          R{} O{change-logs, log, notes, why-this-matters}
- nfr           R{requirements} O{change-logs}
- research      R{context} O{change-logs, cited-by, findings, options}
- review        R{description} O{change-logs, log}
- roadmap       R{plan} O{change-logs}
- spec          R{context, specification} O{change-logs, consequences, decision-log, examples, log, open-questions, rejected-alternatives, research}
- task          R{acceptance-criteria, description, files, unit-test-strategy} O{change-logs, interface-contracts, log, why-discarded}
- usecase       R{expected-outcome, flow, goal, situation} O{change-logs, dependencies, error-handling, log, validation}
<!-- END section-enum -->

## Read one section instead of the whole file

When you only need one section of an a4 file, prefer
`extract_section.py` over reading the entire markdown:

```bash
uv run "../scripts/extract_section.py" <file> <tag>
uv run "../scripts/extract_section.py" <file> --list
```

The script reuses the same fence-aware section scanner as
`validate_body.py`, so outline-shaped tags inside fenced code blocks
inside a section are handled correctly.

## Maintenance

The bullet block between the `BEGIN section-enum` / `END section-enum`
markers is generated from `body_schemas/*.xsd` by
`scripts/generate_section_enum.py`. Do not hand-edit it; the repo's
pre-commit hook re-checks for drift whenever any XSD or this rule file
is staged. To sync after changing an XSD:

```bash
uv run ../scripts/generate_section_enum.py --write
```
