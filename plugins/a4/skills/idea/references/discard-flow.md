# Idea Discard Mode

Triggered when `$ARGUMENTS` starts with the token `discard`. The remainder after the first whitespace is parsed as: `<id-or-slug> [reason]`.

## D1. Resolve the idea file

The second token is the **target**. Accept three forms and resolve in this order:

1. **Numeric id** (e.g., `12`) — glob `<project-root>/a4/idea/<id>-*.md`. Exactly one match expected; error if zero or multiple.
2. **Folder-prefixed path** (e.g., `idea/12-foo`) — glob `<project-root>/a4/<path>.md`. Exactly one match expected.
3. **Slug fragment** (any other non-empty token) — glob `<project-root>/a4/idea/*-<fragment>*.md`. If exactly one matches, use it; if multiple match, list them to the user and ask which.

If no file resolves, abort with: "No idea file found for `<target>`. List candidates with `ls a4/idea/`."

## D2. Check current status

Read the resolved file's frontmatter. If `status` is:

- `open` → proceed to D3.
- `promoted` → abort: "Idea `<path>` is already `promoted`. Discarding a promoted idea is ambiguous; edit by hand if you truly want to reverse that."
- `discarded` → report "`<path>` is already `discarded`. No change." and exit.

## D3. Apply the discard

Edit the file in-place via the `Edit` tool:

1. Change the frontmatter `status:` value from `open` to `discarded`.
2. Update the frontmatter `updated:` to today's date.
3. If a reason was provided (any tokens after `<id-or-slug>`), append a `## Change Logs` bullet (creating the section if not already present):

   ```markdown
   ## Change Logs

   - <YYYY-MM-DD> discarded — <reason text>
   ```

   Use the reason verbatim — no re-wording. If the section already exists, append a new dated bullet.

## D4. Report

Tell the user:

```
Discarded idea #<id> → /abs/path/to/a4/idea/<id>-<slug>.md
Reason recorded: <reason or "none">
```

Do not commit. Leave in the working tree.
