---
title: "auto-bootstrap stepwise behavior under greenfield vs incremental"
status: draft
decision: "TBD — define per-step behavior contracts in `auto-bootstrap/SKILL.md` for greenfield (no existing code) vs incremental (existing code) modes."
supersedes: []
related: []
tags: [auto-bootstrap, greenfield, brownfield, incremental]
created: 2026-04-25
updated: 2026-04-25
---

# auto-bootstrap stepwise behavior under greenfield vs incremental

## Context

`plugins/a4/skills/auto-bootstrap/SKILL.md` is currently the only a4 skill that explicitly recognizes a brownfield (existing-code) entry path. Step 0 declares the binary mode based on `a4/bootstrap.md` presence ("If `a4/bootstrap.md` already exists, archive it … treat this run as **incremental**. Otherwise **fresh**.") and Step 1 extends this with a "Codebase Assessment" branch that distinguishes "no existing code" (fresh bootstrap) from "existing code" (incremental, only set up what's missing).

Per-step behavior beyond Step 1, however, is not consistently parameterized by mode:

- **Step 2 — Project Structure** prescribes "Initialize project files (`package.json`, `pyproject.toml`, …)", "Install dependencies", "Configure build", "Create a minimal entry point". For incremental mode against a working project these are no-ops or partial — but the SKILL.md does not say which actions to skip or how to reconcile with existing configuration.
- **Step 3 — Test Infrastructure** prescribes "Install test dependencies", "Create test configuration file", "Write one minimal passing test per tier". For an existing project that already has unit tests, Steps 3.1–3.3 may be partially or fully redundant.
- **Step 4 — Verification** is the same in both modes, which is correct (verification should always run).
- **Step 5 — Handle Issues** treats all failures uniformly, but in incremental mode some failures (e.g., unexpected dev-dependency conflicts) trace back to pre-existing configuration the user may not want auto-bootstrap to touch.

The pipeline-restructure thread's inventory pass (see [[plugins/a4/.handoff/pipeline-restructure/2026-04-25_1804_compass-and-run-fallback-shipped]]) flagged this as a clarity gap: the binary mode is set in Step 0–1, but the rest of the skill reads as if greenfield is the default and incremental is "skip what's already there" without spelling out which steps that touches.

## Open Questions

- **Stepwise contract.** For each of Steps 2–5, what are the exact contracts under each mode? E.g., Step 2 fresh: "create directory structure, initialize manifests, install deps, configure build, write entry point"; Step 2 incremental: "skip directory creation if already laid out; refuse to overwrite existing manifests; install only declared-but-missing deps; do not modify existing build config without an explicit incremental-fix request."
- **Refusal vs nudge.** When incremental mode detects a configuration that contradicts `architecture.md` (e.g., `architecture.md` says Vitest but the project has Jest), should auto-bootstrap refuse to "fix" the working setup, emit an architecture-targeted review item, or attempt a migration with user confirmation?
- **Reconciliation surface.** Where does the diff between `architecture.md`'s prescribed stack and the existing project's actual stack get recorded? Currently architecture-issue review items per Step 5 are the natural home, but their wording assumes a fresh install.
- **Test isolation in incremental mode.** Step 3's "Verify tier isolation" makes sense for greenfield where auto-bootstrap owns the test config. For incremental against existing test runners with their own conventions, the isolation check may be intrusive.
