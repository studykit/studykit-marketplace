# Interactive Sub-agent with User-Controlled Termination

## 배경

Claude Code CLI 세션에서 sub-agent와 자유로운 대화를 하고, 완료 후 결과만 main session에 반환하고 싶다.

### 핵심 요구사항

1. Sub-agent가 독립적인 CLI UI를 가질 것 (main session과 UI 분리)
2. 사용자가 sub-agent와 직접 대화할 수 있을 것
3. 사용자가 종료 시점을 직접 제어
4. 완료 후 결과 요약만 main session에 반환
5. Main session의 컨텍스트를 오염시키지 않음

## 검토한 접근법

### 1. 수동 중계 루프 (Manual Relay)

Main agent가 매 턴마다 AskUserQuestion → SendMessage → 응답 전달을 반복.

```
사용자 ↔ Main Agent ↔ Sub-agent
         (매 턴 개입)
```

- 장점: 즉시 사용 가능, 설정 불필요
- 단점: Main이 매 턴 개입 → 토큰 2배 소모, Main 컨텍스트 오염

**검증 결과**: 동작하지만 UX가 동일 — 사용자 입장에서 main과 sub 구분 불가

### 2. SDK 외부 루프 (Programmatic Loop)

외부 스크립트가 `query()`를 while 루프에서 반복 호출.

```
사용자 ↔ 외부 스크립트(while 루프) ↔ Claude query()
```

- 장점: 결정적 동작, 토큰 효율적, 자동화 용이
- 단점: CLI UI 사용 불가, 별도 코드 작성 필요, 초기 설정 비용
- 참고: SDK는 CLI 위에서 동작하므로 인증/설정/hooks/MCP 모두 공유됨

### 3. tmux 기반 세션 분리

tmux pane에 별도 CLI 인스턴스를 띄우고, 파일/pipe로 결과 반환.

```
┌─ Main CLI pane ─┬─ Sub-agent CLI pane ─┐
│  결과 대기       │  사용자 ↔ 자유 대화    │
│  ← 파일로 결과   │  Stop hook → 결과 저장 │
└─────────────────┴───────────────────────┘
```

- 장점: Sub-agent가 독립적인 CLI UI 보유
- 단점: 프로세스 간 통신 복잡, pane 수동 전환 필요, 결과 전달 신뢰성 문제

### 4. Agent tool 기반 자체 루프 (실패)

Agent tool로 sub-agent를 생성하여 내부에서 AskUserQuestion 루프를 돌리는 방식.

```
Main Agent → Agent tool로 sub-agent 생성
               ↓
             Sub-agent: 1회 응답 후 즉시 return (루프 불가)
```

- 결과: **실패** — Agent tool로 생성된 sub-agent는 응답 생성 후 즉시 return하는 구조라 AskUserQuestion 루프를 자체적으로 돌릴 수 없음

### 5. Team + AskUserQuestion 루프 (부분 성공)

TeamCreate로 teammate를 생성하여 AskUserQuestion 루프를 돌리는 방식.

```
Main → TeamCreate → teammate 생성
Teammate: AskUserQuestion 호출 → 사용자 응답 → 반복 → SendMessage로 결과 반환
```

- 결과: **기능적으로 성공** — teammate는 지속 실행되므로 AskUserQuestion 루프 가능
- 문제: AskUserQuestion이 main session UI에 표시됨 → UI가 분리되지 않음
- 결론: 수동 중계 루프와 사용자 경험이 동일

### 6. Team + 자연 대화 (선택된 방식) ✅

TeamCreate로 teammate를 생성하되, AskUserQuestion을 사용하지 않고 자연스러운 대화.

```
Main → TeamCreate → teammate 생성 (split pane)
Teammate: 자체 UI에서 사용자와 직접 대화
사용자가 "종료" → teammate가 SendMessage로 요약 전달 → shutdown
```

- 결과: **성공** — UI 분리, 직접 대화, 결과 반환 모두 동작

## 선택된 설계: Team + Split Pane + 자연 대화

### 핵심 원리

Agent Teams 공식 문서에 따르면:

> Unlike subagents, which run within a single session and can only report back to the main agent, you can also interact with individual teammates directly without going through the lead.

이것이 이 설계가 가능한 근본적인 이유다. Teammate는 독립적인 Claude Code 세션이며, 사용자가 직접 상호작용할 수 있다.

### Display Mode

| 모드 | 동작 | 사용자 상호작용 |
|------|------|----------------|
| **in-process** | 모든 teammate가 main 터미널 안에서 실행 | `Shift+Down`으로 teammate 전환 후 직접 대화 |
| **split panes** (tmux/iTerm2) | 각 teammate가 별도 pane에서 실행 | pane 클릭해서 직접 대화 |
| **auto** (기본값) | tmux 안이면 split, 아니면 in-process | 환경에 따라 자동 선택 |

설정:

```json
// settings.json
{
  "teammateMode": "tmux"  // split pane 모드 강제. tmux/iTerm2 자동 감지
}
```

iTerm2 사용 시 `it2` CLI 설치 + Python API 활성화 필요.

### 아키텍처

```
┌─ Main Session (lead) ──────┬─ Teammate Session (split pane) ─┐
│                             │                                  │
│  사용자: "코드 리뷰 해줘"    │  Teammate: 독립적인 CLI UI       │
│  Lead: TeamCreate           │  사용자가 직접 대화               │
│  Lead: teammate 생성        │  (pane 클릭 or Shift+Down)      │
│  Lead: 대기...              │                                  │
│                             │  사용자: "종료"                   │
│  ← SendMessage (요약 수신)  │  Teammate: 요약 작성              │
│                             │  Teammate: SendMessage → lead    │
│  Lead: 결과 활용            │  Teammate: shutdown               │
│                             │                                  │
└─────────────────────────────┴──────────────────────────────────┘
```

### Sub-agent 프롬프트 설계

```
당신은 {역할}입니다. 사용자와 자유롭게 대화하세요.

## 규칙

1. 사용자와 자연스럽게 대화하세요. 질문이 있으면 텍스트로 물어보세요.
2. AskUserQuestion은 사용하지 마세요. 자체 UI에서 직접 대화합니다.
3. 사용자가 "종료", "끝", "exit" 등 종료 의사를 밝힐 때만 대화를 종료하세요.
4. 그 외에는 절대 스스로 종료하지 마세요.
5. 종료 시, 대화 내용을 요약하여 team lead에게 SendMessage로 전달하세요.

## 종료 시 반환 형식

[SHUTDOWN_REQUEST]

## 대화 요약

### 논의한 주제
- ...

### 도출된 결론/결정사항
- ...

### 후속 조치 항목
- ... (없으면 "없음")
```

### 데이터 흐름

```
Lead → Teammate:  초기 컨텍스트 (spawn prompt에 포함)
Teammate ↔ 사용자: 자체 UI에서 직접 대화 (N회 왕복)
Teammate → Lead:  [SHUTDOWN_REQUEST] + 결과 요약 (SendMessage)
Lead:             요약 수신 → shutdown_request 전송 → TeamDelete
```

### 종료 흐름

1. 사용자가 teammate 세션에서 "종료"라고 입력
2. Teammate가 대화 요약 작성
3. Teammate가 `[SHUTDOWN_REQUEST]` + 요약을 SendMessage로 lead에게 전달
4. Lead가 `[SHUTDOWN_REQUEST]` 태그를 감지
5. Lead가 shutdown_request를 teammate에게 전송
6. Teammate가 shutdown 승인 → 세션 종료
7. Lead가 TeamDelete로 team 정리

### 이점

| 항목 | 설명 |
|------|------|
| UI 분리 | Teammate가 독립 pane/세션에서 실행. Main과 완전히 분리 |
| 직접 대화 | 사용자가 teammate와 직접 상호작용. Relay 불필요 |
| 토큰 효율 | Main은 생성/종료에만 개입. 중간 대화는 teammate만 토큰 소모 |
| 컨텍스트 격리 | Main에는 최종 요약만 남음 |
| CLI UI 완전 활용 | Teammate는 완전한 Claude Code 세션 — 마크다운, 도구, MCP 모두 사용 가능 |
| 자연스러운 UX | AskUserQuestion 위젯 없이 일반 대화처럼 진행 |

### 고려사항

| 항목 | 대응 방안 |
|------|----------|
| 긴 대화 시 컨텍스트 증가 | Teammate 자체 컨텍스트이므로 main에 영향 없음 |
| Teammate 자체 종료 불가 | `[SHUTDOWN_REQUEST]` 태그 → lead가 자동 shutdown 처리 |
| Split pane 환경 의존 | tmux 또는 iTerm2 + it2 CLI 필요. 없으면 in-process 모드로 fallback |
| 실험적 기능 | Agent Teams는 experimental. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 활성화 필요 |

### 전제 조건

1. Claude Code v2.1.32 이상
2. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 환경변수 또는 settings.json에 설정
3. Split pane 사용 시: tmux 설치 또는 iTerm2 + `it2` CLI + Python API 활성화
4. Agent 정의 파일: `.claude/agents/interactive-chat.md`

## 검증 이력

| 단계 | 방법 | Display Mode | 결과 |
|------|------|-------------|------|
| 1 | Agent tool + AskUserQuestion 루프 | N/A | 실패 — 1회 응답 후 즉시 return |
| 2 | TeamCreate + AskUserQuestion 루프 | split pane (iTerm2) | 부분 성공 — 루프 동작하나 AskUserQuestion이 main UI에 표시됨 |
| 3 | TeamCreate + 자연 대화 (AskUserQuestion 제거) | split pane (iTerm2) | 성공 — UI 분리, 직접 대화, 결과 반환 모두 동작 |
| 4 | TeamCreate + 자연 대화 + `[SHUTDOWN_REQUEST]` | split pane (iTerm2) | 성공 — 종료 요청 감지 → 자동 shutdown → TeamDelete 전체 흐름 동작 |
| 5 | TeamCreate + 자연 대화 + `[SHUTDOWN_REQUEST]` | in-process | 기능적 성공 — 하지만 UX 불편. teammate 전환이 수동(`Shift+Down`) |
| 6 | in-process 모드에서 `Ctrl+D`로 teammate 종료 | in-process | 실패 — `Ctrl+D`(EOF)가 teammate뿐 아니라 전체 Claude 프로세스를 종료시킴 |
| 7 | split pane 모드에서 `Ctrl+D`로 teammate 종료 | split pane (iTerm2) | 부분 실패 — teammate pane만 종료되지만 lead에 요약 미전달 (SendMessage 전에 프로세스 종료) |

참고: 테스트 환경은 iTerm2 + `it2` CLI. `teammateMode: "auto"` 기본값에서 iTerm2가 감지되어 자동으로 split pane 모드로 동작함.

### 핵심 발견

```
Agent tool  → 1회 응답 후 즉시 return (루프 불가)
Team member → 독립 세션으로 지속 실행 (자연 대화 가능)
Team member + AskUserQuestion → main UI에 표시됨 (UI 분리 안 됨)
Team member - AskUserQuestion → 자체 UI에서 직접 대화 (UI 분리됨) ✅
```

### Split Pane vs In-Process 비교

| 항목 | Split Pane (iTerm2) | In-Process |
|------|-------------------|------------|
| **테스트 여부** | 검증 완료 ✅ | 검증 완료 ✅ |
| **UI 분리** | 물리적 pane 분리 — 동시에 양쪽 확인 가능 | 논리적 분리 — `Shift+Down`으로 수동 전환 |
| **사용자 상호작용** | pane 클릭으로 직접 대화 | `Shift+Down` 수동 전환 후 타이핑 |
| **teammate 생성 시 자동 전환** | pane이 자동 생성되어 바로 보임 | 자동 전환 안 됨 — 수동으로 `Shift+Down` 필요 |
| **환경 요구사항** | tmux 또는 iTerm2 + `it2` CLI | 없음 (모든 터미널) |
| **`Ctrl+D` 동작** | teammate pane만 종료 — lead는 살아있지만 요약 미전달 | 전체 Claude 프로세스 종료 — 위험 |
| **UX 평가** | **좋음** — 자연스러운 흐름 | **불편** — 수동 전환 + `Ctrl+D` 위험 |
| **권장 여부** | **권장** ✅ | interactive 대화 용도로는 비권장 |

### 결론: Split Pane 모드 권장

Interactive sub-agent 대화에는 **split pane 모드가 필수적**. in-process 모드는 teammate 세션으로 자동 전환이 되지 않아 대화 흐름이 끊기며, interactive 용도로는 적합하지 않음. tmux 또는 iTerm2 + `it2` CLI 환경을 전제 조건으로 설정.

### 종료 방법 비교

| 종료 방법 | Lead에 요약 전달 | 안전성 |
|----------|-----------------|--------|
| 대화에서 "종료" 입력 → teammate가 SendMessage 후 shutdown | **전달됨** ✅ | 안전 |
| `Ctrl+D` (split pane) | **미전달** — 프로세스 즉시 종료 | Lead는 살아있음 |
| `Ctrl+D` (in-process) | **미전달** — 전체 프로세스 종료 | 위험 |

**결론: 결과를 받으려면 반드시 대화 내에서 "종료"를 입력해야 함.** `Ctrl+D`는 비상 탈출 용도로만 사용.

### 주의사항

1. **`Ctrl+D`로 teammate를 종료하면 고스트 프로세스가 남을 수 있음.** split pane 모드에서 `Ctrl+D`로 teammate pane을 종료하면 lead 쪽 UI에 `@chat-agent: Incubating...` 상태로 잔존할 수 있다. team 디렉토리를 강제 삭제(`rm -rf`)해도 UI에서 사라지지 않으며, shutdown_request도 응답하지 않는다. 이 경우 **lead 세션 자체를 `/exit`로 재시작**해야 정리된다.

2. **team 디렉토리 강제 삭제는 불완전한 정리.** `rm -rf ~/.claude/teams/{team-name}`으로 디렉토리만 삭제하면 파일 시스템은 정리되지만, 실행 중인 프로세스와 UI 상태는 남는다. 반드시 정상 종료 흐름(SendMessage → shutdown_request → TeamDelete)을 따를 것.

3. **teammate 종료 전 TeamDelete는 실패한다.** active member가 있으면 TeamDelete가 거부됨. 항상 모든 teammate를 shutdown한 후에 TeamDelete를 실행해야 한다.

## 다음 단계

1. 다양한 역할(코드 리뷰어, 디버거 등)의 agent 정의 파일 확장
2. 긴 대화에서의 안정성 테스트
