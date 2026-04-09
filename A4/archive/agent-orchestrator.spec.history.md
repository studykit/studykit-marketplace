---
type: session-history
source: agent-orchestrator.spec.md
---

### Session Close — 2026-04-06 20:00

#### Revisions This Session
- Revision 2: Architecture section written (11 components), notification architecture redesigned, review issues resolved

#### Decisions Made
- Architecture: 11 components identified — SessionTreeStore, SpawnOrchestrator, iTerm2Launcher, SessionStartHook, SessionEndHook, SessionMonitorHook, ContextDriftHook, NotificationRelayHook, RegisterResultCommand, SessionListCommand, ChatSkill
- PromptGenerator absorbed into SpawnOrchestrator as `generate_prompt()` function (not separate component)
- `/register-result` and `/sessions` implemented as Commands (skill with `disable-model-invocation: true` + shell injection), not Skills — thin layer, no LLM reasoning needed
- `/chat` remains a Skill — LLM reasoning required for multi-step conversation
- Notification architecture: 2-stage pipeline — FileChanged hooks write to notification queue + `systemMessage` for user visibility, NotificationRelayHook (UserPromptSubmit) reads queue and injects `additionalContext` for Claude. FileChanged hooks do NOT support `additionalContext`.
- SessionStartHook resume logic: `pending` → new session, everything else → resume (covers terminated, crashed, stale active/resumed)
- SpawnOrchestrator resume dispatch: checks pid alive for active/resumed. Stale active/resumed (pid dead) → resume. `failed_to_start` → offer new session creation (not blocked, not resumed)
- ContextDriftHook matcher: omit or `".*"` (regex on basename, matches all files), script-side filtering against referenceFiles
- Notification queue: separate schemas for main session (SessionMonitorHook) and child session (ContextDriftHook), cursor-based delivery tracking (`notifications.cursor`)
- `${CLAUDE_SKILL_DIR}` for script paths in SKILL.md (not `${CLAUDE_PLUGIN_ROOT}` — broken in SKILL.md per GitHub #9354)

#### Change Log

| Section | Change | Reason | Source |
|---------|--------|--------|--------|
| Architecture | Full section written: 11 components, component diagram, sequence diagrams, interface contracts | Open Item from rev 1 | co-think interview |
| Architecture | PromptGenerator → SpawnOrchestrator internal function | Simple enough for one function | co-think interview |
| Architecture | `/register-result`, `/sessions` as Commands (not Skills) | Thin layer — no LLM reasoning needed | co-think interview |
| Overview | Hook notification mechanism → 2-stage notification pipeline | FileChanged hooks do not support additionalContext (verified against official docs) | co-think interview + spec-review rev 2 |
| FR-6 | Matcher: `".*"` or omitted (was `"\.md$\|\.py$\|..."`) | Reference files can be any type; broad matcher + script-side filtering | co-think interview |
| FR-6, FR-7 | Notification delivery via queue + systemMessage (was stdout additionalContext) | FileChanged hook limitation | co-think interview |
| Architecture | NotificationRelayHook added (UserPromptSubmit) | Injection stage for 2-stage notification pipeline | co-think interview |
| Architecture | Notification queue schema defined (main + child, separate) | 3 components share queue file — schema needed | co-think interview + spec-review full-2 |
| Architecture | Cursor-based delivery tracking (notifications.cursor) | Crash-safe, avoids duplicate/missed notifications | co-think interview |
| Architecture | `${CLAUDE_PLUGIN_ROOT}` → `${CLAUDE_SKILL_DIR}` in SKILL.md | Confirmed broken per GitHub #9354 | spec-review full-2 |
| Architecture | Matcher `"*"` → `".*"` | `*` is invalid regex | spec-review full-2 |
| SessionStartHook | Resume branch: `terminated\|crashed` → `status != pending` | Handles stale active/resumed without SpawnOrchestrator pre-update | co-think interview |
| SpawnOrchestrator | `failed_to_start` → offer new session (was "blocked") | failed_to_start is terminal but same topic can be reused | co-think interview |

#### Open Items

| Section | Item | What's Missing | Priority |
|---------|------|---------------|----------|
| FR-1 | Orchestrator instructions | Exact prompt text for Session System Prompt not written | Medium |
| FR-2 | Orchestrator instructions | Exact prompt text for wrap-up behavior not written | Medium |

#### Next Steps
- Define exact orchestrator instruction prompt text (FR-1, FR-2)
- Implement: update `session_tree.py` (schema changes), update `/chat` skill (persona instead of skill), create `/register-result` command, create `/sessions` command, create context drift hook, create notification relay hook, remove `post_tool_result_collector.py`

#### Interview Transcript
<details>
<summary>Q&A</summary>

**Q:** `/register-result`, `/sessions`를 Skill로 할지 Command로 할지?
**A:** Think layer로 사용하는 것은 전부 Command로. LLM 판단이 필요 없는 thin layer.

**Q:** `/chat`도 Command로?
**A:** `/chat`은 topic 결정, persona 선택, reference files 추천, context summary 생성 등 LLM 판단이 필요해서 Skill로 유지.

**Q:** PromptGenerator를 별도 컴포넌트로?
**A:** 함수 하나면 충분. SpawnOrchestrator 내 `generate_prompt()`로.

**Q:** FileChanged hook이 additionalContext를 지원하는지?
**A:** 공식 문서 확인 결과 지원하지 않음. 2단계 파이프라인으로 재설계: FileChanged(감지+queue+systemMessage) → UserPromptSubmit(additionalContext 주입).

**Q:** NotificationRelayHook을 main/child 분리할지?
**A:** 스크립트 하나로. Queue 파일 경로만 다름.

**Q:** SessionStartHook resume 분기 — terminated|crashed만?
**A:** `status != pending`이면 전부 resume. Stale active/resumed도 처리. SpawnOrchestrator가 pid 확인으로 gatekeeper 역할.

**Q:** `failed_to_start` 시 동작?
**A:** Resume 불가 (transcript 없음). 같은 topic으로 새 session 생성 제안.

**Q:** notifications.jsonl 스키마를 하나로?
**A:** Main session과 child session 데이터가 다르고 파일도 분리되니 스키마도 분리.

**Q:** Notification 전달 추적 — truncate vs cursor?
**A:** Cursor 방식. Crash-safe, 이력 보존, 디버깅 유리.

**Q:** Cursor 파일 — 공유 vs session별?
**A:** Session마다 따로. Queue 파일이 이미 분리되어 있으니 cursor도 분리.

</details>
