# Parallel Execution

Procedure for implementing multiple units in parallel using git worktrees. This reference is read by the think-code orchestrator when a phase contains parallelizable units.

## 1. When to Parallelize

Check the Implementation Order table in the plan. Units in the same phase marked "Can Parallelize: Yes" are candidates.

Before parallelizing, verify:
- The units have no mutual dependencies (they shouldn't if the plan is correct, but verify)
- Each unit's file mappings don't overlap (different units shouldn't modify the same files)

If file mappings overlap, fall back to sequential execution to avoid merge conflicts.

## 2. Spawn Parallel Agents

For each parallelizable unit:

1. Create tasks in TaskList:
   - `"IU-N: spawn worktree agent"` → `in_progress`
   - `"IU-N: update plan file"` → `pending` (blocked by spawn task)

2. Mark each IU as `IN_PROGRESS` in the plan file.

3. Spawn agents in a **single message** (all Agent calls in one turn for true parallelism):

   ```
   Agent(
     subagent_type: "coder",
     isolation: "worktree",
     name: "coder-IU-N",
     prompt: <IU details + codebase context + recent completion notes>
   )
   ```

   Each agent receives:
   - The specific IU section from the plan
   - Codebase context from Step 0 (project structure, conventions, test framework/runner)
   - Completion notes from recently completed IUs
   - The test framework and runner command

   Agents work independently — no shared state during execution.

## 3. Merge Procedure

After all parallel agents complete:

1. **Collect results** — gather each agent's result (success with completion note, or deviation report).

2. **Merge successful worktrees** — for each successful agent, merge its worktree branch into the working branch:
   ```bash
   git merge <worktree-branch> --no-ff -m "merge(IU-N): <short description>"
   ```
   Merge sequentially, one at a time.

3. **Handle merge conflicts** — if conflicts occur:
   - For non-overlapping files: resolve automatically
   - For true conflicts in the same file: this shouldn't happen if file mappings don't overlap (checked in step 1). If it does, resolve manually and record in the completion notes.

4. **Run the full test suite** — after all merges, run the complete test suite to verify integration:
   ```bash
   # Use the project's test runner without path filter
   npm test
   pytest
   ./gradlew test
   ```

5. **Handle integration failures** — if the full suite fails after merge:
   - Identify which test(s) failed and which units they relate to
   - Diagnose whether the failure is due to unit interaction or a pre-existing issue
   - Report to the user with diagnosis

## 4. Deviation Handling — Dependency-Aware Propagation

If one agent reports a major deviation:

1. **Other agents with no dependency on the deviated unit continue.** Do not cancel them.

2. **Merge successful units first.** Handle the deviation after all agents complete and successful results are merged.

3. **Block propagation**: walk the dependency graph from the deviated unit forward. Mark all downstream IUs as `BLOCKED` in TaskList:
   - These IUs cannot be scheduled in future phases until the deviation is resolved
   - Example: IU-3 deviates → IU-6 depends on IU-3 → IU-6 is BLOCKED. IU-4 has no dependency on IU-3 → IU-4 continues.

4. **Report deviation to user** after all parallel agents complete — not immediately when one fails.

## 5. Plan File Updates

After merge and integration test:

1. **Update all parallel units** in a single edit pass:
   - Set `**Status:** DONE` for successful units
   - Write each unit's `**Completion Note:**`
   - Write `**Deviation Note:**` for deviated units and reset their Status to `TODO`

2. **Commit the plan update** separately from the code commits:
   ```
   think-code: update plan status for Phase N

   - IU-3: DONE
   - IU-4: DONE
   - IU-5: DEVIATION (reset to TODO)
   ```

This keeps code commits (one per IU, made by agents) separate from plan tracking commits (made by orchestrator).
