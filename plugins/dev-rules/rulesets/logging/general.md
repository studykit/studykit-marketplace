# Logging — general rules

Apply to every code edit, regardless of language. Language-specific rulesets layer on top.

## Structured output at **every** level

Use a structured format (JSON Lines or similar) for ERROR / WARN / INFO too — not just for DEBUG / TRACE. Each record carries named fields (timestamp, request/session id, function, event); the human-readable message is one field among others, not the whole record. **Do not mix printf-style strings at operator-facing levels with structured records at diagnostic levels** — it makes the aggregated stream unqueryable.

## TRACE and DEBUG — opt-in, file-only

**Opt-in gate.** Enable via env var (`MYAPP_TRACE=1`, `MYAPP_LOG_LEVEL=debug`), CLI flag (`--trace`, `--debug`), or config. Default OFF.

**File-only.** Write to a dedicated log file, **never stdout/stderr** — anything parsing the stream (pipes, hooks, parent processes) breaks otherwise. Live-tailing in the terminal requires a separate opt-in (e.g. `--trace-stdout`) on top of the level opt-in.

**TRACE — decision points only.** One record per decision: branch taken, early return, dedup hit, cache hit/miss, retry, validation outcome. From the trace alone, a reader should reconstruct which path the code took. If a record isn't naming a decision, it doesn't belong at TRACE.

**Never silent on a return.** Every early return — including success and "nothing to do" — emits a record naming the reason.
