# Pros & Cons

## What It Is
A straightforward evaluation technique that lists the advantages (pros) and disadvantages (cons) of a specific option or decision. Simple but effective for making the trade-offs explicit and visible.

## When to Use
- Facing a binary decision (do it or don't, option A or option B)
- Need to make implicit trade-offs explicit
- Quick evaluation is needed — no time for complex frameworks
- Comparing 2-3 alternatives side by side

## When NOT to Use
- Divergent phase — generating ideas, not evaluating them
- Many options to compare (use Impact-Effort Matrix or Priority Voting instead)
- Decision requires weighted criteria (not all pros/cons are equally important)

## Process Steps
1. **State the decision clearly** — What exactly are we deciding? Frame it as a specific choice.
2. **List all pros** — What are the benefits, advantages, and positive outcomes? Be specific and concrete.
3. **List all cons** — What are the drawbacks, risks, costs, and negative outcomes? Be equally thorough.
4. **Weight the items** (optional) — Not all pros and cons are equal. Mark the most important ones (e.g., with a star or high/medium/low weight).
5. **Look for dealbreakers** — Is there a single con that overrides everything else? Is there a must-have pro that makes the decision obvious?
6. **Assess the balance** — Step back and look at the overall picture. Does one side clearly outweigh the other?
7. **Make the call** — Based on the analysis, state a recommendation with reasoning.

## Facilitator Prompts
- "Let's start with the positives. What are all the reasons this is a good idea?"
- "Now the other side. What are the risks, costs, or downsides?"
- "Are all of these equally important? Which pros/cons carry the most weight?"
- "Is there a dealbreaker on either side — something that would override everything else?"
- "Looking at this list, which side feels stronger? Why?"
- "If we had to decide right now based on this list, which way would you lean?"
- "For Option B, let's do the same exercise. How do the pros/cons compare?"

## Example
**Decision**: Should we migrate from monolith to microservices?

| Pros | Cons |
|------|------|
| Independent deployment per service | Significant upfront migration effort |
| Teams can choose their own tech stack | Distributed system complexity (networking, debugging) |
| Better fault isolation | Need to build/learn orchestration and monitoring |
| Easier to scale individual services | Data consistency across services is harder |
| Aligns with team structure (Conway's Law) | More infrastructure overhead |
| ⭐ Unblocks parallel team development | ⭐ 6-month estimated migration timeline |

**Assessment**: Pros are strong for long-term velocity, but the 6-month timeline is a significant cost. Recommendation: Start with a "strangler fig" pattern — extract one service at a time rather than a big-bang migration.
