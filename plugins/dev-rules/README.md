# dev-rules

Hook-only Claude Code plugin that injects coding rule sets (currently: **logging conventions**) into Claude's context whenever Claude is about to write or edit a code file.

## How it works

A single `PreToolUse` hook fires on `Write | Edit | MultiEdit`. The dispatcher script (`scripts/dev_rules_hook.py`):

1. Extracts the target `file_path` from the tool input.
2. Resolves the file's language from its extension (Python / JavaScript / Java / Kotlin).
3. Scans every category subdirectory under `rulesets/` (e.g. `rulesets/logging/`) and injects matching ruleset bodies as `additionalContext`:
   - `rulesets/<category>/general.md` — once per session per category, on the first code edit (any language).
   - `rulesets/<category>/<language>.md` — once per session per `<category>:<language>` pair, on the first edit of a file in that language.
4. Subsequent edits emit nothing (silent on dedup).

Dedup state lives at `.claude/tmp/dev-rules/injected-<session_id>.txt` (one line per injected `<category>:<key>`). A `SessionEnd` hook deletes it, and a `SessionStart` hook sweeps orphan files older than 1 day as a safety net for crashed sessions.

All hooks exit 0 unconditionally — they never block an edit, session start, or session end. Internal failures (missing env, IO errors, malformed JSON) are silent.

## Language coverage

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript | `.js`, `.ts`, `.jsx`, `.tsx`, `.mjs`, `.cjs` |
| Java | `.java` |
| Kotlin | `.kt`, `.kts` |

Files with unrecognized extensions still receive each category's `general.md` on the first code edit; no language-specific ruleset is added.

## Customizing rules

Edit the markdown files under `rulesets/<category>/`. The hook injects each body verbatim — no parsing, no frontmatter required. Keep each ruleset short (LLM context budget) and concrete (rules Claude can actually follow).

To add a new category, create a new subdirectory under `rulesets/` (e.g. `rulesets/error-handling/`) containing a `general.md` and any of the supported `<language>.md` files. The hook auto-discovers categories at runtime — no code change required.

## Files

```
plugins/dev-rules/
├── .claude-plugin/plugin.json
├── README.md
├── rulesets/
│   └── logging/
│       ├── general.md
│       ├── python.md
│       ├── javascript.md
│       ├── java.md
│       └── kotlin.md
├── hooks/
│   └── hooks.json
└── scripts/
    └── dev_rules_hook.py      # stdlib python dispatcher (subcommands: pre-edit, session-end, session-start)
```

## Requirements

- `python3` (>= 3.10) on `PATH`. The dispatcher is stdlib-only and runs directly via its shebang — no `uv` or external packages required.

## Debug trace log

Tracing is **off by default**. Enable it only when you need to debug the dispatcher's behavior by setting the environment variable `DEV_RULES_TRACE` to a truthy value (`1`, `true`, `yes`, `on`, case-insensitive) before launching Claude Code:

```bash
DEV_RULES_TRACE=1 claude
```

When enabled, the dispatcher writes a structured record at every decision point (file resolution, language match, dedup hit, inject result, sweep outcome). Output goes **only** to a file — never to stdout — so it does not consume LLM context.

- Location: `.claude/tmp/dev-rules/trace.log` (project root)
- Format: JSON Lines (one record per line)
- Lifecycle: append-only across sessions; `SessionStart` truncates the file if its mtime is older than 1 day (keeps recent sessions for debugging without unbounded growth)

Sample record:
```json
{"ts": "2026-05-03T14:13:01.123456", "sid": "abc-123", "cmd": "pre-edit", "event": "inject", "file_path": "/x/foo.py", "language": "python", "injected_keys": ["logging:general", "logging:python"]}
```

To stop tracing, simply unset `DEV_RULES_TRACE` (or set it to `0` / unset / empty) and restart Claude Code. The existing `trace.log` file is left in place; delete it manually if you want a clean slate.
