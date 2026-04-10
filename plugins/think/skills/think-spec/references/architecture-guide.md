# Architecture Guide

Detailed procedures for Phase 3: designing system architecture from requirements and domain model.

## Topic 3.0: External Dependencies

Before designing internal components, identify external systems the software depends on:

1. **Scan FRs for external interactions** — any FR that references sending email, payment, authentication via third-party, file storage, external data sources, etc.
2. **Present the list** to the user:

   > I've identified these external dependencies from the FRs:
   >
   > | External System | Used By | Purpose |
   > |----------------|---------|---------|
   > | OAuth Provider | FR-1, FR-2 | User authentication |
   > | Email Service | FR-5 | Notification delivery |
   >
   > Are there other external services this system will use?

3. **For each confirmed dependency**, clarify:
   - What does the system send/receive?
   - Are there constraints? (rate limits, pricing tiers, specific provider chosen or open)
   - What happens if the external system is unavailable? (fallback behavior)
4. **Record in the output file** — External Dependencies section under Architecture.

## Topic 3.1: Component Identification

- Propose an initial set of components from the input materials
- Present the component list with responsibility descriptions
- Through interview, confirm: component name, responsibility, whether it has its own data store
- Present as PlantUML component diagram

## Topic 3.2: Per-Component Deep Dive

For each confirmed component:

- **DB schema** (if the component has its own data store):
  - Identify entities, attributes, and relationships
  - Present as PlantUML IE diagram
  - Not all components need a DB schema — ask before diving in

- **Information flow** (per use case):
  - For each use case involving this component, map the information flow between components
  - Present as PlantUML sequence diagram — one per use case
  - First iteration: "A sends user information to B" level is fine
  - Subsequent iterations: progressively refine to **interface contract** level — communication method (REST, event, function call), operation name, request/response schema
  - The goal by finalization: a coding agent can implement the interface without guessing

- **Interface contracts** (per component boundary):
  - Define how components communicate: API style, operations, request/response schemas
  - This is not required in the first iteration — it emerges as the spec matures
  - Present as a contract table per component pair:

    > | Operation | Direction | Request | Response | Notes |
    > |-----------|-----------|---------|----------|-------|
    > | createSession | Client → SessionService | { userId, title } | { sessionId, status } | |
    > | onSessionExpired | SessionService → NotificationService | { sessionId, reason } | — | event |

## Technology Choices

When a technology choice arises:
- **Lightweight decisions** — discuss inline and record with brief rationale.
- **Heavy decisions** — ask the user: "This seems like a decision worth investigating more deeply. Would you like to use `/think:spark-decide` to evaluate options?"

## Technical Claim Verification

When writing or confirming any technical statement in the spec (API support, library capabilities, framework constraints, compatibility, etc.), verify it before recording. Keep this lightweight — don't verify obvious facts, focus on claims that would cause implementation failures if wrong.

### Procedure

1. **Check the codebase first** — if the claim is about the current project's tech stack, verify by reading the actual code, configs, or dependency files. If confirmed, no research subagent needed.
2. **Launch a research subagent** — if the claim requires external verification, spawn a background `Agent` with `run_in_background: true`. Prompt it with the specific claim and ask it to verify against official documentation, release notes, or changelogs using `WebSearch`/`WebFetch`.
3. **Continue the interview** — keep working within the current phase while waiting. **Do not transition to the next phase** until all pending research results have been received and reflected.
4. **When notified** — the subagent writes results to `A4/<topic-slug>.spec.research-<label>.md` per `${CLAUDE_SKILL_DIR}/references/research-report.md`. Update the research index (`A4/<topic-slug>.spec.research-index.md`).
5. **Reflect the result** — apply the verification outcome to the spec. Add an inline reference to the research report where the claim is recorded (e.g., `(ref: research-nextjs-server-actions.md)`).
6. **Flag uncertainty** — if official documentation is ambiguous or unavailable, tell the user: "I couldn't confirm this from official sources. Want to proceed as an assumption or investigate further?"

### Research Index

Maintain `A4/<topic-slug>.spec.research-index.md` as a lookup table:

```markdown
| # | File | Tags | Summary | Date |
|---|------|------|---------|------|
| 1 | research-nextjs-server-actions.md | Next.js, Server Actions, v14 | 공식 문서, 버전별 지원 범위, 제약사항 정리 | 2026-04-10 |
| 2 | research-postgres-jsonb-index.md | PostgreSQL, JSONB, GIN index | 성능 벤치마크, 쿼리 패턴별 인덱스 전략 | 2026-04-10 |
```

Use the index as the primary lookup — do not read research report files unless you need the full details. Before launching a new research subagent, check the index first; if the claim was already verified, read the existing report only if the summary is insufficient.
