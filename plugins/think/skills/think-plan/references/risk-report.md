# Risk Assessment Report Persistence

After each `risk-assessor` invocation, the subagent writes the report directly to the file path provided by the invoking skill.

## File Path

`A4/<topic-slug>.impl-plan.risk-<revision>.md`

Where `<revision>` is the current plan revision number at the time the subagent is launched.

## Frontmatter

```markdown
---
type: risk-report
source: <topic-slug>.impl-plan.md
revision: <current revision number>
assessed: <YYYY-MM-DD HH:mm>
---
```

## Content

Write the assessor's full report as-is below the frontmatter — do not summarize or truncate.

The report should cover:

- **Per-unit risks** — risks specific to individual implementation units
- **Cross-cutting risks** — risks that span multiple units or affect the plan as a whole
  - Complex integrations — units that depend on external services
  - Schema migrations — units that modify existing database schemas
  - Performance-sensitive areas — units with NFR constraints
  - Unknowns — areas where the spec has Open Items
- **Risk matrix** — each risk with Impact, Likelihood, suggested Mitigation, and Affected Units
- **Recommended mitigations** — concrete strategies, not generic advice

## Purpose

- Preserves the risk analysis trail for auditing across iterations
- Enables resume after interruption: read existing reports to understand what was already assessed
- Provides context to fresh subagent invocations via file path passing
- Separates detailed analysis (report) from summary (impl-plan Risk Assessment section)
