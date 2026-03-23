# Story Relationship Analysis

After 5 or more stories have been confirmed, analyze and present the relationships between stories. Update the working file with a **Story Relationships** section after the Job Stories section. Re-analyze whenever new stories are added.

## What to identify

### Dependency relationships

One story requires another to be completed first. Look for:
- Stories that need data produced by another story
- Stories that build on a screen or feature introduced by another story
- Stories whose "When" clause assumes a capability from another story

Format: `A → B` means A must exist before B can work.

### Reinforcement relationships

One story enhances or strengthens another but isn't strictly required. Look for:
- Stories that improve reliability of another (e.g., monitoring reinforces data pipelines)
- Stories that personalize or extend a base feature
- Stories that fill gaps in another story's coverage

### Story groups

Cluster stories by the area they serve. A story can appear in multiple groups if it spans areas.

## How to present

> Here are the relationships between the stories so far:
>
> **Dependencies:** 10 → 1 (need holdings data for dashboard), 1 → 2 (dashboard needed before embedding calendar)
>
> **Reinforcements:** 6 → 4, 5, 10 (monitoring reinforces all pipelines)
>
> **Groups:**
> | Group | Stories | Description |
> |-------|---------|-------------|
> | Dashboard | 1, 2, 9 | Main view |
> | News | 4, 5 | Timeline |
>
> Does this look right?

After the user confirms or revises, update the working file.
