# Pugh Matrix (Concept Selection)

## What It Is
A relative comparison technique that evaluates options against a baseline (usually the current state or status quo). Each option is scored as better (+), same (S), or worse (-) than the baseline per criterion. Simple counting reveals whether an option is a net improvement.

## When to Use
- You have a clear baseline (current tool, existing process, status quo)
- The core question is "should we change, and to what?"
- Criteria are hard to weight precisely
- Want a quick, visual comparison

## When NOT to Use
- No clear baseline exists (starting from scratch)
- Need precise numerical comparison (use Weighted Scoring)
- Options are fundamentally different in kind (apples vs oranges)

## Process Steps

1. **Define the baseline** — Usually the current state or the most familiar option. Label it "Baseline."
2. **List criteria** — Same as Weighted Scoring: 4-8 dimensions that matter.
3. **Score each alternative relative to baseline** — For each criterion:
   - `+` = Better than baseline
   - `S` = Same as baseline
   - `-` = Worse than baseline
4. **Count** — For each option: total `+`, total `-`, total `S`. Net score = `+` count minus `-` count.
5. **Analyze** — A positive net score suggests improvement over status quo. Look at which criteria got `-` — are any of them dealbreakers?
6. **Iterate** — If no clear winner, try combining the best aspects of top options into a hybrid, then re-score.

## Facilitator Prompts

- "What's the current state we're comparing against?"
- "Compared to what you have now, is [option] better, same, or worse at [criterion]?"
- "This option has 3 plusses but 2 minuses. Are any of those minuses dealbreakers?"
- "Could we combine the best parts of [A] and [B] into a hybrid option?"

## Example

**Decision:** Replace current CI/CD pipeline (Baseline: Jenkins)

| Criterion | GitHub Actions | GitLab CI | CircleCI |
|-----------|---------------|-----------|----------|
| Setup ease | + | + | + |
| Config as code | S | + | S |
| Plugin ecosystem | - | S | - |
| Cost | + | S | - |
| Debug experience | + | + | S |
| **+ count** | **3** | **3** | **1** |
| **- count** | **1** | **0** | **2** |
| **Net** | **+2** | **+3** | **-1** |

Winner: GitLab CI (+3 net), with no negatives against baseline.
