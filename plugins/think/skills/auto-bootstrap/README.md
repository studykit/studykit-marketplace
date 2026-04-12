# auto-bootstrap

Takes an architecture document and sets up a working development base — project structure, dependencies, build configuration, and test infrastructure. Runs autonomously with no user interaction.

## Current Notes

- **Primary file:** `plugins/think/skills/auto-bootstrap/SKILL.md`
- **Current behavior:** Runs from an `.arch.md` input, writes a bootstrap report, and may launch the `api-researcher` agent only when environment-level verification failures need source-grounded fixes.

## Workflow

```plantuml
@startuml
title auto-bootstrap Workflow

start

partition "Step 0: Input" {
  :Resolve $ARGUMENTS;
  :Read .arch.md file;
  :Extract tech stack, components,
  test strategy, external deps;
  :Read source .usecase.md;
}

partition "Step 1: Codebase Assessment" {
  if (Existing code?) then (yes)
    :Identify what exists
    vs what's missing;
    :Incremental bootstrap;
  else (no)
    :Fresh bootstrap;
  endif
}

partition "Step 2: Project Structure" {
  :Create directory structure;
  :Initialize project files;
  :Install dependencies;
  :Configure build;
  :Create minimal entry point;
}

partition "Step 3: Test Infrastructure" {
  :For each tier in Test Strategy;
  :Install test dependencies;
  :Create test runner config;
  :Write minimal passing test per tier;
  :Add npm scripts per tier;
  :Verify tier isolation;
}

partition "Step 4: Verification" {
  :Run build command;
  :Launch app;
  :Run test runners per tier;
  :Dev loop (edit → build → test);
}

partition "Step 5: Bootstrap Report" {
  :Generate report
  (environment, verified commands,
  test infra, verification results);
  :Commit bootstrap files;
}

partition "Step 6: Feedback" {
  if (Verification failures?) then (yes)
    if (Arch issue?) then (yes)
      :Record as upstream
      feedback for think-arch;
    else (environment issue)
      :Spawn research agent;
      :Apply fix from findings;
      :Re-verify;
    endif
  else (no)
  endif
}

:Suggest next step:
think-plan;

stop

@enduml
```
