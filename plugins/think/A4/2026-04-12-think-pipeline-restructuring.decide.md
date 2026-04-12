---
type: decide
pipeline: spark
topic: "Think Pipeline Restructuring"
date: 2026-04-12
status: final
framework: "analysis-driven"
decision: "Remove think-spec, split into think-usecase (expanded) + think-arch (new) + auto-scaffold (new)"
tags: [think-pipeline, architecture, testing, scaffold]
---
# Decision Record: Think Pipeline Restructuring

> Source: integration report findings from visual-claude project — 9/21 FRs BLOCKED due to missing test environment, 3 FRs FAIL due to code wiring gaps

## References

### Analyzed artifacts (visual-claude project)
- `visual-claude/A4/terminal-markdown-renderer.usecase.md` — UC output, compared with FR for redundancy analysis
- `visual-claude/A4/terminal-markdown-renderer.spec.md` — spec output (rev 12), analyzed for abstraction level mixing
- `visual-claude/A4/terminal-markdown-renderer.impl-plan.md` — impl plan (rev 11), IU-1/IU-14/IU-15/IU-16 scaffold analysis
- `visual-claude/A4/terminal-markdown-renderer.integration-report.md` — integration report showing 9 BLOCKED, 3 FAIL
- `visual-claude/A4/spark/2026-04-12-0010-vscode-extension-test-framework.decide.md` — post-hoc test strategy decision

### Think pipeline skills analyzed
- `plugins/think/skills/think-usecase/SKILL.md` + references
- `plugins/think/skills/think-spec/SKILL.md` + references (architecture-guide.md, requirements-guide.md, abstraction-guards.md, output-template.md, phase-review-guide.md, session-procedures.md, research-report.md, session-history.md, review-report.md, domain-model-guide.md)
- `plugins/think/skills/think-plan/SKILL.md` + references (planning-guide.md, output-template.md, session-procedures.md, revision-rules.md, risk-report.md)
- `plugins/think/skills/think-code/SKILL.md` + references (execution-procedure.md, test-and-commit.md, parallel-execution.md, session-resume.md)
- `plugins/think/skills/think-verify/SKILL.md` + references (waterfall-trace.md, integration-report.md)

### Think pipeline agents analyzed
- `plugins/think/agents/coder.md`
- `plugins/think/agents/spec-reviewer.md`
- `plugins/think/agents/plan-reviewer.md`
- `plugins/think/agents/risk-assessor.md`

## Context

The think pipeline (think-usecase → think-spec → think-plan → think-code → think-verify) was used to build Claude Studio, a VS Code extension. The integration report revealed structural gaps:

- **9 out of 21 FRs BLOCKED** — no working SDK-backed live session could be bootstrapped in the verification environment
- **3 FRs FAIL** — code wiring bugs (input box not rendered, export handler missing, persona UI not mounted)
- **WebdriverIO** dependencies installed but harness not operational
- **Unit tests 615/615 pass** — but integration/E2E verification impossible

Root cause analysis traced these failures back to structural gaps in the think-* skills themselves, not to any single skill's execution error.

## Problems Identified

### 1. No test environment setup in the pipeline

No think-* skill instructs "set up and verify the test environment." The entire pipeline assumes the test environment already exists. think-verify discovers the problem last, when all code is written and the cost of fixing is highest.

### 2. think-plan's Launch & Verify is aspirational, not validated

think-plan writes Launch & Verify as metadata ("verify tool: WebdriverIO") but never creates IUs to set it up. The planning-guide.md has a verify tool selection table, but the result is a declaration, not a working environment.

### 3. Scaffold was technically complete but not functional

IU-1 (scaffold) passed its acceptance criteria ("extension activates", "postMessage works", "23 tests pass") but the webview couldn't actually execute — no esbuild bundler, no DOM containers, no localResourceRoots. IU-14, IU-15, IU-16 were added later to fix what should have been part of the initial scaffold. The planning-guide.md already warns about this: "A scaffold that cannot be used is not a testable increment — it is dead code."

### 4. think-spec mixed abstraction levels

Analysis of the actual spec output (terminal-markdown-renderer.spec.md) revealed:
- **Requirements + Domain Model** (lines 60–693): technology-neutral, user-behavior level — well abstracted
- **Architecture** (lines 696+): component diagrams, TypeScript data schemas, postMessage protocols, sequence diagrams with message formats — implementation-level design

These two levels have fundamentally different abstraction and serve different purposes.

### 5. FR and UC separation provided no practical benefit

Comparing actual UC and FR outputs showed:
- FR additions that were **business rules** (validation, error handling, timeouts) → could be captured in UC
- FR additions that were **implementation details** (Screen/View, system prompt, SVG clickability) → should be in architecture
- FR additions that were **new feature discovery** (personas, platform capabilities) → could happen during UC discovery

The UC/FR separation is textbook but doesn't match how thinking actually flows. Managing two documents (`.usecase.md` and `.spec.md`) created overhead without practical benefit.

## Decisions

### 1. Remove think-spec — split responsibilities

think-spec is removed. Its responsibilities are redistributed:

| think-spec responsibility | Moves to |
|--------------------------|----------|
| FR precision (validation, error handling, business rules) | think-usecase |
| Platform capabilities (cross-UC analysis) | think-usecase |
| Domain Model extraction | think-usecase |
| Mock generation | think-usecase |
| Technology Stack | think-arch |
| External Dependencies | think-arch |
| Component design, DB Schema, Sequence Diagram, Interface Contract | think-arch |
| Technology Choices + Technical Claim Verification | think-arch |

**Rationale:**
- FR-level precision (error handling, validation) naturally emerges during UC discovery — separating it into a later phase is artificial
- Domain Model concepts emerge during UC precision work and serve as shared language for architecture and code
- Architecture is implementation-level design, fundamentally different from requirements discovery
- Technology Stack is decided in architecture, not in requirements

### 2. New skill: think-arch

Interactive skill for implementation-level design. Receives expanded UC output (`.usecase.md`) as input.

**Scope:**
- Domain Model serves as the starting vocabulary (read from usecase output)
- Technology Stack selection
- External Dependencies (identification + access patterns + fallback)
- Component design, DB Schema, Information Flow, Interface Contracts
- Technology Choices + Technical Claim Verification
- **Test Strategy** (new) — tier-by-tier test tool selection based on the technology stack

**Output:** `.arch.md`

**Rationale for Domain Model placement:** Domain Model is extracted during UC work (where the concepts are discovered) and formalized in the usecase output. think-arch reads and uses these terms as shared language. DDD's principle of "domain is central" was considered, but making Domain Model a separate pipeline stage would be over-engineering for the project scale. Domain concepts are discovered during UC work and consumed by architecture — placing extraction in think-usecase and usage in think-arch is the practical choice.

### 3. New skill: auto-scaffold

Autonomous skill that sets up and verifies the development base. Runs after think-arch, before think-plan.

**Input:** `.arch.md` (Technology Stack, Component structure, Test Strategy)

**What it does:**
- Project structure creation, dependency installation, build configuration
- Test infrastructure setup for each tier
- Verification: build succeeds, app runs, each test runner works, dev loop (edit → build → test) cycles

**What it does NOT do:**
- Implement any FR logic
- Create feature tests
- It creates the base on which think-code's coder agents can develop and test

**Verification criteria:**

| Check | What it confirms |
|-------|-----------------|
| Build | Source → executable artifact |
| Run | App launches without error |
| Test runners | Each tier's runner executes and an empty/minimal test passes |
| Dev loop | Code change → build → test cycle works |

**Output:** `.scaffold.md` with frontmatter (revision, sources referencing `.arch.md`), verified build/test commands, project structure, and any issues found.

**History:** `.scaffold.history.md` — Session Close entries per execution, same pattern as other think-* skills.

**Feedback:** On failure, scaffold report records issues with `Stage: arch`. think-arch detects unreflected scaffold reports on iteration entry.

**Impact on think-plan:**
- think-plan reads scaffold report for verified build/test/launch commands → Launch & Verify is populated with **verified facts**, not aspirations
- think-plan no longer needs to create scaffold IUs (IU-1 style) — the scaffold already exists and is verified
- think-plan focuses purely on feature implementation units

### 4. Pipeline change

```
[Before] think-usecase → think-spec → think-plan → think-code → think-verify
[After]  think-usecase → think-arch → auto-scaffold → think-plan → think-code → think-verify
```

### 5. Downstream impacts

| Skill | Change needed |
|-------|--------------|
| think-usecase | Expand UC format: add validation/error handling, platform capabilities, Domain Model section. Absorb spec-reviewer's requirements-related review criteria. |
| think-plan | Input changes from `.spec.md` to `.arch.md`. Read scaffold report for Launch & Verify. Remove scaffold IU pattern. |
| think-verify | Waterfall trace: split `spec` stage into `usecase` and `arch` stages. |
| compass | Update pipeline routing to reflect new skill sequence. |
| auto-spec (TODO.md) | Direction changes — may become auto-arch or be reconsidered. |
| spec-reviewer agent | Remove or restructure into usecase-reviewer expansion + arch-reviewer. |

## Rejected Alternatives

### Keep think-spec, add test environment step

Adding a test-env skill without restructuring would fix the immediate test environment problem but leave the UC/FR redundancy and mixed abstraction levels in place. The restructuring addresses root causes, not symptoms.

### Domain Model as independent pipeline stage

DDD recommends domain as the central concern. However, for the scale of projects in this pipeline (solo developer, single application), a dedicated domain modeling stage would be over-engineering. Domain concepts are naturally discovered during UC work and don't need a separate ceremony.

### Merge everything into one skill

Combining UC discovery, architecture design, and scaffold setup into a single skill would eliminate handoffs but create an unwieldy skill that mixes conversation modes (Socratic interview for UCs, technical design for architecture, autonomous execution for scaffold).

## Next Steps

1. Design expanded think-usecase output format (`.usecase.md` with Domain Model, validation, error handling sections)
2. Design think-arch skill (SKILL.md, references, output template, arch-reviewer agent)
3. Design auto-scaffold skill (SKILL.md, references, report template)
4. Update think-plan to accept `.arch.md` input and read scaffold reports
5. Update think-verify waterfall trace for usecase/arch stage split
6. Update compass pipeline routing
7. Revisit TODO.md items (auto-spec → auto-arch, pipeline orchestrator)

## Implementation Status

Reflects the state of implementation as of 2026-04-12.

### Completed

| # | Next Step | Result |
|---|----------|--------|
| 1 | Expanded think-usecase output format | Done — think-usecase now includes validation/error handling per UC, platform capabilities audit, Domain Model extraction (glossary, relationships, state transitions), UI screen grouping, and mock generation. 13 reference files support the skill. |
| 2 | Design think-arch | Done — think-arch covers Technology Stack, External Dependencies, Component Design (DB schema, information flows, interface contracts), and Test Strategy. 8 reference files, arch-reviewer and domain-updater agents. |
| 3 | Design auto-scaffold | Done — implemented as **auto-bootstrap** (renamed from auto-scaffold). Sets up project structure, dependencies, build config, and test infrastructure per tier. Verifies build, run, test runners, and dev loop. Outputs `.bootstrap.md` (not `.scaffold.md`). |
| 4 | Update think-plan | Done — accepts `.arch.md` input, reads bootstrap report for verified Launch & Verify commands, no scaffold IUs. Phase 1 (plan + verification) and Phase 2 (implement + test loop, max 3 cycles). |
| 5 | Update think-verify waterfall trace | Removed — think-verify was removed from the pipeline. Its waterfall trace diagnostic was absorbed into compass (Pipeline Diagnosis mode, Layer 1–3 trace). |
| 6 | Update compass pipeline routing | Done — compass reflects the new pipeline: think-usecase → think-arch → auto-bootstrap → think-plan. Also routes to autonomous variants (auto-usecase, auto-plan) and ideation skills (spark-brainstorm, spark-decide). |
| 7 | Revisit TODO.md items | Partially done — auto-spec was not created. auto-usecase and auto-plan exist as autonomous alternatives to think-usecase and think-plan respectively. |

### Additional changes beyond the original plan

| Change | Detail |
|--------|--------|
| think-code removed | Implementation is now handled within think-plan's Phase 2 (implement + test loop). A separate coding skill was unnecessary — think-plan autonomously implements, runs tests, and iterates. |
| think-verify removed | Verification is embedded in think-plan (Phase 2 test cycles) and compass (pipeline diagnosis). A dedicated verification skill was redundant. |
| spec-reviewer agent removed | Replaced by usecase-reviewer (UC quality + system completeness) and arch-reviewer (architecture quality). |
| coder agent removed | Implementation is done directly in think-plan's Phase 2, not delegated to a coder subagent. |
| risk-assessor agent removed | Risk assessment is handled inline within auto-plan (Step 6) and think-plan's review process. |
| domain-updater agent added | Spawned by think-arch during Component Design when Domain Model changes are needed. Updates the `.usecase.md` Domain Model without switching skills. |
| auto-usecase added | Autonomous UC generation without interactive interview. Uses usecase-composer, usecase-reviewer, usecase-reviser, and usecase-explorer agents in a compose → quality → growth loop. |
| auto-plan added | Autonomous plan generation without interactive interview. Shares think-plan's references and plan-reviewer agent. |

### Final pipeline

```
[Interactive]   think-usecase → think-arch → auto-bootstrap → think-plan
[Autonomous]    auto-usecase  → think-arch → auto-bootstrap → auto-plan
[Ideation]      spark-brainstorm → spark-decide
[Navigation]    compass
[Standalone]    web-design-mock
```
