# Workflow Test Principles

Workflow tests should protect executable behavior and stable layer boundaries.
They should not freeze prose quality, heading preferences, or authoring judgment
unless that wording is intentionally part of a contract.

## Test when the rule is mechanical

Use tests for behavior that can fail objectively:

- Resolver output and selected authoring paths.
- Provider/cache read, write, refresh, and mutation behavior.
- Hook output shape and session-state behavior.
- Main-agent, operator, and contributor boundary regressions.
- Required manifest, config, or instruction-file wiring.

## Prefer documentation and review for judgment

Do not add tests that only check:

- Whether prose is persuasive or complete.
- Exact wording in non-contract documentation.
- Preferred heading names when the heading is not a contract.
- Whether an authoring rationale is high quality.

If a documentation test needs a stable heading, phrase, or path, treat that value
as an explicit contract and keep the assertion narrow. Otherwise, record the
principle in documentation and rely on review.

## Keep documentation tests boundary-focused

Documentation tests are appropriate when they prevent a known layer leak or
schema catalog from returning to the wrong surface. They should assert the
boundary, not the full document text.
