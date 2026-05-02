# ci-setup Commit Format

Stage `a4/ci.md`, any emitted review items and research reports, and all test-infrastructure files (test runner configs, sample tests, package-manager script changes).

Single commit:

```
ci-setup: <fresh | update>

- Tiers: unit=<PASS|FAIL>, integration=<PASS|FAIL>, e2e=<PASS|FAIL|N/A>
- Multi-tier run: PASS | FAIL
- Issues: <open-architecture-count> open
```

Never skip hooks, amend, or force-push.

Commit-subject conventions for other a4 commits live in `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md`.
