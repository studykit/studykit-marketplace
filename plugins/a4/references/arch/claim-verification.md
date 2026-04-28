# Technical Claim Verification

When writing or confirming any technical claim (API support, library capability, framework constraint, compatibility), verify before recording. Focus on claims whose failure would break implementation.

## Procedure

1. **Check the codebase first.** For claims about the current project's stack, read the actual code, configs, or dependency files.

2. **Launch an `api-researcher` agent.** For external verification, spawn a background agent:

   ```
   Agent(subagent_type: "a4:api-researcher", run_in_background: true)
   ```

   Prompt with the specific claim and ask it to verify against official documentation.

3. **Continue the interview.** Keep working while waiting. Do not transition to the next phase until all pending research results have been received and reflected.

4. **On completion.** The agent writes results to `a4/research/<label>.md`. Read it and apply the verification outcome. Add an inline `(ref: [research/<label>](research/<label>.md))` where the claim is recorded.

5. **Flag uncertainty.** When official documentation is ambiguous, tell the user and ask whether to proceed as an assumption or investigate further.

## Research-report management

Maintain the set of research reports under `a4/research/`. Derived indexes (which claims cite which report) come from grep over the body links, not a separately maintained index file.

The output schema for `api-researcher` reports is owned by the agent and embedded in its prompt — no shared schema file.
