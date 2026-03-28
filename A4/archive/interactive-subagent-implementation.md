# Interactive Sub-agent 구현 가이드

## 개요

사용자가 `/chat` 을 입력하면 interactive sub-agent와 split pane에서 자유 대화를 시작하고, 종료 시 결과 요약이 main session에 반환되는 시스템. agent를 지정하면 해당 agent가 interactive 모드로 동작한다.

```
사용자: /chat obsidian 플러그인에 대해 이야기하자
  → Skill이 team 생성 + teammate spawn (기본: interactive-chat)
  → Split pane에서 사용자 ↔ teammate 직접 대화
  → 사용자: "종료"
  → Teammate: 요약 + [SHUTDOWN_REQUEST] → lead
  → Lead: shutdown → TeamDelete
  → Main session에 요약 표시

사용자: /chat debugger 로그인 버그 분석
  → Skill이 "debugger" agent를 인식
  → debugger agent가 interactive 모드로 spawn
  → 이하 동일한 흐름
```

## 파일 구조

```
.claude/
├── agents/
│   ├── interactive-chat.md     # 기본 teammate agent 정의
│   └── {custom-agent}.md       # 사용자 정의 agent (선택)
└── skills/
    └── chat/
        └── SKILL.md            # /chat skill 정의 (agent 선택 로직 포함)
```

## 전제 조건

```json
// settings.json (프로젝트 또는 글로벌)
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

- Claude Code v2.1.32 이상
- iTerm2 + `it2` CLI + Python API 활성화 (split pane용)
  - 또는 tmux 설치
- `teammateMode`: `"auto"` (기본값) 또는 `"tmux"`

## 구현

### 1. Agent 정의: `.claude/agents/interactive-chat.md`

기본 teammate의 동작을 정의하는 파일. Team member로 spawn될 때 이 정의가 적용된다.

```yaml
---
name: interactive-chat
description: 사용자와 자유롭게 대화하는 interactive sub-agent. 종료 권한은 사용자에게만 있다.
tools:
  - Read
  - Grep
  - Glob
  - SendMessage
---

당신은 사용자와 자유롭게 대화하는 interactive assistant입니다.

## 규칙

1. 사용자와 자연스럽게 대화하세요. 질문이 있으면 텍스트로 물어보세요.
2. 사용자가 "종료", "끝", "exit" 등 종료 의사를 밝힐 때만 대화를 종료하세요.
3. 그 외에는 절대 스스로 종료하지 마세요.
4. 종료 시, 대화 내용을 요약하여 team lead에게 SendMessage로 전달한 뒤 종료하세요.

## 대화 스타일

- 사용자의 언어에 맞춰 응답하세요 (한국어면 한국어로).
- 친근하고 자연스럽게 대화하세요.
- 코드, 기술, 일상 어떤 주제든 자유롭게 다루세요.
- 필요하면 Read, Grep, Glob 도구로 코드를 읽어서 답변하세요.

## 종료 시

사용자가 종료 의사를 밝히면:

1. 아래 형식으로 대화 요약을 작성하세요.
2. SendMessage로 team lead에게 요약과 함께 종료 요청을 전달하세요.

메시지 형식:

[SHUTDOWN_REQUEST]

## 대화 요약

### 논의한 주제
- ...

### 도출된 결론/결정사항
- ...

### 후속 조치 항목
- ... (없으면 "없음")

`[SHUTDOWN_REQUEST]` 태그를 반드시 포함하세요. team lead가 이 태그를 보고 자동으로 종료 처리합니다.
```

### 2. Skill 정의: `.claude/skills/chat/SKILL.md`

`/chat` 명령으로 전체 흐름을 자동화하는 skill. 첫 번째 인자로 agent를 지정할 수 있다.

#### Agent 선택 로직

Skill은 `$ARGUMENTS`의 첫 번째 단어를 `.claude/agents/` 디렉토리와 대조한다:

| 입력 | 첫 번째 단어 | `.claude/agents/`에 존재? | 사용할 agent | 주제 |
|------|-------------|-------------------------|-------------|------|
| `/chat debugger 로그인 버그` | `debugger` | `debugger.md` 있음 ✅ | `debugger` | `로그인 버그` |
| `/chat 오늘 뭐 할까` | `오늘` | `오늘.md` 없음 ❌ | `interactive-chat` | `오늘 뭐 할까` |
| `/chat` | (없음) | — | `interactive-chat` | (없음) |

#### Interactive 프롬프트 주입

**핵심: 어떤 agent를 지정하든, skill이 interactive 대화 규칙을 prompt에 주입한다.**

이를 통해:
- 사용자 정의 agent(예: debugger, reviewer)의 전문성은 agent 정의 파일에서 가져오고
- Interactive 대화 프로토콜(종료 제어, `[SHUTDOWN_REQUEST]`, AskUserQuestion 금지)은 skill이 일괄 주입

Agent 정의 파일에 interactive 규칙을 직접 넣을 필요가 없다. Skill이 spawn 시 prompt로 주입하므로, 기존 agent를 수정 없이 interactive 모드로 사용할 수 있다.

#### Skill 전문

실제 파일 내용은 `.claude/skills/chat/SKILL.md`를 참조.

## 사용 방법

```
# 기본 agent로 자유 대화
/chat

# 기본 agent + 주제 지정
/chat obsidian 플러그인에 대해 이야기하자

# 특정 agent 지정 + 주제
/chat debugger 로그인 시 세션이 끊기는 문제
/chat reviewer src/auth/ 코드 리뷰
```

실행 후:
1. Split pane이 열리고 teammate가 인사합니다.
2. Teammate pane에서 자유롭게 대화합니다.
3. "종료"라고 입력하면 teammate가 요약을 lead에게 전달합니다.
4. Main session에 대화 요약이 표시됩니다.

## 동작 흐름 상세

```
┌─ Main (Lead) ─────────────────┬─ Teammate (Split Pane) ──────────┐
│                                │                                   │
│  /chat [agent] [topic] 실행    │                                   │
│  ↓                             │                                   │
│  인자 파싱:                    │                                   │
│    agent 존재? → subagent_type │                                   │
│    없으면 → interactive-chat   │                                   │
│  ↓                             │                                   │
│  TeamCreate("interactive-chat")│                                   │
│  ↓                             │                                   │
│  Agent({parsed-agent},         │                                   │
│    name: "chat-agent",         │  ← 생성됨                         │
│    team: "interactive-chat",   │  인사 + 대화 시작                  │
│    prompt: interactive rules)  │                                   │
│  ↓                             │                                   │
│  대기...                       │  사용자 ↔ teammate 직접 대화       │
│  (idle_notification 무시)      │  (N회 왕복)                        │
│                                │                                   │
│                                │  사용자: "종료"                    │
│                                │  ↓                                │
│  ← [SHUTDOWN_REQUEST] + 요약   │  SendMessage → lead               │
│  ↓                             │                                   │
│  shutdown_request 전송 →       │  → shutdown 승인                  │
│  ↓                             │  → pane 종료                      │
│  TeamDelete                    │                                   │
│  ↓                             │                                   │
│  사용자에게 요약 표시           │                                   │
│                                │                                   │
└────────────────────────────────┴───────────────────────────────────┘
```

## 사용자 정의 Agent 추가 방법

`/chat`에서 사용할 커스텀 agent를 추가하려면 `.claude/agents/`에 agent 정의 파일을 만들면 된다.

### 예시: 디버거 agent

`.claude/agents/debugger.md`:

```yaml
---
name: debugger
description: 버그 분석 및 디버깅 전문 agent
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - SendMessage
---

당신은 디버깅 전문가입니다.

## 전문 분야
- 버그 재현 및 원인 분석
- 로그 분석
- 단계별 디버깅 가이드

## 접근 방식
1. 문제 현상 파악
2. 관련 코드/로그 확인
3. 가설 수립 및 검증
4. 수정 방안 제안
```

**주의: interactive 규칙(종료 프로토콜, AskUserQuestion 금지 등)은 넣지 않아도 된다.** `/chat` skill이 spawn 시 자동으로 주입한다.

사용:
```
/chat debugger 로그인 시 세션이 끊기는 문제
```

### Agent 정의 시 필수 사항

| 항목 | 설명 |
|------|------|
| `SendMessage` tool | tools 목록에 반드시 포함. 종료 시 lead에게 요약을 보내기 위해 필요 |
| 파일명 = agent 이름 | `{이름}.md`의 `{이름}` 부분이 `/chat` 명령에서 agent를 지정할 때 사용하는 이름 |

## 알려진 제한사항

| 제한 | 설명 | 대응 |
|------|------|------|
| `Ctrl+D` 시 요약 미전달 | 프로세스가 즉시 종료되어 SendMessage 실행 불가 | 대화에서 "종료" 입력으로 정상 종료 유도 |
| 고스트 프로세스 | 비정상 종료 시 lead UI에 teammate가 잔존 | `/exit`로 세션 재시작 |
| 강제 삭제 불완전 | `rm -rf` 으로 team 디렉토리 삭제해도 프로세스/UI 잔존 | 정상 종료 흐름 사용 |
| Experimental 기능 | Agent Teams는 실험적 기능 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 활성화 필요 |
| Split pane 환경 의존 | iTerm2 + it2 CLI 또는 tmux 필요 | in-process 모드는 UX 불편 |
| 한 세션에 하나의 team | 동시에 여러 team 운영 불가 | 이전 team 정리 후 새 team 생성 |
