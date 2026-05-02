# Task Discard Procedure

Loaded by `/a4:discard`. The remainder after the first whitespace is parsed as: `<id-or-slug> [reason]`. UC-cascade discards (when a UC flips to `discarded`) are handled automatically by the PostToolUse cascade hook — this procedure is for **explicit one-off task discards** that are not driven by a UC cascade.

After a4 v12.0.0 the four issue families (`task`, `bug`, `spike`, `research`) live in separate top-level folders. Resolution walks all four.

## D1. Resolve the task file

Accept three forms and resolve in this order:

1. **Numeric id** (e.g., `42`) — glob `<project-root>/a4/{task,bug,spike,research}/<id>-*.md`. Exactly one match expected; error if zero or multiple.
2. **Folder-prefixed path** — `task/<id>-<slug>`, `bug/<id>-<slug>`, `spike/<id>-<slug>`, or `research/<id>-<slug>`. Resolve as `<project-root>/a4/<path>.md`.
3. **Slug fragment** (any other non-empty token) — glob `<project-root>/a4/{task,bug,spike,research}/*<fragment>*.md`. If exactly one matches, use it; if multiple match, list them with `<type>/<id>-<title>` and ask which.

If no file resolves, abort with: "No task file found for `<target>`. List candidates with `ls a4/task/ a4/bug/ a4/spike/ a4/research/`."

## D2. Check current status

Read the resolved file's frontmatter. `ISSUE_FAMILY_TRANSITIONS` allows `discarded` from `open | pending | progress | complete | failing`:

- Any of those five → proceed to D3.
- `discarded` → report "`<path>` is already `discarded`. No change." and exit.

Surface the task's `type:` and `implements:` / `spec:` to the user before flipping, so they can confirm they're discarding the right one. One-line summary, no separate prompt unless slug-fragment resolution returned multiple candidates in D1.

## D3. Apply the discard

Compose the reason: every token after `<id-or-slug>` joined by a single space. If empty, use `"discarded via /a4:discard"` as a default. The reason is captured in the body's `## Why Discarded` section (see below) — there is no CLI to pass it to.

If the user supplied a reason worth narrative capture, append (or extend) a `## Why Discarded` body section via `Edit` **before flipping `status:`**, so the file is consistent at any read point:

```markdown
## Why Discarded

- <YYYY-MM-DD> — <reason text>
```

Append a new dated bullet if the section already exists.

Then edit the file's frontmatter `status:` to `discarded` directly. The PostToolUse cascade hook detects the legal transition, refreshes `updated:`, and runs no cross-file cascade for issue-family discards (they don't propagate). If the resulting jump is illegal (already-`discarded` etc.), the cascade hook silently skips and the Stop-hook safety net surfaces the violation. Skip the discard if D2 returned `discarded`; never write the same status twice.

## D4. Spike artifact directory advisory (if `type: spike`)

If the task's `type:` is `spike` and `<project-root>/artifacts/spike/<id>-<slug>/` exists, **do not delete it**. Per `${CLAUDE_PLUGIN_ROOT}/authoring/artifacts.md`, archiving spike code is a manual `git mv` decision. Tell the user:

> Spike artifact directory `artifacts/spike/<id>-<slug>/` was left in place. Options: (a) leave as-is for reference, (b) `git mv artifacts/spike/<id>-<slug> artifacts/spike/archive/<id>-<slug>` to archive, (c) `git rm -r artifacts/spike/<id>-<slug>` to delete. Pick one when convenient.

If the directory does not exist, skip this step silently.

## D5. Report

Tell the user:

```
Discarded #<id> (<title>, type: <type>) → a4/<type>/<id>-<slug>.md
Reason: <reason or "(none)">
Spike artifact directory: <left in place at artifacts/spike/<id>-<slug>/ | not present | n/a>
```

Mention any other artifacts the user may want to revisit:

- If `implements:` was non-empty, name the UC(s) so the user can decide whether to re-author a replacement task or also discard the UC.
- If `spec:` was non-empty, the cited spec(s) are unaffected.

If the discarded task was the only `pending` / `progress` / `failing` task tied to a UC, mention that the UC may now have nothing to ship — the user can decide whether to author a replacement task, discard the UC itself, or leave the UC in `implementing` waiting for another task.

Do not commit. Leave files in the working tree. The single-commit scope is just the edited task file (status flip + optional `## Why Discarded` section). Spike artifact directory moves/deletes are a separate, user-driven commit.
