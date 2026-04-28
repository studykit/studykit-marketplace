# Step 4: Roadmap Verification

Spawn `Agent(subagent_type: "a4:roadmap-reviewer")`. Pass:

- `a4/` absolute path
- Prior open roadmap-targeted review item ids (to deduplicate)

The reviewer emits per-finding review items to `a4/review/<id>-<slug>.md` and returns a summary.

## Walk findings

Apply the **stop on strong upstream dependency** policy at `../wiki-authorship.md` §Cross-stage feedback — roadmap depends directly on architecture (component → task split) and UCs (UC → AC source), so upstream findings halt this skill rather than continuing with stale assumptions.

- **Roadmap-level fix** — edit `roadmap.md` or the affected task file; flip the review item via `transition_status.py --to resolved`; add a `<change-logs>` bullet on `roadmap.md` if it changed.
- **Arch / usecase finding** — **stop**. Leave the review item `status: open` with its existing `target:` pointing at `architecture` or `usecase/...`. Tell the user to run `/a4:arch` or `/a4:usecase iterate` and resume `/a4:roadmap iterate` afterwards.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff.

## Loop bound

Loop up to 3 review rounds if roadmap-level revisions are substantial. Once the reviewer returns `ACTIONABLE` (or the user explicitly approves moving on with deferred findings), the roadmap is ready.

Suggest `/a4:run` to drive the implement loop.
