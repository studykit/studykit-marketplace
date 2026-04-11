# Waterfall Trace Procedure

A top-down diagnosis procedure that checks each pipeline stage in order. **Stop at the first stage that fails.**

## Steps

### Step 4.1: Does a UC exist for this capability?

Search the usecase file's UC list for a UC that covers the failed behavior.

- If **no UC found** → **USECASE issue** (missing UC or missing platform capability).
  - Check: is this a platform capability assumed by multiple UCs? (e.g., message input, conversation display)
  - Check: was this excluded in the usecase's Excluded Ideas as "basic behavior"?
  - Recommended fix: add UC to the usecase file.
  - **Stop here.** Do not check architecture, plan, or code.

### Step 4.2: Does the architecture cover this UC?

Check the arch file for component(s) and information flows addressing this UC.

- If **no component or flow covers the UC** → **ARCH issue** (UC not addressed in architecture).
  - Recommended fix: add component assignment or information flow for this UC.
  - **Stop here.**

### Step 4.3: Does an IU cover this UC?

Find the IU(s) assigned to this UC in the plan.

- If **no IU covers the UC** → **PLAN issue** (UC not mapped to any IU).
  - Recommended fix: assign UC to an existing or new IU.
  - **Stop here.**

### Step 4.4: Are the IU's instructions sufficient?

Read the IU's description, file mapping, and acceptance criteria. Check whether they adequately describe the work needed for this UC to function:

- Does the file mapping include all necessary files? (e.g., HTML entry point, component mount file)
- Does the description specify integration behavior? (e.g., "mount in DOM" vs just "wire up handlers")
- If a Shared Integration Points table exists, does it describe this IU's contribution to shared files?
- Do the acceptance criteria include an end-to-end verification scenario?

- If **IU instructions are insufficient** → **PLAN issue** (IU scope or detail gap).
  - Recommended fix: expand IU description, file mapping, or Shared Integration Points.
  - **Stop here.**

### Step 4.5: Does the code match the IU instructions?

Read the actual implementation files. Check whether the code does what the IU says:

- Are the files listed in the file mapping created/modified as described?
- Does the component exist but is it not imported/mounted/registered?
- Is the logic correct but the wiring missing?
- Is there a runtime error visible in console/logs?

- If **code doesn't match IU** → **CODE issue** (implementation bug or integration oversight).
  - Recommended fix: specific code change (mount component, fix import, register handler, etc.).

## Summary Table

| Trace Step | Check | Failure → Stage |
|-----------|-------|----------------|
| 4.1 | UC exists in usecase file? | No → **usecase** |
| 4.2 | Architecture covers this UC? | No → **arch** |
| 4.3 | IU covers UC in plan? | No → **plan** |
| 4.4 | IU instructions sufficient? | No → **plan** |
| 4.5 | Code matches IU? | No → **code** |

## Recording

For each diagnosed issue, record:
- What failed (UC reference + description)
- Which trace step identified the root cause (4.1 / 4.2 / 4.3 / 4.4 / 4.5)
- Root cause (what's missing or wrong)
- Responsible stage (usecase / arch / plan / code)
- Recommended fix (specific and actionable)
