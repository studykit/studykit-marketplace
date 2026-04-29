# Step 3: Integration + Smoke Tests

**Invariant:** Step 3 runs only when every cycle ready task is integrated into local main (parallel mode: every Step 2.5 merge succeeded; serial mode: every task committed without halt). Any merge sweep failure → skip Step 3 and end the cycle in halt. The test-runner runs against a fully-integrated tree so its `target:` mapping (failure → task) stays honest.

Otherwise, spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
a4/ path: <absolute path>
Cycle: <current integer>

Use bootstrap.md's <verify> section (verified commands, smoke scenario, test isolation
flags) for build / run / test commands. Run integration and smoke tests as defined
there. For each failing test, emit one review item at
a4/review/<id>-<slug>.md via allocate_id.py with:

  kind: finding
  status: open
  target: [<task/<id>-<slug> if the failure is traceable to a task; otherwise roadmap>]
  source: test-runner
  priority: high | medium
  labels: [test-failure, cycle-<N>]

Body includes: test name, expected vs actual, full stack/log snippet, and best-guess
root cause pointer (without classifying as roadmap/arch/usecase — the calling skill does
that classification).

Return: counts (passed, failed), list of review item ids written.
""")
```
