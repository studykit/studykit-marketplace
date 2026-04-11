# Waterfall Trace Procedure

A top-down diagnosis procedure that checks each pipeline stage in order. **Stop at the first stage that fails.**

## Steps

### Step 4.1: Does an FR exist for this capability?

Search the spec's FR list for an FR that covers the failed behavior.

- If **no FR found** → **SPEC issue** (missing FR or missing platform capability).
  - Check: is this a platform capability assumed by multiple FRs? (e.g., message input, conversation display)
  - Check: was this excluded in the usecase's Excluded Ideas as "basic behavior"?
  - Recommended fix: add FR to spec.
  - **Stop here.** Do not check plan or code — there's nothing to implement without an FR.

### Step 4.2: Does an IU cover this FR?

Find the IU(s) assigned to this FR in the plan.

- If **no IU covers the FR** → **PLAN issue** (FR not mapped to any IU).
  - Recommended fix: assign FR to an existing or new IU.
  - **Stop here.**

### Step 4.3: Are the IU's instructions sufficient?

Read the IU's description, file mapping, and acceptance criteria. Check whether they adequately describe the work needed for this FR to function:

- Does the file mapping include all necessary files? (e.g., HTML entry point, component mount file)
- Does the description specify integration behavior? (e.g., "mount in DOM" vs just "wire up handlers")
- If a Shared Integration Points table exists, does it describe this IU's contribution to shared files?
- Do the acceptance criteria include an end-to-end verification scenario?

- If **IU instructions are insufficient** → **PLAN issue** (IU scope or detail gap).
  - Recommended fix: expand IU description, file mapping, or Shared Integration Points.
  - **Stop here.**

### Step 4.4: Does the code match the IU instructions?

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
| 4.1 | FR exists in spec? | No → **spec** |
| 4.2 | IU covers FR in plan? | No → **plan** |
| 4.3 | IU instructions sufficient? | No → **plan** |
| 4.4 | Code matches IU? | No → **code** |

## Recording

For each diagnosed issue, record:
- What failed (FR reference + description)
- Which trace step identified the root cause (4.1 / 4.2 / 4.3 / 4.4)
- Root cause (what's missing or wrong)
- Responsible stage (spec / plan / code)
- Recommended fix (specific and actionable)
