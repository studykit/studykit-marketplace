# PlantUML Compose Skill Map

Use this file first to choose the right reference document for the request.

## Mode Hints

| User intent | Mode |
|---|---|
| "draw", "create", "generate", "make a diagram", "add to markdown", "insert into file" | `create` |
| "syntax", "how do I write", "example for", "reference" | `reference` |
| "check", "validate", "lint", "syntax check", "is this valid", "why does this fail", "invalid PlantUML" | `check` |

## Primary Diagram References

| Request cues | Reference file |
|---|---|
| activity, workflow, flowchart, process flow, swimlane, decision, fork, conditional | `activity-diagram.md` |
| sequence, message flow, interaction, lifeline, request/response | `sequence-diagram.md` |
| class, inheritance, interface, association, composition, aggregation | `class-diagram.md` |
| component, module, service dependency, port, connector | `component-diagram.md` |
| deployment, node, artifact, infrastructure, device, server topology | `deployment-diagram.md` |
| object, instance snapshot, runtime object state | `object-diagram.md` |
| state, state machine, transition, lifecycle, composite state | `state-diagram.md` |
| use case, actor, system boundary | `use-case-diagram.md` |
| timing, waveform, signal timing, clock, time constraint | `timing-diagram.md` |
| ER, entity relationship, database schema, cardinality | `er-diagram.md` |
| gantt, timeline, milestone, task schedule | `gantt-diagram.md` |
| mind map, brainstorm tree, idea map | `mindmap-diagram.md` |
| WBS, work breakdown structure, task hierarchy | `wbs-diagram.md` |
| network, nwdiag, IP, subnet, VLAN, rack | `network-diagram.md` |
| JSON, YAML, data tree, structured payload | `json-yaml.md` |
| salt, archimate, ditaa, regex, EBNF, wireframe | `other-diagrams.md` |
| C4, system context, container, component (C4), deployment (C4), dynamic (C4) | `c4-diagram.md` |

## Supplemental References

| Need | Reference file |
|---|---|
| bold/italic text, tables, links, tooltips, emojis, math, HTML, note formatting | `creole-and-links.md` |
| logos, cloud icons, AWS/Azure icons, stdlib sprites, custom sprites | `sprites.md` |

## Optional Follow-ups

Load these only when the request needs less-common or specialized syntax:

| Primary reference | Advanced file |
|---|---|
| `activity-diagram.md` | `activity-diagram-advanced.md` |
| `sequence-diagram.md` | `sequence-diagram-advanced.md` |
| `class-diagram.md` | `class-diagram-advanced.md` |
| `gantt-diagram.md` | `gantt-diagram-advanced.md` |
| `timing-diagram.md` | `timing-diagram-advanced.md` |
| `c4-diagram.md` | `c4-diagram-macros.md` |
| `sprites.md` | `sprites-names.md` |

## Composition Rules

1. Pick one primary reference first.
2. Add `creole-and-links.md` if the request needs rich text, links, formulas, or complex notes.
3. Add `sprites.md` if the request needs icons or logos.
4. For C4 diagrams with logos, load both `c4-diagram.md` and `sprites.md`.
5. In `reference` mode, answer from the selected docs without writing files.
6. In `create` mode, validate after any file write.
