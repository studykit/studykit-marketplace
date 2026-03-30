# Use Case Splitting Guide

After a Use Case is confirmed, evaluate whether it is too large. A use case is too large when it contains **multiple distinct goals**, **serves more than one outcome**, or **spans unrelated situations**.

## Signs a use case needs splitting

- The flow has steps that serve independent goals
- The expected outcome describes two or more unrelated results
- The situation covers multiple distinct scenarios that don't always occur together
- Different actors are involved in different parts of the flow
- Implementing it would require touching many independent parts of the system

## How to split

When a large use case is detected, flag it:

> This use case feels like it's covering multiple goals. Let me try splitting it:
>
> **Original:**
> **UC-4. Handle customer complaint**
> - **Actor:** Support agent
> - **Goal:** Resolve complaint and track patterns
> - **Situation:** A customer complaint arrives via email
> - **Flow:**
>   1. Read the complaint
>   2. Categorize the issue
>   3. Assign to the right team
>   4. Draft a response
>   5. Send acknowledgment to customer
>   6. Log for pattern tracking
> - **Expected Outcome:** Complaint is assigned, customer is acknowledged, and patterns are trackable
>
> **Split into:**
>
> **UC-4a. Triage customer complaint**
> - **Actor:** Support agent
> - **Goal:** Get the complaint to the right team quickly
> - **Situation:** A customer complaint arrives via email
> - **Flow:**
>   1. Read the complaint
>   2. Categorize the issue
>   3. Assign to the right team
> - **Expected Outcome:** The right team starts working on it immediately
>
> **UC-4b. Acknowledge customer complaint**
> - **Actor:** Support agent
> - **Goal:** Let the customer know their complaint is being handled
> - **Situation:** A complaint has been categorized and assigned
> - **Flow:**
>   1. Review the category and assigned team
>   2. Draft a response based on the category
>   3. Send acknowledgment to customer
> - **Expected Outcome:** Customer receives acknowledgment within minutes
>
> **UC-4c. Track complaint patterns**
> - **Actor:** Support lead
> - **Goal:** Identify recurring issues to fix root causes
> - **Situation:** Complaints have been resolved over time
> - **Flow:**
>   1. View complaints grouped by category
>   2. Identify categories with high frequency
>   3. Drill into specific complaints for details
> - **Expected Outcome:** Recurring root causes are visible and actionable
>
> Does this split make sense? Want to adjust any of these?

## Splitting rules

- Each child use case must be independently valuable — it should make sense on its own even if the others aren't built
- Preserve the parent use case's numbering with suffixes (4a, 4b, 4c) to maintain traceability
- Each child must have its own actor, goal, situation, flow, and expected outcome
- Ask the user to confirm the split before counting them as separate use cases
- If the user prefers to keep a use case combined, respect that — note it as a "composite use case" and move on
