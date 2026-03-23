# Story Splitting Guide

After a Job Story is confirmed, evaluate whether it is too large. A story is too large when it contains **multiple distinct actions**, **serves more than one outcome**, or **spans unrelated situations**.

## Signs a story needs splitting

- The "I want to" clause has "and" connecting separate actions
- The "so I can" clause describes two or more unrelated outcomes
- The "When" clause covers multiple distinct scenarios that don't always occur together
- Implementing the story would require touching many independent parts of the system

## How to split

When a large story is detected, flag it:

> This story feels like it's doing two things at once. Let me try splitting it:
>
> **Original:**
> **When** I receive a customer complaint, **I want to** categorize the issue and assign it to the right team and draft a response, **so I can** resolve it quickly and track patterns.
>
> **Split into:**
>
> **4a.** **When** I receive a customer complaint, **I want to** categorize the issue and assign it to the right team, **so I can** ensure the right people start working on it immediately.
>
> **4b.** **When** a complaint has been categorized, **I want to** draft a response based on the category, **so I can** acknowledge the customer within minutes instead of hours.
>
> **4c.** **When** complaints are resolved over time, **I want to** see patterns by category, **so I can** fix recurring root causes.
>
> Does this split make sense? Want to adjust any of these?

## Splitting rules

- Each child story must be independently valuable — it should make sense on its own even if the others aren't built
- Preserve the parent story's numbering with suffixes (3a, 3b, 3c) to maintain traceability
- Ask the user to confirm the split before counting them as separate stories
- If the user prefers to keep a story combined, respect that — note it as a "composite story" and move on
