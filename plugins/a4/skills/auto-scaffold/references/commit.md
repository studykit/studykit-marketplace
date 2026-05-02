# Scaffold Commit Format

Stage all scaffold-configured project files (package manifest, build config, source layout, minimal entry point) plus any emitted review items and research reports.

Single commit:

```
scaffold: <fresh | incremental>

- Build: PASS | FAIL
- Run: PASS | FAIL
- Dev loop: PASS | FAIL
- Issues: <open-architecture-count> open
```

Never skip hooks, amend, or force-push.

Commit-subject conventions for other a4 commits live in `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md`.
