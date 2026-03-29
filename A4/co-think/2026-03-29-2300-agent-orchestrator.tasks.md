---
type: tasks
pipeline: co-think
topic: "interactive agent/prompt use cases"
date: 2026-03-29
status: draft
revision: 0
tags: []
---
# Work Breakdown: Agent Orchestrator

> Source: [architecture](./2026-03-29-2100-agent-orchestrator.architecture.md), [requirement](./2026-03-28-1030-agent-orchestrator.requirement.md)

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done
- `[s]` skipped

## Completed (prior work)

- [x] **FR-16** — Conversation-first behavioral layer (`global/agents/interactive.md`, `global/prompts/interactive.txt`) [92c7b8a]

---

## Tasks

### T1. session-tree.json 유틸리티 (공통 인프라)

`[ ]` **FR-17 기반** — 모든 컴포넌트가 공유하는 session-tree.json 읽기/쓰기 유틸리티

**산출물:**
- `global/hooks/lib/session-tree.sh` — flock 기반 atomic read-modify-write 함수들
  - `st_read` — lock + read
  - `st_write` — lock + write (jq 변환)
  - `st_find_child` — session_id로 child entry 조회

**의존성:** 없음 (기반 모듈)

---

### T2. iTerm2 스크립팅 모듈

`[ ]` **FR-17 기반** — iTerm2 탭 생성 및 환경변수 전달

**산출물:**
- `global/hooks/lib/iterm2.py` — Python + inline dependency (`iterm2` 패키지), `uv run`으로 실행
  - 새 탭 생성 + 환경변수(`SESSION_TREE`) 설정
  - `claude --session-id <uuid> --append-system-prompt-file interactive.txt` 실행

**의존성:** 없음

---

### T3. Session Manager (메인 세션 오케스트레이션)

`[ ]` **FR-17** — child session spawn 로직

**산출물:**
- `global/agents/interactive.md` 업데이트 — session manager 지시문 추가 (spawn 가능 안내, 워크플로우)
- `global/skills/spawn-session.md` — spawn 전용 skill (slash command 역할)

**처리 내용:**
1. `.claude/sessions/<main-conversation-id>/` 디렉토리 lazy 생성
2. UUID 생성 → session-tree.json에 child entry 기록 (topic, skill, resultPatterns, context)
3. T2 모듈로 iTerm2 탭 실행

**트리거 방식 (두 가지 병행):**
- interactive.md 지시문 — LLM이 대화 중 판단/제안, 사용자 승인 후 Bash로 spawn 스크립트 실행
- spawn-session skill — 사용자가 명시적으로 `/spawn-session` 호출

**의존성:** T1, T2

---

### T4. Child Session Bootstrap (SessionStart 훅)

`[ ]` **FR-17, STORY-15** — child session 초기화

**산출물:**
- `global/hooks/session-start-bootstrap.sh` — SessionStart 훅 스크립트
- `.claude/settings.json` 훅 등록

**처리 내용:**
1. `$SESSION_TREE` 환경변수로 session-tree.json 위치 확인
2. stdin JSON에서 `session_id` 읽기
3. session-tree.json에서 자기 entry 조회 (T1 유틸리티)
4. context (referenceFiles, summary) + resultPatterns를 stdout으로 주입
5. skill이 지정되어 있으면 skill 호출 지시 주입
6. conversationId, transcriptPath, pid(`$$`) 기록

**의존성:** T1

---

### T5. Result Collector — PostToolUse 훅

`[ ]` **FR-18, STORY-10** — 파일 쓰기 시 result file 자동 등록

**산출물:**
- `global/hooks/post-tool-result-collector.sh` — PostToolUse 훅 스크립트
- `.claude/settings.json` 훅 등록

**처리 내용:**
1. stdin JSON에서 `tool_name`, `tool_input.file_path` 읽기
2. Write/Edit 도구일 때만 동작
3. session-tree.json에서 자기 entry의 `resultPatterns` 조회
4. glob 패턴 매칭 → 일치하면 `resultFiles`에 추가

**의존성:** T1, T4 (Bootstrap이 먼저 entry를 완성해야 함)

---

### T6. Result Collector — SessionEnd 훅

`[ ]` **FR-18, STORY-12** — 세션 종료 시 상태 업데이트

**산출물:**
- `global/hooks/session-end-collector.sh` — SessionEnd 훅 스크립트
- `.claude/settings.json` 훅 등록

**처리 내용:**
1. `$SESSION_TREE` 확인 (없으면 일반 세션이므로 무시)
2. session-tree.json에서 자기 entry의 `status`를 `terminated`로 업데이트

**의존성:** T1, T4

---

### T7. Session Monitor (FileChanged 훅)

`[ ]` **FR-18, STORY-10, STORY-12** — 메인 세션에서 session-tree.json 변경 감지

**산출물:**
- `global/hooks/session-monitor.sh` — FileChanged 훅 스크립트 (matcher: `session-tree.json`)
- `.claude/settings.json` 훅 등록

**처리 내용:**
1. session-tree.json 변경 감지
2. 변경된 child entry 식별 (status 변경, 새 resultFiles)
3. `additionalContext`로 메인 세션에 상태 변화 주입
4. crash detection: `kill -0 <pid>` 실패 시 `crashed` 상태로 업데이트
5. handshake timeout: `pid == null` + `createdAt` > 30초 → `failed_to_start`

**의존성:** T1, T4 (Bootstrap이 pid를 기록해야 crash detection 가능)

---

### T8. History Investigator (서브 에이전트)

`[ ]` **FR-19, STORY-13** — 과거 child session 대화 기록 조사

**산출물:**
- `global/agents/history-investigator.md` — 서브 에이전트 정의

**처리 내용:**
1. session-tree.json에서 transcriptPath, resultFiles 읽기
2. `.jsonl` 트랜스크립트 파일 읽기 (offset/limit)
3. 요약 반환

**의존성:** T1 (session-tree.json 읽기 필요), T4 (transcriptPath가 기록되어야 함)

---

### T9. 통합 및 settings.json 훅 등록

`[ ]` — 모든 훅을 프로젝트 수준 `.claude/settings.json`에 등록하고 조건부 실행 보장

**산출물:**
- `.claude/settings.json` (프로젝트 수준) 최종 훅 설정
- `SESSION_TREE` 환경변수가 있는 세션에서만 child session 훅 동작하도록 가드
- 추후 검증 완료 시 `~/.claude/settings.json` (global)로 이전 예정

**의존성:** T4, T5, T6, T7

---

## Dependency Graph

```
T1 (session-tree 유틸리티)    T2 (iTerm2 모듈)
  │                            │
  ├──────────┬─────────────────┤
  │          │                 │
  │          ▼                 │
  │       T3 (Session Manager) ◄──┘
  │
  ├──► T4 (Child Session Bootstrap)
  │          │
  │          ├──► T5 (Result Collector — PostToolUse)
  │          ├──► T6 (Result Collector — SessionEnd)
  │          ├──► T7 (Session Monitor)
  │          └──► T8 (History Investigator)
  │
  └──────────────► T5, T6, T7, T8 (직접 의존)
                         │
                         ▼
                  T9 (통합 및 훅 등록)
```

## Suggested Execution Order

**Phase 1 — 기반 (병렬 가능)**
- T1 + T2 동시 진행

**Phase 2 — 코어 (T1 완료 후)**
- T3 (Session Manager) — T1, T2 모두 필요
- T4 (Child Session Bootstrap) — T1 필요

**Phase 3 — 이벤트 처리 (T4 완료 후, 병렬 가능)**
- T5 + T6 + T7 동시 진행

**Phase 4 — 보조 및 마무리**
- T8 (History Investigator)
- T9 (통합 및 훅 등록)

## FR → Task Mapping

| FR | Story | Tasks |
|----|-------|-------|
| FR-16 | STORY-7, STORY-14 | *(완료)* |
| FR-17 | STORY-9, STORY-15 | T1, T2, T3, T4 |
| FR-18 | STORY-10, STORY-12 | T5, T6, T7 |
| FR-19 | STORY-13 | T8 |

## Decisions

- **T2 — iTerm2 스크립팅**: Python + inline dependency (`iterm2`), `uv run`으로 실행
- **T3 — Spawn 트리거**: 두 가지 병행 — interactive.md 지시문 + spawn-session skill. 테스트 용이성 확보
- **T9 — 훅 등록 범위**: 프로젝트 수준 `.claude/settings.json`에 먼저 등록, 검증 후 global로 이전

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
[92c7b8a]: https://github.com/studykit/studykit-plugins/commit/92c7b8a
