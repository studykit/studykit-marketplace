# SWOT Analysis (per Option)

## What It Is
A strategic evaluation framework that examines each option across four dimensions: **S**trengths (internal positive), **W**eaknesses (internal negative), **O**pportunities (external positive), **T**hreats (external negative). Unlike Pros-Cons, SWOT explicitly separates internal factors (what you control) from external factors (market, ecosystem, competition, timing).

## When to Use
- Strategic decisions where external factors matter (market trends, ecosystem health, community momentum)
- Technology choices that depend on industry direction
- Build-vs-buy decisions where vendor viability matters
- Decisions that involve timing (e.g., "should we adopt this now or wait?")

## When NOT to Use
- Purely internal, technical decisions (use Weighted Scoring or Pros-Cons)
- Quick decisions where external analysis is overkill
- Decisions where all options face the same external factors

## Process Steps

1. **Identify options** — 2-4 candidates.
2. **For each option, fill the SWOT grid:**
   - **Strengths**: What's inherently good about this option? What advantages does it have? (Internal, positive)
   - **Weaknesses**: What's inherently limited? What gaps exist? (Internal, negative)
   - **Opportunities**: What external trends, market shifts, or ecosystem developments favor this option? (External, positive)
   - **Threats**: What external risks could undermine this option? Vendor risk, market shifts, competition? (External, negative)
3. **Cross-analyze** — For each option: Can strengths exploit opportunities? Can strengths counter threats? Do weaknesses amplify threats?
4. **Compare** — Which option has the best strength-opportunity alignment and the least weakness-threat exposure?
5. **Time dimension** — Ask: "How does this SWOT change in 6 months? 2 years?" Some threats are temporary; some opportunities are closing.

## Facilitator Prompts

- "What does this option do well that others don't?" (Strengths)
- "Where is this option inherently limited?" (Weaknesses)
- "What trends in the market or ecosystem make this option more attractive?" (Opportunities)
- "What external factors could make this option a bad choice in the future?" (Threats)
- "Can this option's strengths take advantage of the opportunities you identified?"
- "How does this picture change in a year from now?"

## Example

**Decision:** Choose a frontend framework

**React**
| Strengths | Weaknesses |
|-----------|------------|
| Massive ecosystem, proven at scale | Boilerplate-heavy, choice fatigue |
| Easy to hire developers | No built-in routing/state |

| Opportunities | Threats |
|---------------|---------|
| Server Components maturing | Ecosystem fragmentation increasing |
| React Native for mobile reuse | Meta's priorities may shift |

**Svelte**
| Strengths | Weaknesses |
|-----------|------------|
| Minimal boilerplate, fast perf | Smaller ecosystem, fewer libraries |
| Built-in state, transitions | Harder to hire experienced devs |

| Opportunities | Threats |
|---------------|---------|
| Growing rapidly, SvelteKit stable | Still niche — ecosystem could stall |
| Performance trend favors compiled | Key maintainer risk (small team) |

Cross-analysis: React's strength (ecosystem) counters the hiring threat. Svelte's weakness (small ecosystem) is amplified by the maintainer threat.
