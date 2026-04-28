# Step 1: Detect Mode

Three modes dispatch from the seed + recent conversation.

## (a) Activate existing

The user is referring to a spec already recorded earlier as `draft`.

**Signals:**

- `$ARGUMENTS` contains a spec id (`12`, `spec/12`), slug fragment, or title that matches an existing `a4/spec/*.md` at `status: draft`; or
- the recent conversation referenced a specific draft spec by path/id.

Detect by `Glob a4/spec/*.md` + frontmatter read; confirm with the user before proceeding (one light question: "Activate `spec/<id>-<slug>`?"). If confirmed, skip Steps 2–5 and jump to **Step 6: Activate via writer**.

## (b) Revise existing

The user wants to extend or amend a live spec.

**Signals:**

- `$ARGUMENTS` references an `active` spec; or
- the conversation produced a refinement or new rule for an existing spec.

The skill edits the spec body in place and appends a `<decision-log>` entry with today's date and the substance of the change. The frontmatter is left at `status: active` — `transition_status.py` is not invoked.

## (c) New record (default)

The seed is a topic/title for a spec not yet on disk. Continue with Step 2.

## Disambiguation

If the user's phrasing is ambiguous, ask once which mode they mean.
