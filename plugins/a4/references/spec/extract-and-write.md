# Steps 2–5: Extract, Discover Research, Decide Status, Write

## Step 2: Extract the spec

Two input modes:

- **No argument.** Read recent conversation context. Identify the converged shape — what artifact it describes, the prescriptive rules, and any decisions explaining why the shape landed this way. If no clear shape emerged, ask the user which one to record.
- **Short summary / title.** Use `$ARGUMENTS` as a seed; still draw the full content from recent conversation.

Draft a scratch summary covering the fields and sections defined in `../spec-authoring.md` (`title`, `decision` one-liner, required `<context>` + `<specification>`, optional sections only when the conversation produced content for them, candidate `supersedes:` if the conversation referenced a predecessor). Do **not** emit placeholder sections.

Present the draft to the user before proceeding. Iterate until the substance is confirmed.

## Step 3: Discover related research

Offer two sources for citations:

1. **Auto-scan.** `Glob ./research/*.md` (relative to project root). For each candidate, compare the file's `topic:` frontmatter or slug to the spec's title/topic. Propose plausible matches.
2. **User-specified.** If the user named a research file during the conversation, include it verbatim.

Confirm the final list with the user. Empty is fine — specs do not require prior research. Step 5b runs the registrar.

## Step 4: Decide on status via dialogue

Interpret confidence/commitment from the user:

- `active` signals — "this is the spec", "lock this in", "확정", "이걸로 가자".
- `draft` signals — "tentative", "still open", "두고 보자", "아직 여지 있음".

If ambiguous, ask once: *"Activate now, or leave as `draft` for now?"*

**Record the signal — do not write it yet.** The file is always born at `status: draft` in Step 5; Step 6 flips it via the writer if `active` was signaled.

## Step 5: Allocate id, slug, and write the file

1. Allocate id:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
   ```

2. Derive slug from the title (kebab-case; ASCII lowercase + CJK pass through; punctuation stripped; collapse hyphens; trim to ~50 chars; fall back to `untitled` if empty).

3. File path: `<project-root>/a4/spec/<id>-<slug>.md`.

4. Use the `Write` tool. Frontmatter shape, required body sections (`<context>`, `<specification>`), optional sections (`<decision-log>`, `<open-questions>`, `<rejected-alternatives>`, `<consequences>`, `<examples>`), and tag-form rules are defined in `../spec-authoring.md`. Initial `status:` is always `draft`; `decision:` is the one-liner that Step 6 will quote in the activate transition. Do **not** hand-write `<research>` — Step 5b registers it.

Report the full file path: "Spec recorded at `<path>` as `draft`."

## Step 5b: Register research citations

For each research artifact confirmed in Step 3, invoke the registrar:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
  "<project-root>/a4" \
  "research/<slug>" \
  "spec/<id>-<slug>"
```

Idempotent. Skip entirely when Step 3's list is empty; run once per (research, spec) pair otherwise. The registrar owns the four-place atom (spec `research:` + `<research>`, research `cited_by:` + `<cited-by>`) and bumps the research file's `updated:`.

## Step 6: Activate via writer (if signal was `active`)

Invoke only when the user signaled `active` in Step 4, or the whole invocation is in activate-existing mode.

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" "<project-root>/a4" \
  --file spec/<id>-<slug>.md \
  --to active \
  --reason "<one-line shape summary>" \
  --json
```

The writer's lifecycle / validation / supersedes-cascade behavior is defined in `../spec-authoring.md` §Lifecycle. On `ok: true`, report the primary flip plus any cascades. On `exit 2`, surface `validation_issues` verbatim and return to Step 5 — never retry with `--force`.
