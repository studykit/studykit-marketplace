---
type: architecture
pipeline: co-think
topic: "interactive agent/prompt use cases"
date: 2026-03-29
status: final
revision: 4
last_revised: 2026-03-29
tags: []
---
# Architecture: interactive agent/prompt use cases
> Source: [2026-03-27-1500-agent-orchestrator.story.md](./2026-03-27-1500-agent-orchestrator.story.md), [2026-03-28-1030-agent-orchestrator.requirement.md](./2026-03-28-1030-agent-orchestrator.requirement.md), [2026-03-29-1500-agent-orchestrator.domain.md](./2026-03-29-1500-agent-orchestrator.domain.md)

## Overview
The agent orchestrator extends Claude Code's interactive session model with a two-level session hierarchy. Five components collaborate through a shared file-based manifest (`session-tree.json`) and Claude Code's hook infrastructure. The **Session Manager** in the main session spawns child sessions in iTerm2 tabs. The **Child Session Bootstrap** hook initializes each child with context and skill injection. The **Result Collector** hooks register deliverables and handle termination. The **Session Monitor** hook on the main session side watches for manifest changes and injects status updates. The **History Investigator** sub-agent reads past child session transcripts on demand.

All inter-session communication flows through `session-tree.json` — no direct IPC, no sockets, no shared memory. Hooks read and write the manifest; the main session LLM and child session LLM never communicate directly.

### Hook Communication Model

Claude Code hooks receive session metadata via **stdin JSON** (including `session_id` and `transcript_path`) and inject information back into the conversation via **stdout** or a structured `additionalContext` JSON field. Environment variables (`$SESSION_TREE`, etc.) supplement stdin for cross-session context that hooks cannot derive from their own session alone.

## Component Diagram

```plantuml
@startuml
skinparam componentStyle rectangle

package "Main Session" {
  component [Session Manager] as SM
  component [Session Monitor] as MO
  component [History Investigator] as HI
}

package "Child Session (per iTerm2 tab)" {
  component [Child Session Bootstrap] as CB
  component [Result Collector] as RC
}

database "session-tree.json" as ST

SM --> ST : reads/writes child entries
SM --> CB : launches iTerm2 tab
CB --> ST : reads own entry,\nwrites transcriptPath, pid
RC --> ST : registers result files,\nupdates status
MO --> ST : watches for changes
MO --> SM : injects status updates
SM --> HI : spawns for investigation
HI --> ST : reads transcriptPath
@enduml
```

**Session Manager** — orchestration logic in the main session. Creates child entries in session-tree.json, launches iTerm2 tabs, and coordinates investigation requests. iTerm2 tab creation uses `it2` CLI (iTerm2 shell integration). Spawn is triggered via the `chat` skill, which receives the main session's `session_id` through the `${CLAUDE_SESSION_ID}` skill template variable.

**Child Session Bootstrap** — SessionStart hook on the child session. Locates session-tree.json via the `$SESSION_TREE` environment variable, reads its own entry by matching `session_id` from stdin JSON against `id`, injects context (reference files, summary) and skill into the conversation via stdout, then writes back its transcriptPath and pid.

**Result Collector** — PostToolUse and SessionEnd hooks on the child session. PostToolUse hook receives `tool_input.file_path` via stdin JSON and appends all Write/Edit file paths to `modifiedFiles` without filtering. SessionEnd hook marks the session as terminated. Both locate session-tree.json via the `$SESSION_TREE` environment variable.

**Session Monitor** — FileChanged hook on the main session (matcher: `session-tree.json`). Detects session-tree.json modifications and injects child session status changes (termination, new result files) into the main session's conversation context via stdout.

**History Investigator** — sub-agent spawned by the main session on demand. Reads a child session's transcript and result files, returns a summary.

## Components

### Session Manager

**Responsibility:** Core orchestration — spawns child sessions, maintains session-tree.json, serves as the entry point for all session lifecycle operations in the main session.

**Data store:** Yes — `session-tree.json` at `.claude/sessions/<main-conversation-id>/`. Created lazily on first child spawn — the directory and manifest do not exist until the user requests the first child session.

#### DB Schema

```plantuml
@startuml
entity "MainSessionRecord" as main {
  *id : text <<PK>> -- Claude session ID
  --
  *name : text
}

entity "ChildSessionRecord" as child {
  *id : text <<PK>> -- Claude session ID
  --
  *topic : text
  *status : text
  *createdAt : timestamp
  pid : number
  skill : text
  transcriptPath : text
  modifiedFiles : text[]
  resultFiles : text[]
  referenceFiles : text[]
  additionalContext : text
}

main ||--o{ child : contains
@enduml
```

The session-tree.json file contains one MainSessionRecord and zero or more ChildSessionRecords. This is a single JSON file, not a relational database — the ERD captures the logical structure.

- **MainSessionRecord**: identifies the main session. `name` is user-assigned for search/identification.
- **ChildSessionRecord**: one per spawned child session. `id` is the PK — the Claude session ID, generated at spawn time and used as the `--session-id` for the child Claude Code process. `status` is `pending` (spawned, bootstrap not yet complete), `active` (bootstrap complete, session running), `terminated`, `crashed`, or `failed_to_start`. `pid` is the child Claude Code process ID, recorded by the Child Session Bootstrap for crash detection. `transcriptPath` is initially null, filled by the Child Session Bootstrap hook. `modifiedFiles` accumulates all file paths written or edited during the session — the Result Collector's PostToolUse hook appends every Write/Edit target without filtering. `resultFiles` accumulates key deliverable paths registered explicitly by LLM nudge (with user approval) or direct user instruction. `referenceFiles` and `additionalContext` capture the injected context from the main session at spawn time.

#### Information Flow

##### Story: STORY-9 — Spawn a dedicated child session

```plantuml
@startuml
participant "User" as U
participant "chat skill" as SK
participant "Session Manager" as SM
participant "session-tree.json" as ST
participant "iTerm2\n(it2 CLI)" as IT
participant "Child Session Bootstrap" as CB
participant "Child Session" as CS

alt Natural language trigger
  U -> SM : request spawn (topic, skill?)
else Skill trigger
  U -> SK : /chat
  SK -> SM : invoke with topic, skill
end

SM -> ST : write new child entry\n(id, topic, skill,\ncontext, status=active)
SM -> IT : it2 CLI:\nSESSION_TREE=<path> claude --session-id <uuid>\n--append-system-prompt-file interactive-child.txt
IT -> CS : new Claude Code session starts
CS -> CB : SessionStart hook fires\n(stdin: {session_id, transcript_path, ...})
CB -> CB : read $SESSION_TREE env var
CB -> ST : read own child entry\n(match by session_id from stdin)
CB -> CS : inject context\n+ invoke skill (via stdout / additionalContext)
CB -> ST : write transcriptPath, pid
U -> CS : interact directly
@enduml
```

The spawn flow has two entry points: (1) natural language — the LLM suggests spawning and the user approves, (2) the `chat` skill — the user invokes `/chat` directly. Both paths converge at the Session Manager, which generates a child session ID (UUID), writes the entry to session-tree.json with `id` set to the generated UUID (Claude session ID), and launches an iTerm2 tab via `it2` CLI with `SESSION_TREE=<path> claude --session-id <uuid> --append-system-prompt-file interactive-child.txt`. The child session's SessionStart hook receives `session_id` and `transcript_path` via stdin JSON, reads the `$SESSION_TREE` environment variable to locate session-tree.json, finds its own entry by matching `session_id` against `id`, injects the context (and skill if specified) via stdout, and writes back its transcriptPath and pid to the manifest.

##### Story: STORY-15 — Skill injection at child session startup

Skill injection is part of the STORY-9 spawn flow. The Session Manager includes the skill name in the child entry. The Child Session Bootstrap reads it and invokes the skill (e.g., `/workflow:co-think-requirement`) as part of context injection. No separate information flow — it's embedded in the bootstrap sequence above.

### Child Session Bootstrap

**Responsibility:** Initializes a newly spawned child session with context from the session tree and optionally invokes a skill.

**Data store:** No

**Identification mechanism:** The child session is launched with `SESSION_TREE=<path>` environment variable and `--session-id <uuid>` CLI flag. The SessionStart hook receives `session_id` via stdin JSON, reads `$SESSION_TREE` to locate the manifest, and matches its entry by `session_id` against `id`. This avoids any indirect identification (marker files, iTerm2 session IDs) — the child knows exactly who it is and where to look.

#### Information Flow

##### Story: STORY-9 — Spawn a dedicated child session

See Session Manager's STORY-9 sequence above. The Bootstrap is the child-side participant that reads context from session-tree.json and injects it.

### Result Collector

**Responsibility:** Registers result files during the child session's lifetime and handles termination status updates.

**Data store:** No (writes to session-tree.json owned by Session Manager)

#### Information Flow

##### Story: STORY-10 — Automated information exchange between sessions

```plantuml
@startuml
participant "Child Session LLM" as CS
participant "Result Collector\n(PostToolUse hook)" as RC
participant "session-tree.json" as ST
participant "Session Monitor\n(FileChanged hook)" as MO
participant "Main Session" as MS

CS -> CS : Write tool creates a file
CS -> RC : PostToolUse hook fires
RC -> ST : append file path\nto children[].modifiedFiles
ST -> MO : FileChanged detected
MO -> ST : read updated entry
MO -> MS : inject status update\n(new modified file tracked)
@enduml
```

The PostToolUse hook on the child session receives `tool_name` and `tool_input` via stdin JSON. When the tool is `Write` or `Edit`, it reads `$SESSION_TREE` to locate session-tree.json, looks up its own child entry by `session_id`, and appends `tool_input.file_path` to `modifiedFiles`. No filtering — all file modifications are tracked. The main session's FileChanged hook picks up the change.

Deliverable registration is separate from file tracking. The child session LLM may suggest registering a file as a key deliverable (nudge) when it judges the file to be a primary output of the session — not incidental edits. Upon user approval, or when the user directly instructs, the LLM writes the file path to `resultFiles` in session-tree.json.

##### Story: STORY-12 — Child session result file accessible to main session

```plantuml
@startuml
participant "User" as U
participant "Child Session" as CS
participant "Result Collector\n(SessionEnd hook)" as RC
participant "session-tree.json" as ST
participant "Session Monitor\n(FileChanged hook)" as MO
participant "Main Session" as MS

U -> CS : ends session (Ctrl+D or exit)
CS -> RC : SessionEnd hook fires
RC -> ST : update status to terminated
ST -> MO : FileChanged detected
MO -> ST : read terminated entry\n(topic, modifiedFiles, resultFiles)
MO -> MS : inject termination info\n+ modified/result file paths
@enduml
```

On child session termination, the SessionEnd hook updates the child's status to `terminated`. The main session's FileChanged hook detects this and injects the termination notification with modified file paths and result file paths into the main session's conversation context.

### Session Monitor

**Responsibility:** Watches session-tree.json for changes on the main session side and injects relevant updates into the main session's conversation context.

**Data store:** No

#### Information Flow

##### Story: STORY-10 — Automated information exchange between sessions

See Result Collector's STORY-10 sequence above. The Session Monitor is the main-session-side participant that detects FileChanged events on session-tree.json.

##### Story: STORY-12 — Child session result file accessible to main session

See Result Collector's STORY-12 sequence above. The Session Monitor detects the termination status change and injects it into the main session.

### History Investigator

**Responsibility:** Reads and summarizes past child session transcripts and result files on demand.

**Data store:** No

**Transcript access:** Reads the `.jsonl` transcript file directly via the Read tool. For large transcripts, uses offset/limit to read in chunks. No session resume — read-only access to the raw file.

#### Information Flow

##### Story: STORY-13 — Child session conversation history investigation

```plantuml
@startuml
participant "User" as U
participant "Session Manager" as SM
participant "session-tree.json" as ST
participant "History Investigator\n(sub-agent)" as HI
participant "Transcript file" as TF
participant "Result files" as RF

U -> SM : ask about past child session
SM -> ST : look up child entry\n(by topic or ID)
SM -> SM : check transcript size
SM -> HI : spawn sub-agent with\ntranscriptPath + resultFiles
HI -> TF : read .jsonl via Read tool\n(offset/limit for large files)
HI -> RF : read result files
HI -> SM : return summary
SM -> U : present summary
@enduml
```

The user asks about a past child session. The Session Manager finds the child entry in session-tree.json, checks the transcript size, and either reads directly or spawns a sub-agent (History Investigator) to read and summarize the transcript and result files.

## Concurrency and Error Handling

### File locking

All reads and writes to session-tree.json must be wrapped in an exclusive file lock to prevent update-lost anomalies. The lock scope covers the entire read-modify-write cycle. The implementation uses Python's `fcntl.flock()` with `LOCK_SH` (shared) and `LOCK_EX` (exclusive) on a `.lock` file adjacent to session-tree.json:

```python
import fcntl

# shared lock for reads
with open(lock_path) as lf:
    fcntl.flock(lf, fcntl.LOCK_SH)
    data = json.loads(path.read_text())
    fcntl.flock(lf, fcntl.LOCK_UN)

# exclusive lock for read-modify-write
with open(lock_path) as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    data = json.loads(path.read_text())
    transform(data)
    path.write_text(json.dumps(data, indent=2) + "\n")
    fcntl.flock(lf, fcntl.LOCK_UN)
```

This applies to all components that write to session-tree.json: Session Manager, Child Session Bootstrap, and Result Collector. The shared library (`hooks/lib/session_tree.py`) exposes `st_read()` for shared-lock reads and `st_write(transform)` for exclusive-lock read-modify-write operations.

### Crash detection

If a child session crashes (process killed, terminal closed abnormally), the SessionEnd hook never fires and the entry remains `active`. The Session Monitor detects this by checking `kill -0 <pid>` against the child's recorded PID. When the process is no longer alive and status is still `active`, the Session Monitor updates it to `crashed` and injects a notification into the main session.

The Child Session Bootstrap records `os.getppid()` (the parent PID, i.e., the Claude Code process) into the child entry during initialization. Since the hook runs as a child process of the Claude Code process, `os.getppid()` points to the Claude Code process — if this process dies, the Session Monitor's `kill -0` check (via `os.kill(pid, 0)`) will fail.

### Bootstrap handshake timeout

Covers the case where the child process starts but the Bootstrap hook never completes — status remains `pending`. The Session Monitor checks for entries where `status == "pending"` AND `createdAt` is older than 30 seconds. When detected, status is updated to `failed_to_start` and a notification is injected into the main session.

This is distinct from crash detection: crash detection checks `active` entries with a recorded PID, while handshake timeout checks `pending` entries where the Bootstrap never ran.

## Consistency Check

### Cross-diagram consistency

All five components (Session Manager, Child Session Bootstrap, Result Collector, Session Monitor, History Investigator) appear in both the component diagram and at least one sequence diagram. session-tree.json is the shared data store referenced consistently across all diagrams.

### Domain model coverage

| Domain Concept | Component(s) | Notes |
|---|---|---|
| Main Session | Session Manager | Main session is the execution context for Session Manager, Session Monitor, and History Investigator |
| Child Session | Child Session Bootstrap, Result Collector | Child session is the execution context; Bootstrap initializes it, Result Collector manages its outputs |
| Session Tree | Session Manager (data store) | session-tree.json schema matches the domain model's SessionTree concept |
| Interactive Prompt | Child Session Bootstrap | Loaded via `--append-system-prompt-file` at spawn; Bootstrap adds context on top |
| Injected Skill | Child Session Bootstrap | Skill name stored in session-tree.json, invoked by Bootstrap during initialization |

All five domain concepts are housed in at least one component.

**Cross-component relationships:**
- Session Tree → Main Session (1:1): Session Manager creates exactly one MainSessionRecord per session-tree.json
- Main Session → Child Session (1:0..*): Session Manager creates ChildSessionRecords; no nesting enforced by the two-level design
- Child Session → Interactive Prompt (1:1): enforced by the spawn command always including `--append-system-prompt-file interactive-child.txt`
- Child Session → Injected Skill (1:0..1): `skill` field in ChildSessionRecord is nullable
- Injected Skill overrides Interactive Prompt on conflict: this is a behavioral rule within the prompt content, not an architectural flow — the Interactive Prompt already contains the precedence rule ("Skills override this prompt")

**State transitions:**
- Child Session `pending → active`: managed by Child Session Bootstrap's SessionStart hook — confirms the child process started and writes back transcriptPath and pid
- Child Session `active → terminated`: managed by Result Collector's SessionEnd hook writing to session-tree.json
- Child Session `active → crashed`: detected by Session Monitor via `kill -0 <pid>` when the child process is no longer alive and SessionEnd was never called
- Child Session `pending → failed_to_start`: detected by Session Monitor when status is still `pending` and `createdAt` is older than 30 seconds (bootstrap never completed)

### Story coverage

| Story | Sequence Diagram(s) | Component(s) Involved |
|---|---|---|
| STORY-7 | *(no diagram — behavioral prompt, already implemented as FR-16)* | Child Session Bootstrap loads the Interactive Prompt via `--append-system-prompt-file` during STORY-9 spawn flow |
| STORY-9 | Session Manager / STORY-9 | Session Manager, Child Session Bootstrap |
| STORY-10 | Result Collector / STORY-10 | Result Collector, Session Monitor |
| STORY-12 | Result Collector / STORY-12 | Result Collector, Session Monitor |
| STORY-13 | History Investigator / STORY-13 | History Investigator, Session Manager |
| STORY-14 | *(no diagram — behavioral rule in Interactive Prompt, FR-16)* | — |
| STORY-15 | *(embedded in STORY-9 spawn flow)* | Session Manager, Child Session Bootstrap |

STORY-7 and STORY-14 are behavioral rules delivered by the Interactive Prompt (FR-16, already implemented). They require no architectural components — the prompt file is loaded at child session startup as part of the STORY-9 spawn flow. All orchestrator stories (STORY-9 through STORY-15) have sequence diagram coverage.

### Gaps identified and resolved

Post-review fixes applied:
1. **STORY-7 coverage**: Added to story coverage table. No sequence diagram needed — it's a behavioral prompt (FR-16, already implemented). The architecture ensures it's loaded during the STORY-9 spawn flow.
2. **STORY-13 participant naming**: Changed "Main Session LLM" to "Session Manager" in the sequence diagram for consistency with the component diagram.
3. **Component diagram read path**: Session Manager arrow updated to "reads/writes child entries" to reflect that it both writes (spawn) and reads (investigation) from session-tree.json.
4. **InjectedSkill override relationship**: Noted as a behavioral rule within the Interactive Prompt content, not an architectural information flow.
5. **Crash detection**: Added `pid` field to ChildSessionRecord and `crashed` status. Session Monitor checks process liveness via `kill -0`.
6. **Concurrent writes**: All session-tree.json writes wrapped in Python `fcntl.flock(LOCK_EX)` exclusive lock covering the full read-modify-write cycle to prevent update-lost.
7. **Bootstrap handshake timeout**: Added `failed_to_start` status for entries where bootstrap never completes (pid remains null after 30s).
8. **Result tracking redesign**: Removed `resultPatterns`. PostToolUse hook now tracks all Write/Edit file paths in `modifiedFiles` without filtering. `resultFiles` is reserved for key deliverables registered explicitly via LLM nudge (with user approval) or direct user instruction.

## Interview Transcript
<details>
<summary>Full Q&A</summary>

### Round 1
**Q:** (self) What are the natural component boundaries given the file-based, hook-driven architecture?
**A:** Five components emerge from the FR processing steps: Session Manager (main session orchestration + data store), Child Session Bootstrap (SessionStart hook), Result Collector (PostToolUse + SessionEnd hooks), Session Monitor (FileChanged hook on main session), History Investigator (sub-agent for transcript reading). The boundaries align with hook event ownership — each hook-based component handles one or two specific events.

### Round 2
**Q:** (self) Should session-tree.json be its own component or a data store owned by Session Manager?
**A:** Data store owned by Session Manager. Multiple components read/write it, but Session Manager is responsible for creating and maintaining its structure. Other components (Bootstrap, Result Collector) write specific fields but don't own the schema.

### Round 3
**Q:** (self) Is the Session Monitor a separate component or part of Session Manager?
**A:** Separate. Session Monitor is a FileChanged hook — a distinct execution context that fires asynchronously. Session Manager is the LLM-driven orchestration logic. They run in the same main session but have different triggers and responsibilities.

### Round 4
**Q:** (self) How does the Child Session Bootstrap identify its own entry in session-tree.json?
**A:** Resolved. The main session launches the child with `SESSION_TREE=<path> claude --session-id <uuid>`. The SessionStart hook receives `session_id` via stdin JSON and reads `$SESSION_TREE` to locate session-tree.json. It matches its entry by `session_id`. Two inputs: stdin JSON for identity, environment variable for manifest location.

### Round 5
**Q:** (self) Does STORY-14 (user controls termination) need an architectural component?
**A:** No. STORY-14 is a behavioral rule already implemented in the Interactive Prompt (FR-16). No architectural component needed — the LLM follows the prompt instructions.

### Round 6
**Q:** (self) Should the Result Collector's PostToolUse hook and SessionEnd hook be separate components?
**A:** No. They serve the same responsibility (managing child session outputs) and run in the same execution context (child session). One component with two hook implementations.

</details>

<!-- references -->
[STORY-7]: https://github.com/studykit/studykit-plugins/issues/7
[STORY-9]: https://github.com/studykit/studykit-plugins/issues/9
[STORY-10]: https://github.com/studykit/studykit-plugins/issues/10
[STORY-12]: https://github.com/studykit/studykit-plugins/issues/12
[STORY-13]: https://github.com/studykit/studykit-plugins/issues/13
[STORY-14]: https://github.com/studykit/studykit-plugins/issues/14
[STORY-15]: https://github.com/studykit/studykit-plugins/issues/15
[FR-16]: https://github.com/studykit/studykit-plugins/issues/16
[FR-17]: https://github.com/studykit/studykit-plugins/issues/17
[FR-18]: https://github.com/studykit/studykit-plugins/issues/18
[FR-19]: https://github.com/studykit/studykit-plugins/issues/19
