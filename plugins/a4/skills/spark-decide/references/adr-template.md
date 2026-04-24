# ADR Output Format

```markdown
---
type: decide
topic: "<topic>"
date: <YYYY-MM-DD>
status: final
framework: "<evaluation framework used>"
decision: "<one-line summary of the decision>"
tags: []
---
# Decision Record: <topic>
> Source: [<source-file-name>](./<source-file-name>)

## Context
<Why this decision is needed. Background, constraints, triggers.>

## Success Criteria
<The dimensions being optimized for, ranked by importance.>

## Options Considered

### Option 1: <name>
<Description. Key characteristics.>

### Option 2: <name>
<Description. Key characteristics.>

...

## Research Findings

### Option 1: <name>
<Objective findings. Sources cited.>

### Option 2: <name>
<Objective findings. Sources cited.>

...

## Evaluation

### Criteria & Weights
| Criterion | Weight | Description |
|-----------|--------|-------------|
| ... | ... | ... |

### Comparison
| Criterion | Option 1 | Option 2 | ... |
|-----------|----------|----------|-----|
| ... | ... | ... | ... |

### Analysis
<Trade-off discussion. What each option excels at and where it falls short.>

## Decision
**Chosen:** <option name>

**Rationale:** <Why this option, connected to the evaluation results.>

**Trade-offs accepted:** <What you're giving up by choosing this.>

**Reversibility:** <Easy / Moderate / Difficult. What switching would cost.>

**Risks & mitigations:**
- <Risk>: <Mitigation>

## Rejected Alternatives
| Option | Reason |
|--------|--------|
| <name> | <specific reason tied to evaluation> |

## Next Steps
- [ ] <concrete action item>
- [ ] <concrete action item>

## Discussion Log
<details>
<summary>Full conversation</summary>

### Round 1
**Q:** <question>
**A:** <answer>

...
</details>
```

**Required sections**: Context, Success Criteria, Options Considered, Evaluation, Decision, Rejected Alternatives, Next Steps.
**Conditionally required:**
- **Research Findings** — if research was conducted
- **Discussion Log** — always included in final version
