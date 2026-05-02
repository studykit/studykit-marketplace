# Step 3: Integration + Smoke Tests

**Invariant:** Step 3 runs only when every cycle ready task is integrated into local main (parallel mode: every Step 2.5 merge succeeded; serial mode: every task committed without halt). Any merge sweep failure → skip Step 3 and end the cycle in halt. The test-runner runs against a fully-integrated tree so its `target:` mapping (failure → task) stays honest.

Otherwise, spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
ci file: <absolute path to a4/ci.md>  # single source of truth for test execution
a4/ path: <absolute path>
Cycle: <current integer>

Use ci.md's ## How to run tests section (per-tier commands, multi-tier run, test
isolation flags) plus the optional ## Smoke scenario for run / test commands.
Run integration and smoke tests as defined there. For each failing test, emit
one review item at a4/review/<id>-<slug>.md via allocate_id.py — frontmatter
and body shape per ${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md — with:

  kind: finding
  status: open
  target: [<<type>/<id>-<slug> (where <type> ∈ {task, bug, spike, research}) if the failure is traceable to a task; leave empty when the failure is genuinely cross-task — the calling skill classifies the broader category>]
  source: test-runner
  priority: high | medium
  labels: [test-failure, cycle-<N>]

Body includes: test name, expected vs actual, full stack/log snippet, and best-guess
root cause pointer (without classifying as task/arch/usecase — the calling skill does
that classification).

Return: counts (passed, failed), list of review item ids written.
""")
```
