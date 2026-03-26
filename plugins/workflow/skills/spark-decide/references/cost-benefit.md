# Cost-Benefit Analysis

## What It Is
A structured evaluation that enumerates all costs and benefits for each option, then computes a rough ratio to determine which option delivers the most value relative to its cost. Costs include effort, money, time, and opportunity cost. Benefits include direct value, risk reduction, learning, and future optionality.

## When to Use
- Resource-constrained decisions (limited time, budget, or team capacity)
- ROI matters — need to justify the investment
- Comparing options with very different cost profiles (e.g., build vs. buy)
- Decisions where hidden costs are likely lurking

## When NOT to Use
- Costs and benefits are roughly equal across options (use a different differentiator)
- The decision is not resource-driven (use SWOT or Weighted Scoring)
- Benefits are too intangible to estimate even roughly

## Process Steps

1. **For each option, enumerate Costs:**
   - **Direct costs**: Money, licenses, infrastructure, hosting
   - **Effort costs**: Development time (hours/days), setup time, learning curve
   - **Ongoing costs**: Maintenance, upgrades, monitoring, vendor fees
   - **Opportunity cost**: What else could you do with those resources?
   - **Switching cost**: If this doesn't work, how expensive is it to change?
2. **For each option, enumerate Benefits:**
   - **Direct value**: What does it deliver? Time saved, problems solved, capability gained
   - **Risk reduction**: What risks does it eliminate or reduce?
   - **Learning value**: What do you learn by choosing this that helps future decisions?
   - **Optionality**: Does this choice open or close future doors?
3. **Estimate rough magnitudes** — Don't aim for precision. Use T-shirt sizes (S/M/L/XL) or relative scales. The goal is to surface obvious imbalances.
4. **Compute the ratio** — Which option has the best benefit-to-cost ratio? Consider both total value and time-to-value.
5. **Surface hidden costs** — Explicitly ask: "What costs might we be forgetting?" Common hidden costs: integration effort, training, migration, technical debt created.

## Facilitator Prompts

- "How much time/money/effort does this option require upfront?"
- "What's the ongoing cost after the initial investment?"
- "If this doesn't work out, how expensive is it to switch?"
- "What's the single biggest benefit of this option?"
- "What would you be giving up by choosing this option instead of doing something else?"
- "Are there any hidden costs we haven't discussed?"
- "How quickly does this option start delivering value?"

## Example

**Decision:** Build internal dashboard vs. buy Metabase

**Option A: Build Custom**
| Costs | Magnitude |
|-------|-----------|
| Development | XL (3-4 weeks, 1 developer) |
| Maintenance | L (ongoing feature requests, bug fixes) |
| Opportunity cost | L (developer not working on core product) |

| Benefits | Magnitude |
|----------|-----------|
| Exact fit to needs | L |
| No vendor dependency | M |
| Team learns data viz | S |

**Option B: Metabase (open source)**
| Costs | Magnitude |
|-------|-----------|
| Setup & config | S (1-2 days) |
| Learning curve | S (team needs to learn Metabase) |
| Customization limits | M (may not fit all needs) |

| Benefits | Magnitude |
|----------|-----------|
| Immediate value | XL (working in days, not weeks) |
| Battle-tested features | L |
| Community support | M |
| Developer stays on core product | L |

Ratio: Metabase delivers XL benefit for S cost. Custom delivers L benefit for XL cost. Clear winner: Metabase.
