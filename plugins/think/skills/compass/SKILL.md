---
name: compass
description: "This skill should be used when the user doesn't know which think skill to use, is stuck mid-pipeline, or needs help deciding the next step. Triggers: 'what should I do next', 'where do I go from here', 'which skill should I use', 'help me navigate', 'I'm stuck', 'next step', 'continue the pipeline', 'compass', or when the user invokes the think plugin without a specific skill name."
argument-hint: <topic slug, file path, or description of what you need>
allowed-tools: Read, Glob, Grep, Skill
---

# Pipeline Navigator

Helps users find the right skill or diagnose the next step in an ongoing pipeline.

Argument: **$ARGUMENTS**

## Step 1: Detect Context

Determine the user's situation by checking for existing pipeline artifacts.

### 1.1 Resolve topic

- If `$ARGUMENTS` is a file path or topic slug: extract the topic slug (e.g., `my-app` from `A4/my-app.usecase.md` or from the literal `my-app`).
- If `$ARGUMENTS` is empty or a free-text description: skip to **Step 2** (Fresh Start).

### 1.2 Scan artifacts

Glob for `A4/<slug>*` and check which files exist:

| Artifact | File pattern | Produced by |
|----------|-------------|-------------|
| Use Cases | `<slug>.usecase.md` | think-usecase, auto-usecase |
| Architecture | `<slug>.arch.md` | think-arch |
| Bootstrap | `<slug>.bootstrap.md` | auto-bootstrap |
| Plan | `<slug>.plan.md` | think-plan, auto-plan |
| Test Report | `<slug>.test-report.c*.md` | think-plan |

Also check for review reports and archived bootstrap reports (e.g., `<slug>.usecase.review-*.md`, `<slug>.arch.review-*.md`, `<slug>.plan.review-*.md`, `<slug>.bootstrap.r*.md`).

If **no artifacts found** for the slug: skip to **Step 2** (Fresh Start), treating the argument as a topic description.

If **artifacts found**: proceed to **Step 3** (Pipeline Diagnosis).

---

## Step 2: Fresh Start

The user has no existing artifacts or described a vague intent. Present the skill catalog and help them pick.

Ask: **"What are you trying to do?"** and show the options:

### Ideation
| Skill | What it does |
|-------|-------------|
| `spark-brainstorm` | Generate ideas with structured creative techniques |
| `spark-decide` | Evaluate options and make a documented decision (ADR) |

### Pipeline (interactive)
| Skill | What it does |
|-------|-------------|
| `think-usecase` | Shape a vague idea into concrete Use Cases + Domain Model through dialogue |
| `think-arch` | Design architecture — tech stack, components, interfaces, test strategy |
| `think-plan` | Plan, implement, and test — autonomously iterate until tests pass |

### Pipeline (autonomous)
| Skill | What it does |
|-------|-------------|
| `auto-usecase` | Auto-generate use cases without interview |
| `auto-bootstrap` | Set up project structure, dependencies, build, and test infrastructure |
| `auto-plan` | Auto-generate impl plan without interview |

### Standalone
| Skill | What it does |
|-------|-------------|
| `web-design-mock` | Create HTML/CSS mockups and prototypes |

Based on the user's answer, invoke the chosen skill via the Skill tool:
```
Skill({ skill: "think:<skill-name>", args: "<user's topic or file path>" })
```

---

## Step 3: Pipeline Diagnosis

The user has existing artifacts. Diagnose where they are and what to do next.

### 3.1 Read artifact state

Read each existing artifact file's **frontmatter and status sections only** (not the full content). Extract:

- **Status** field (draft, in-review, final, etc.)
- **Open Items** section — unresolved issues from reviews
- **Source SHA** fields — whether upstream changes have propagated
- **Plan status** (from plan) — draft, verified, implementing, complete, blocked
- **Plan phase** — plan-review, implement, test
- **Plan cycle** — current test cycle (1-3)

If test reports exist (`<slug>.test-report.c*.md`), read the **summary table** and **failure analysis**.

If review reports exist (e.g., `<slug>.plan.review-r*.md`), read their verdict (ACTIONABLE / NEEDS_REVISION).

### 3.2 Read implementation state

If a plan exists with `status: implementing` or `status: complete`:

1. Read the plan's **file mappings** for IUs.
2. Check whether the mapped files actually exist (Glob).
3. For files that exist, do a lightweight check — read the first 30 lines to confirm the file's purpose matches the IU's description (e.g., component name, exports, main function).

This is a **paper review**, not a runtime test. The goal is to detect obvious mismatches, not verify behavior.

### 3.3 Diagnose the gap layer

Use a simplified waterfall trace to locate where the issue is:

**Layer 1 — Use Cases**: Are there open items or unreflected review feedback in the usecase file?
- If yes → recommend `think-usecase` to iterate.

**Layer 2 — Architecture**: Is there an arch file? Does it have open items, unresolved review feedback, or a source SHA mismatch with the usecase file?
- If no arch exists → recommend `think-arch` to create one.
- If arch has issues → recommend `think-arch` to iterate.

**Layer 2.5 — Bootstrap**: Is there a bootstrap report? Does it show all checks passing? Is it current with the arch file?
- If no bootstrap exists → recommend `auto-bootstrap` to set up the dev environment.
- If bootstrap has failures → check if arch issues (recommend `think-arch`) or environment issues (report to user).

**Layer 3 — Plan + Implementation + Testing**: Is there a plan? What is its status?
- If no plan exists → recommend `think-plan` to create and execute one.
- If `status: blocked` → read the latest review or test report to understand why. Trace back to the responsible layer (arch/usecase).
- If `status: draft` or `status: verified` → recommend `think-plan` to continue (implementation not started or not complete).
- If `status: implementing` → check `phase` and `cycle` to determine progress. Recommend `think-plan` to resume.
- If `status: complete` → check whether file mappings match actual files. If mismatches, recommend `think-plan` to re-run.

### 3.4 Present diagnosis

Report to the user in this format:

```
## Pipeline Status: <topic>

| Stage | Artifact | Status |
|-------|----------|--------|
| Use Cases | <slug>.usecase.md | <status summary> |
| Architecture | <slug>.arch.md | <status summary or "not yet created"> |
| Bootstrap | <slug>.bootstrap.md | <status summary or "not yet run"> |
| Plan | <slug>.plan.md | <status, phase, cycle — or "not yet created"> |

## Diagnosis

<1-3 sentences explaining where the gap is and why>

## Recommendation

→ **<skill-name>**: <what to do and why>
```

Wait for the user's confirmation, then invoke the recommended skill:
```
Skill({ skill: "think:<skill-name>", args: "<file path>" })
```

If the user disagrees with the recommendation, discuss alternatives and let them choose.
