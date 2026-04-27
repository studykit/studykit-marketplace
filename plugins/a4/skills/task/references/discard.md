# Task Discard Procedure

Loaded by `/a4:task` when `$ARGUMENTS` starts with the token `discard`. Author mode does not need this file.

The remainder after the first whitespace is parsed as: `<id-or-slug> [reason]`. UC-cascade discards (when a UC flips to `discarded`) are handled automatically by `transition_status.py` — this procedure is for **explicit one-off task discards** that are not driven by a UC cascade.

## D1. Resolve the task file

The second token is the **target**. Accept three forms and resolve in this order:

1. **Numeric id** (e.g., `42`) — glob `<project-root>/a4/task/<id>-*.md`. Exactly one match expected; error if zero or multiple.
2. **Folder-prefixed path** (e.g., `task/42-foo`) — glob `<project-root>/a4/<path>.md`. Exactly one match expected.
3. **Slug fragment** (any other non-empty token) — glob `<project-root>/a4/task/*<fragment>*.md`. If exactly one matches, use it; if multiple match, list them with id + title and ask which.

If no file resolves, abort with: "No task file found for `<target>`. List candidates with `ls a4/task/`."

If the target is missing entirely (no second token), abort with the usage hint: "`/a4:task discard <id-or-slug> [reason]` — provide a task id, slug fragment, or `task/<id>-<slug>` path."

## D2. Check current status

Read the resolved file's frontmatter. The writer (`transition_status.py` `TASK_TRANSITIONS`) allows `discarded` from `open | pending | progress | complete | failing`:

- Any of those five → proceed to D3.
- `discarded` → report "`<path>` is already `discarded`. No change." and exit.

Surface the task's `kind:` and `implements:` / `adr:` to the user before flipping, so they can confirm they're discarding the right one. One-line summary, no separate prompt unless slug-fragment resolution returned multiple candidates in D1.

## D3. Apply the discard

Compose the reason: every token after `<id-or-slug>` joined by a single space. If empty, use `"discarded via /a4:task discard"` as the writer's reason — `transition_status.py` requires a non-empty `--reason`.

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file task/<id>-<slug>.md \
  --to discarded \
  --reason "<reason>" \
  --json
```

The writer flips `status:`, bumps `updated:`, and appends a `## Log` entry. If exit code is non-zero, surface the writer's stderr verbatim and stop — do not retry with `--force`.

If the user supplied a reason explicit enough to deserve narrative capture (more than a few words, or distinct from the writer's `## Log` line), additionally append (or extend) a `## Why discarded` body section via `Edit`:

```markdown
## Why discarded

<YYYY-MM-DD> — <reason text>
```

Append a new dated line if the section already exists. Skip this step entirely when no reason was supplied — the `## Log` entry is sufficient.

## D4. Spike sidecar advisory (if `kind: spike`)

If the task's `kind:` is `spike` and `<project-root>/spike/<id>-<slug>/` exists, **do not delete it**. Per the experiments-slot ADR, archiving spike code is a manual `git mv` decision. Tell the user:

> Spike sidecar `spike/<id>-<slug>/` was left in place. Options: (a) leave as-is for reference, (b) `git mv spike/<id>-<slug> spike/archive/<id>-<slug>` to archive, (c) `git rm -r spike/<id>-<slug>` to delete. Pick one when convenient.

If the directory does not exist, skip this step silently.

## D5. Reverse-link refresh

`refresh_implemented_by.py` does **not** filter by status, so a discarded task with non-empty `implements:` will remain in its UCs' `implemented_by:` list. This is consistent with current behavior (the script back-scans the task tree as-is). Skip the script — `implements:` did not change.

If the user later wants the discarded task removed from UC reverse links, that is a separate concern (either delete the task file outright via `git rm`, or filter discarded entries in a future revision of `refresh_implemented_by.py`).

## D6. Report

Tell the user:

```
Discarded task #<id> (<title>, kind: <kind>) → a4/task/<id>-<slug>.md
Reason: <reason or "(none — see ## Log)">
Spike sidecar: <left in place at spike/<id>-<slug>/ | not present | n/a>
```

Mention any other artifacts the user may want to revisit:

- If `implements:` was non-empty, name the UC(s) so the user can decide whether to re-author a replacement task or also discard the UC.
- If `adr:` was non-empty, the cited ADR(s) are unaffected.

If the discarded task was the only `pending` / `implementing` / `failing` task tied to a UC, mention that the UC may now have nothing to ship — the user can decide whether to author a replacement task, discard the UC itself, or leave the UC in `implementing` waiting for another task.

Do not commit. Leave files in the working tree. The single-commit scope is just the edited task file (status flip + optional `## Why discarded` section). Spike sidecar moves/deletes are a separate, user-driven commit per the experiments-slot ADR.
