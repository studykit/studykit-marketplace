# Claude Code Commands Reference

> Source: [Claude Code plugins docs](https://code.claude.com/docs/en/plugins.md), [skills reference](https://code.claude.com/docs/en/skills.md)

## Command vs Skill

| Aspect | Command (thin layer) | Skill (LLM reasoning) |
|--------|---------------------|----------------------|
| Auto-invocation | No (`disable-model-invocation: true`) | Yes (Claude decides) |
| Execution | Shell injection — script runs before Claude sees content | Claude orchestrates via tools |
| Use case | Run script, output result | Multi-step, LLM judgment needed |

Both are implemented as skill directories. "Command" = skill with `disable-model-invocation: true` + shell injection.

## Directory Structure

```
my-plugin/
├── skills/
│   ├── register-result/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── register_result.py
│   └── sessions/
│       ├── SKILL.md
│       └── scripts/
│           └── list_sessions.py
```

Invoked as `/plugin-name:register-result`, `/plugin-name:sessions`.

## SKILL.md Format

```yaml
---
description: Register deliverable files from a child session
disable-model-invocation: true
---

!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/register-result/scripts/register_result.py $ARGUMENTS`
```

### Frontmatter Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `description` | When/why to use (max 250 chars) | Yes |
| `disable-model-invocation` | `true` to prevent auto-trigger | For commands |
| `argument-hint` | Autocomplete hint (e.g., `[file1 file2 ...]`) | Optional |
| `allowed-tools` | Tools Claude can use without asking | Optional |

## Arguments

- `$ARGUMENTS` — full argument string from user input
- `$0`, `$1`, ... or `$ARGUMENTS[0]`, `$ARGUMENTS[1]` — indexed args
- If `$ARGUMENTS` not in content, Claude Code appends `ARGUMENTS: <input>` automatically

## Shell Injection

Script output is inserted into skill content **before** Claude sees it.

**Inline:** `` !`command` ``

**Multi-line:**
````
```!
uv run script.py
echo "---"
```
````

## Available Template Variables

| Variable | Value |
|----------|-------|
| `$ARGUMENTS` | User input after command name |
| `${CLAUDE_SESSION_ID}` | Current session UUID |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin installation directory |
| `${CLAUDE_SKILL_DIR}` | Current skill directory |
| `${CLAUDE_PLUGIN_DATA}` | Persistent plugin data directory |

## Example: Thin-Layer Command

**`skills/sessions/SKILL.md`:**
```yaml
---
description: List child sessions and their status
disable-model-invocation: true
argument-hint: ""
---

!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/sessions/scripts/list_sessions.py ${CLAUDE_SESSION_ID}`
```

Python script receives `${CLAUDE_SESSION_ID}` as `sys.argv[1]`, finds `session-tree.json`, reads and formats output.

## Testing

```bash
# Load plugin from dev directory
claude --plugin-dir ./my-plugin

# Invoke commands
/my-plugin:sessions
/my-plugin:register-result file1.md file2.md

# Reload after changes (no restart needed)
/reload-plugins
```
