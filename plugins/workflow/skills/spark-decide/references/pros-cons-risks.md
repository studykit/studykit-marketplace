# Pros-Cons-Risks Analysis

## What It Is
A simple three-column evaluation for each option. List the advantages (Pros), disadvantages (Cons), and uncertainties (Risks) for each candidate. Includes a "killer flaw" check — any single con that disqualifies an option regardless of its pros.

## When to Use
- Quick decisions with 2-3 options
- Informal context — don't need a formal matrix
- Early-stage evaluation before investing in deeper analysis
- The decision is relatively reversible

## When NOT to Use
- Many options (5+) — the lists become unwieldy
- Need to weigh criteria against each other (use Weighted Scoring)
- High-stakes, irreversible decision that needs rigorous justification

## Process Steps

1. **List options** — Keep to 2-3 candidates. If more, pre-filter first.
2. **For each option, brainstorm Pros** — What's good about it? What problems does it solve? What makes it attractive?
3. **For each option, brainstorm Cons** — What's bad? What problems does it create? What's missing?
4. **For each option, identify Risks** — What's uncertain? What could go wrong? What assumptions are we making?
5. **Killer flaw check** — For each option, ask: "Is there any single con so severe that no number of pros can overcome it?" If yes, eliminate the option.
6. **Compare** — Look at the remaining options side by side. Which has the strongest pros in the areas that matter most? Which has the most manageable cons?
7. **Decide** — Choose the option with the best pro-to-con ratio in the dimensions you care about.

## Facilitator Prompts

- "What's the strongest argument FOR this option?"
- "What's the biggest concern or downside?"
- "What could go wrong that we haven't considered?"
- "Is there anything about this option that would make it a non-starter, no matter what?"
- "Looking at both options side by side, which set of trade-offs can you live with?"

## Example

**Decision:** Build custom auth vs. use Auth0

**Option A: Custom Auth**
| Pros | Cons | Risks |
|------|------|-------|
| Full control | Significant dev time (2-3 weeks) | Security vulnerabilities if not done right |
| No vendor lock-in | Must maintain ourselves | Compliance requirements may change |
| No per-user pricing | Need to build MFA, SSO separately | |

**Option B: Auth0**
| Pros | Cons | Risks |
|------|------|-------|
| Production-ready in 1 day | Monthly cost scales with users | Vendor could change pricing |
| MFA, SSO included | Less control over flow | Outage dependency |
| Security handled by experts | Vendor lock-in | |

Killer flaw check: Custom auth has a security risk that could be severe for a healthcare app → eliminated.

Decision: Auth0 — the security risk of custom auth is a killer flaw given the compliance requirements.
