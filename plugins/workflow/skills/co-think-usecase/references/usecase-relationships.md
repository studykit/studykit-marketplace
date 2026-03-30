# Use Case Relationship Analysis

After 5 or more use cases have been confirmed, analyze and present the relationships between use cases. Update the working file with a **Use Case Relationships** section and update the **Use Case Diagram** with the relationships. Re-analyze whenever new use cases are added.

## What to identify

### Dependency relationships

One use case requires another to be completed first. Look for:
- Use cases that need data or state produced by another use case
- Use cases that build on a screen or feature introduced by another use case
- Use cases whose situation assumes a capability from another use case

Format: `A → B` means A must exist before B can work.

In the PlantUML diagram, represent these as `<<include>>` relationships where appropriate.

### Reinforcement relationships

One use case enhances or strengthens another but isn't strictly required. Look for:
- Use cases that improve reliability of another (e.g., monitoring reinforces data pipelines)
- Use cases that personalize or extend a base feature
- Use cases that fill gaps in another use case's coverage

In the PlantUML diagram, represent these as `<<extend>>` relationships where appropriate.

### Use case groups

Cluster use cases by the area they serve. A use case can appear in multiple groups if it spans areas.

## How to present

> Here are the relationships between the use cases so far:
>
> **Dependencies:** UC-10 → UC-1 (need holdings data for dashboard), UC-1 → UC-2 (dashboard needed before embedding calendar)
>
> **Reinforcements:** UC-6 → UC-4, UC-5, UC-10 (monitoring reinforces all pipelines)
>
> **Groups:**
> | Group | Use Cases | Description |
> |-------|-----------|-------------|
> | Dashboard | UC-1, UC-2, UC-9 | Main view |
> | News | UC-4, UC-5 | Timeline |
>
> Does this look right?

After the user confirms or revises, update the working file and the Use Case Diagram.
