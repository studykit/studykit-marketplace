# Weighted Scoring Matrix

## What It Is
A structured evaluation technique that scores each option against weighted criteria. Each criterion gets a weight (reflecting importance) and each option gets a score per criterion. The weighted sum determines the ranking.

## When to Use
- Multiple options (3+) with multiple evaluation dimensions
- Criteria importance varies — some matter much more than others
- Need to justify the decision with numbers to stakeholders or your future self
- Want to reduce emotional bias in decision-making

## When NOT to Use
- Only 2 options — Pros-Cons-Risks or Pugh Matrix is faster
- Criteria are not meaningfully quantifiable (e.g., "feels right")
- The decision is trivial or easily reversible
- You lack enough information to score options (research first)

## Process Steps

1. **List criteria** — Ask: "What dimensions matter for this decision?" Aim for 4-8 criteria. Too few misses nuance; too many dilutes focus.
2. **Assign weights** — Weights must sum to 100%. Ask: "If you could only optimize for one thing, what would it be?" Start there and distribute the rest. No criterion should get less than 5% (if it's that unimportant, remove it).
3. **Score each option** — Use a 1-5 scale per criterion per option:
   - 1 = Poor / does not meet
   - 2 = Below average
   - 3 = Adequate / meets minimum
   - 4 = Good / exceeds expectations
   - 5 = Excellent / best possible
4. **Compute weighted scores** — For each option: sum of (weight × score) across all criteria.
5. **Analyze** — Look beyond the total: Which criteria drove the winner? Are there any criteria where the winner scored poorly? Is a 4.1 vs 3.9 difference meaningful or noise?
6. **Sensitivity check** — Change the top weight by ±10%. Does the winner change? If yes, the decision is fragile and needs more thought.

## Facilitator Prompts

- "What are the 4-5 things that matter most for this decision?"
- "If you could only optimize for one of these, which would it be?"
- "On a scale of 1-5, how well does [option] handle [criterion]? What's your reasoning?"
- "The scores are close between [A] and [B]. What would tip the balance?"
- "If we change [top criterion]'s weight by 10%, does the answer change?"

## Example

**Decision:** Choose a task management tool

| Criterion | Weight | Notion | Linear | GitHub Projects |
|-----------|--------|--------|--------|-----------------|
| Search & filtering | 30% | 5 | 4 | 2 |
| Setup simplicity | 25% | 3 | 4 | 5 |
| API / automation | 20% | 4 | 5 | 4 |
| Relationship tracking | 15% | 5 | 3 | 2 |
| Cost (free tier) | 10% | 3 | 2 | 5 |
| **Weighted Total** | | **4.10** | **3.75** | **3.25** |

Winner: Notion (4.10), driven by search/filtering and relationship tracking.
