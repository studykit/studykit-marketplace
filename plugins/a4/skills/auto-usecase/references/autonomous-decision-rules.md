# Autonomous Decision Rules

Apply these consistently during composition and revision. No user interaction is permitted — `auto-usecase` is an autonomous skill.

## Rules

1. **Ambiguous topic** → pick the most specific interpretation. Record the interpretation in `context.md`'s Problem Framing and emit a `kind: question` review item so a human can confirm later.
2. **Unclear actor role** → default to `viewer`. Upgrade to `editor` when actions imply edit capability.
3. **Splitting boundary** → prefer splitting. Smaller UCs are better.
4. **Vague situation** → construct a plausible concrete one. Emit a `kind: question` review item.
5. **Unclear relationship** → prefer `depends_on` over `related`. Note the reasoning in the UC's `## Source` section.
6. **New UC overlaps existing** → exclude. Record in the exclusion log (Step 3a composer output) and do not emit a file.
7. **New UC outside context** → exclude. Record in the exclusion log.
8. **Practical value borderline** → prefer exclusion over inclusion.
9. **Never set `status: final`** on any wiki or UC. Autonomous output is always `status: draft`. Promotion to `ready` / `implementing` / `shipped` is always user-driven.

## Why these rules exist

The skill runs without a person to disambiguate against. Without consistent defaults, repeated runs against the same input would produce different UC sets — defeating the purpose of a deterministic batch generator. The rules favor:

- **Specificity** over breadth (rule 1, 3) — a too-narrow UC can be widened by a reviewer; a too-broad UC obscures real coverage gaps.
- **Conservative inclusion** (rules 6–8) — autonomous overreach pollutes the workspace; the explorer pass exists to add UCs deliberately.
- **User control of the lifecycle** (rule 9) — automation produces drafts; humans promote.

Subagents (composer, reviser, reviewer, explorer) all apply these rules. Decisions made under rules 1, 4, and 5 must be recorded in the UC's `## Source` section; see [`source-attribution.md`](source-attribution.md).
