# Session Resume

Procedure for resuming implementation from a previous session. This reference is read by the think-code orchestrator when it detects an existing session (not all units are TODO).

## 1. Detect Previous Progress

Scan all IU statuses in the plan file:

| Status Pattern | Mode | Action |
|---------------|------|--------|
| All `TODO` | Fresh Start | No resume needed — proceed normally from Step 0 |
| Mix of `DONE` and `TODO` | Resume | Follow the Resume procedure below |
| Any `IN_PROGRESS` | Interrupted | Previous session was interrupted mid-unit. Follow the Interrupted procedure below |

## 2. Resume Procedure

The plan has some completed units. Pick up where the last session left off.

### Context Recovery

Before starting the next unit, build context from the previous session's work:

1. **Read recent completion notes** — read the Completion Notes of the last 2-3 DONE units. These contain implementation decisions, deviations, and rationale that may affect the next unit.

2. **Check git log** — verify that IU-tagged commits exist for the DONE units:
   ```bash
   git log --oneline --grep="IU-" --since="2 weeks ago"
   ```
   Each DONE unit should have a corresponding commit. If a unit is marked DONE but has no commit, something is inconsistent.

3. **Run existing tests** — run the test suite to confirm previously completed work still passes:
   ```bash
   # Use the project's test runner
   npm test
   ```

### State Consistency Check

If tests fail for previously DONE units:
- **Do not proceed.** Something changed since the last session.
- Report to the user: which tests failed, which units they belong to.
- Wait for the user to resolve before continuing.

If everything passes, present the resume summary:

> **Resuming implementation:**
> - **Completed:** IU-1 (data model), IU-2 (auth service)
> - **Next:** IU-3 (API endpoints)
> - **Remaining:** 4 units
> - **Tests:** all passing
>
> Continue?

### Deviation Notes

Check if any units have Deviation Notes from a previous session. If so, report them:

> **Previous deviations:**
> - IU-4: skipped — OAuth2 vs SAML conflict (2026-04-09)
>
> This unit and its dependents are blocked until resolved. Continue with unaffected units?

Re-derive BLOCKED state from the dependency graph: any unit depending on a deviated (TODO with Deviation Note) unit is blocked.

## 3. Interrupted Procedure

An `IN_PROGRESS` unit means the previous session was interrupted mid-implementation.

1. **Reset to TODO** — set the IN_PROGRESS unit's status back to `TODO`.
2. **Check for partial work** — look for uncommitted changes:
   ```bash
   git status
   git diff
   ```
3. **Clean up if needed** — if there are uncommitted changes from the interrupted unit:
   - Report to the user what was found
   - Let the user decide: keep the partial work (manual commit) or discard it
4. **Notify the user** — explain what happened and that the unit will be re-implemented from scratch:

   > **Interrupted session detected:**
   > - IU-3 (API endpoints) was `IN_PROGRESS` — reset to `TODO`
   > - Found uncommitted changes in `src/routes/api.ts`
   >
   > Discard partial work and re-implement IU-3?

5. After cleanup, proceed with the normal Resume flow.
