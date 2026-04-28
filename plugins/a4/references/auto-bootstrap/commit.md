# Bootstrap Commit Format

Stage `a4/bootstrap.md`, any emitted review items (including those from drift detection), research reports, and all bootstrap-configured project files (package.json, test config, sample tests, etc.).

Single commit:

```
bootstrap: <fresh | iterate>

- Build: PASS | FAIL
- Test tiers: N/M passing
- Dev loop: PASS | FAIL
- Issues: <open-archive-count> open
```

Never skip hooks, amend, or force-push.

Commit-subject conventions for other a4 commits live in `../commit-message-convention.md`.
