---
type: debug
pipeline: co-think
topic: "agent orchestrator implementation verification"
date: 2026-03-29
status: draft
---
# Debug Report: Agent Orchestrator Implementation vs Architecture

> Architecture: [2026-03-29-2100-agent-orchestrator.architecture.md](./2026-03-29-2100-agent-orchestrator.architecture.md)
> Tasks: [2026-03-29-2300-agent-orchestrator.tasks.md](./2026-03-29-2300-agent-orchestrator.tasks.md)

## Summary

T1~T9 모두 done으로 표시되어 있으나, 아키텍처 명세와 실제 구현 사이에 **17건의 불일치**를 발견했다. 심각도 기준: Critical (동작 불가 또는 데이터 정합성 위험), Major (명세 위반이나 동작은 함), Minor (스타일/비일관성).

---

## Findings

### D-01. [Critical] Session Monitor가 새 resultFiles 등록을 감지하지 않음

**명세 (STORY-10):**
> "MO → MS : inject status update (new result file registered)"

**구현 (`session-monitor.sh`):**
`terminated`, `crashed`, `failed_to_start` 상태 변화만 감지. `resultFiles` 배열에 새 파일이 추가되었을 때의 diff 로직이 없음.

**영향:** child session이 결과 파일을 쓸 때 main session이 실시간으로 알림을 받지 못함. main session은 child가 terminate된 후에야 결과 파일 목록을 볼 수 있음.

**수정 방향:** 이전 스냅샷과 현재 상태의 `resultFiles` 배열을 비교하여 새로 추가된 파일을 감지하고 알림에 포함.

---

### D-02. [Critical] spawn-session.sh가 iterm2.py 대신 iterm2.sh를 호출

**명세 (Architecture, T2):**
> "iTerm2 tab creation uses a Python script with the `iterm2` package (inline dependency), executed via `uv run`."
> "launches an iTerm2 tab via `uv run iterm2.py`"

**구현 (`spawn-session.sh:114`):**
```bash
bash "$HOOKS_LIB/iterm2.sh" \
```

`iterm2.sh`는 `it2` CLI를 사용하며, `iterm2.py`는 AppleScript를 사용. 두 구현 모두 아키텍처가 명시한 `iterm2` Python 패키지를 사용하지 않음.

**영향:** `iterm2.sh`는 iTerm2 session ID를 반환하지 못함 (`{"itermSessionId": null}`). `iterm2.py`는 AppleScript로 session ID를 반환하지만 호출되지 않음.

**수정 방향:** spawn-session.sh에서 `uv run "$HOOKS_LIB/iterm2.py"`를 호출하도록 변경. iterm2.py가 반환하는 session ID를 session-tree.json에 기록. `iterm2.sh`는 fallback 또는 제거.

---

### D-03. [Critical] CLAUDE_SESSION_ID 환경변수 미제공으로 session-tree.json 경로 붕괴

**명세 (Session Manager):**
> "session-tree.json at `.claude/sessions/<main-conversation-id>/`"

**구현 (`spawn-session.sh:44,66-67`):**
```bash
SESSION_ID="${CLAUDE_SESSION_ID:-${CLAUDE_CONVERSATION_ID:-}}"
SESSION_DIR=".claude/sessions/$SESSION_ID"
export SESSION_TREE="$SESSION_DIR/session-tree.json"
```

**실제 동작:** `CLAUDE_SESSION_ID`와 `CLAUDE_CONVERSATION_ID` 모두 Claude Code가 hook/bash에 환경변수로 제공하지 않음. 결과적으로 `SESSION_ID`가 빈 문자열이 되어:
- `SESSION_DIR` → `.claude/sessions/` (conversation ID 하위 디렉토리 없음)
- `SESSION_TREE` → `.claude/sessions/session-tree.json`

**검증 결과:** 실제로 `~/.claude/sessions/session-tree.json`이 sessions 디렉토리 바로 아래에 생성됨. 모든 대화의 session-tree.json이 동일 파일에 덮어씌워짐.

**영향:** 서로 다른 main session이 동일한 session-tree.json을 공유하게 되어 child entry가 뒤섞임. 아키텍처의 핵심 전제 (대화별 격리된 세션 트리)가 완전히 무너짐.

**수정 방향:** Claude Code가 실제로 제공하는 세션 식별자를 확인. stdin JSON의 `session_id`는 hook에서만 사용 가능하므로, spawn-session.sh는 SessionStart hook이 아닌 Bash tool에서 실행됨 → hook stdin을 사용할 수 없음. `CLAUDE_SESSION_ID` 대신 Claude Code가 실제 제공하는 메커니즘 파악 필요.

---

### D-04. [Critical] main session이 프로젝트 `.claude/` 대신 `$HOME/.claude/`를 사용

**명세:**
> "session-tree.json at `.claude/sessions/<main-conversation-id>/`"

`.claude/sessions/`는 프로젝트 루트 기준 상대 경로.

**관찰:** main session이 수동 spawn 시 `$HOME/.claude/sessions/`를 사용:
```bash
SESSION_DIR="$HOME/.claude/sessions/$CLAUDE_CONVERSATION_ID"
```

**영향:** session-tree.json이 프로젝트 디렉토리가 아닌 글로벌 설정 디렉토리에 생성됨. 프로젝트 간 격리 불가. `.claude/settings.json`의 FileChanged matcher (`session-tree.json`)도 프로젝트 상대 경로를 기대하므로 session-monitor.sh가 변경을 감지하지 못할 수 있음.

**근본 원인:** spawn-session.sh는 상대 경로 `.claude/sessions/`를 사용하지만, main session LLM이 직접 Bash로 실행할 때 경로를 `$HOME/.claude/`로 잘못 해석. interactive.md의 spawn workflow 예시에도 절대 경로 가이드가 없어 LLM이 추측하게 됨.

**수정 방향:** spawn-session.sh만 사용하도록 강제하거나, interactive.md에 명확한 경로 규칙 명시. D-03과 함께 해결 필요.

---

### D-05. [Major] 파일 잠금 메커니즘: flock 대신 mkdir 스핀락

**명세 (Concurrency and Error Handling):**
```bash
(
  flock -x 200
  content=$(cat session-tree.json)
  updated=$(echo "$content" | jq '...')
  echo "$updated" > session-tree.json
) 200>session-tree.json.lock
```

**구현 (`session-tree.sh:14-24`):**
```bash
_st_lock() {
  while ! mkdir "$_st_lockdir" 2>/dev/null; do
    ...
    sleep 0.05
  done
}
```

`mkdir` 기반 스핀락은 원자적이긴 하나, `flock`과 달리 프로세스가 비정상 종료 시 lock 디렉토리가 남을 수 있음 (stale lock). 아키텍처가 명시적으로 `flock`을 지정한 이유이기도 함.

**영향:** child session이 crash하면 `.lock` 디렉토리가 남아 이후 모든 session-tree.json 쓰기가 100회 재시도 후 실패할 수 있음.

**수정 방향:** `flock` 기반으로 전환하거나, stale lock 감지 로직 추가 (예: lockdir의 age 확인).

---

### D-06. [Major] PID 기록: 명세 `$$` vs 구현 `$PPID`

**명세 (Crash detection):**
> "The Child Session Bootstrap records `$$` (its own PID) into the child entry during initialization. Since the hook runs as a child process of the Claude Code process, the recorded PID is the Claude Code process itself"

**구현 (`session-start-bootstrap.sh:81`):**
```bash
.pid = $PPID)
```

**분석:** 명세의 설명 자체가 모순. `$$`는 hook script 자신의 PID이지 Claude Code process의 PID가 아님. 구현의 `$PPID`가 Claude Code process PID를 정확히 가리키므로, **구현이 올바르고 명세가 잘못됨**.

**수정 방향:** 아키텍처 문서에서 `$$`를 `$PPID`로 정정하고, 설명도 수정.

---

### D-07. [Major] SessionEnd 훅이 "Stop" 이벤트로 등록됨

**명세:**
> "SessionEnd hooks on the child session"
> T6: "`global/hooks/session-end-collector.sh` — SessionEnd 훅 스크립트"

**구현 (`.claude/settings.json`):**
```json
"Stop": [{
  "hooks": [{
    "command": "bash global/hooks/session-end-collector.sh"
  }]
}]
```

**분석:** Claude Code에서 세션 종료 시 발동하는 hook 이벤트 이름이 `Stop`일 수 있음. 다만 `Stop`은 일반적으로 "LLM이 응답을 완료했을 때"를 의미하며, "세션이 종료될 때"와 다름. `Stop`은 매 턴마다 발동하므로, 세션 종료가 아닌 모든 응답 완료 시마다 `terminated` 상태를 쓰려고 시도할 수 있음.

**영향:** 매 LLM 응답마다 session-end-collector.sh가 실행되어 불필요한 오버헤드 발생 가능. 또한 첫 응답 이후 즉시 `terminated`로 표시될 위험.

**수정 방향:** Claude Code가 지원하는 hook 이벤트 타입을 확인. `Stop` hook의 stdin JSON에 세션 종료 여부를 판별할 수 있는 필드가 있는지 검토. 없다면 다른 메커니즘(예: trap on EXIT in the shell) 필요.

---

### D-08. [Major] 불필요한 prompt 파일 동적 생성

**관찰 (main session의 수동 spawn 실행):**
```bash
PROMPT_FILE="$SESSION_DIR/${CHILD_ID}.txt"
cat > "$PROMPT_FILE" << 'PROMPT'
...context...
PROMPT
```

**명세:**
> `--append-system-prompt-file interactive.txt`

`session-start-bootstrap.sh`가 이미 `session-tree.json`에서 context를 읽어 stdout으로 주입. `spawn-session.sh`도 고정 파일 `global/prompts/interactive.txt`만 전달.

**영향:** 중복 context 주입. child session이 동일 정보를 system prompt file과 SessionStart hook 두 경로로 받음. 또한 세션별 임시 파일이 정리되지 않고 누적.

**수정 방향:** 동적 prompt 파일 생성 제거. `spawn-session.sh`의 원래 설계대로 `interactive.txt`만 전달.

---

### D-09. [Major] session-monitor.sh의 crash detection jq 구문 오류 가능성

**구현 (`session-monitor.sh:64`):**
```bash
st_write '(.children[] | select(.id == "'"$child_id"'")) .status = "crashed"'
```

`) .status` 사이의 공백이 jq 파싱 오류를 일으킬 수 있음. `).status` 또는 `|= .status`여야 함.

비교: `session-end-collector.sh:20`의 올바른 구문:
```bash
st_write "(.children[] | select(.id == \"$session_id\")).status = \"terminated\""
```

**영향:** crash detection이 작동하지 않을 수 있음.

**수정 방향:** `).status`로 공백 제거, 또는 `session-end-collector.sh`와 동일한 패턴 사용.

---

### D-10. [Major] post-tool-result-collector.sh의 glob 패턴 매칭 한계

**구현 (`post-tool-result-collector.sh:42`):**
```bash
if [[ "$file_path" == $pattern ]]; then
```

bash의 `==` 패턴 매칭은 `*`를 지원하지만 `**` (recursive globstar)를 지원하지 않음. `[[ ]]` 내에서 `**`는 `*`와 동일하게 동작.

**영향:** `A4/co-think/*.debug.md`처럼 단일 레벨 glob은 동작하나, `A4/**/*.debug.md`처럼 재귀 glob은 예상대로 동작하지 않음.

**수정 방향:** 재귀 패턴이 필요한 경우 `find` 또는 별도 glob 매칭 유틸리티 사용. 단순 패턴만 사용한다면 문서에 `**` 미지원을 명시.

---

### D-11. [Minor] iterm2.py에 `iterm2` 패키지 inline dependency 누락

**명세 (T2):**
> "Python + inline dependency (`iterm2` 패키지)"

**구현 (`iterm2.py:2-4`):**
```python
# /// script
# requires-python = ">=3.10"
# ///
```

`iterm2` 패키지가 dependencies에 없음. 실제로는 AppleScript(`osascript`)를 사용하므로 외부 패키지가 필요 없음.

**영향:** 기능상 문제 없음. 다만 명세와 구현 접근법이 완전히 다름 (iterm2 Python API vs AppleScript).

**수정 방향:** 아키텍처 문서에서 구현 방식을 AppleScript로 정정, 또는 iterm2 Python 패키지 기반으로 재구현.

---

### D-12. [Minor] SESSION_TREE 경로가 상대 경로

**구현 (`spawn-session.sh:66`):**
```bash
SESSION_DIR=".claude/sessions/$SESSION_ID"
export SESSION_TREE="$SESSION_DIR/session-tree.json"
```

**영향:** 모든 hook은 CWD가 프로젝트 루트라는 가정 하에 동작. Claude Code가 다른 디렉토리에서 hook을 실행하면 파일을 찾지 못함. 실제로 main session의 수동 실행에서 `$HOME/.claude/sessions/`를 사용한 것은 이 혼란의 증거.

**수정 방향:** 절대 경로 사용을 고려. 또는 hook 스크립트에서 `cd "$PROJECT_ROOT"` 가드 추가.

---

### D-13. [Minor] iterm2.sh가 iTerm2 session ID를 반환하지 못함

**구현 (`iterm2.sh:47`):**
```bash
echo '{"itermSessionId": null}'
```

`it2 session split`이 session ID를 반환하지 않으므로 항상 null.

**영향:** `iterm2.py`는 AppleScript를 통해 session ID를 반환하지만, 실제 호출되는 `iterm2.sh`는 null만 반환. session-tree.json의 `itermSessionId`가 항상 null.

---

### D-14. [Minor] session-start-bootstrap.sh에서 skill-specific resultPatterns 추가 누락

**명세:**
> "the Child Session Bootstrap may add skill-specific patterns during initialization"
> "CB → ST : append skill-specific resultPatterns (if skill defines additional patterns)"

**구현:** session-start-bootstrap.sh에 skill-specific resultPatterns를 추가하는 로직 없음. skill 이름을 읽어서 호출 지시만 주입.

**영향:** skill이 정의하는 추가 resultPatterns가 자동으로 등록되지 않음. child session LLM이 수동으로 추가해야 함.

---

### D-15. [Minor] session-monitor.sh의 handshake timeout이 macOS 전용

**구현 (`session-monitor.sh:72`):**
```bash
created_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$child_created" +%s 2>/dev/null || echo 0)
```

`date -j -f`는 macOS의 BSD date 전용. Linux의 GNU date에서는 동작하지 않음.

**영향:** macOS에서만 handshake timeout이 작동. 현재 프로젝트가 macOS 타겟이므로 실질적 문제는 적음.

---

### D-16. [Minor] interactive.md와 interactive.txt 내용 중복

`global/agents/interactive.md`와 `global/prompts/interactive.txt`가 거의 동일한 내용. agent 정의와 prompt 파일이 별도로 관리되어 동기화 부담.

---

### D-17. [Minor] history-investigator.md에 session-tree.json 접근 방법 미기재

**명세 (STORY-13):**
> "SM → ST : look up child entry (by topic or ID)"
> "SM → HI : spawn sub-agent with transcriptPath + resultFiles"

**구현:** history-investigator.md는 `transcriptPath`와 `resultFiles`를 입력으로 받는다고 기술하지만, 이를 어떻게 전달받는지(main session이 session-tree.json에서 읽어서 프롬프트에 포함) 명시하지 않음.

**영향:** 기능상 문제 없음 (main session LLM이 알아서 처리). 다만 agent 정의만으로는 사용법이 불명확.

---

## Severity Summary

| Severity | Count | IDs |
|----------|-------|-----|
| Critical | 4 | D-01, D-02, D-03, D-04 |
| Major | 6 | D-05, D-06, D-07, D-08, D-09, D-10 |
| Minor | 7 | D-11, D-12, D-13, D-14, D-15, D-16, D-17 |

## Resolution Status

| ID | Status | Resolution |
|----|--------|------------|
| D-01 | ✅ Fixed | session-monitor.sh에 resultFiles diff 로직 추가 |
| D-02 | ✅ Fixed | iterm2.py 삭제, iterm2.sh (it2 CLI)로 통일 |
| D-03 | ✅ Fixed | `${CLAUDE_SESSION_ID}` skill 템플릿 변수 사용, `--session-id` 파라미터 추가 |
| D-04 | ✅ Fixed | 프로젝트 루트 기준 `.claude/sessions/<session-id>/`로 통일 (D-03과 함께 해결) |
| D-05 | ✅ Fixed | mkdir 스핀락 유지 (macOS에 flock 없음), stale lock 감지 추가 (10초 age 확인) |
| D-06 | ✅ Fixed | 아키텍처 문서에서 `$$` → `$PPID`로 정정 |
| D-07 | ✅ Fixed | settings.json에서 `Stop` → `SessionEnd` 이벤트로 변경 |
| D-08 | ✅ Fixed | interactive.md/txt에서 spawn 상세 제거, `/spawn-session` skill로 위임 |
| D-09 | ✅ Fixed | jq 구문 `) .status` → `).status` 공백 제거 |
| D-10 | ✅ Fixed | `**`를 `*`로 치환하여 매칭 |
| D-11 | ✅ Resolved | iterm2.py 삭제로 해소 (D-02) |
| D-12 | Open | SESSION_TREE 상대 경로 — ${CLAUDE_SESSION_ID} 사용으로 경감됨 |
| D-13 | ✅ Resolved | itermSessionId 필드 전면 제거, iterm2.py 삭제 (D-02) |
| D-14 | Open | skill-specific resultPatterns 추가 로직 미구현 |
| D-15 | Open | macOS 전용 date 구문 — 현재 타겟이 macOS이므로 수용 |
| D-16 | ✅ Resolved | interactive-child.txt 분리, interactive.md에서 spawn 상세 제거로 중복 완화 |
| D-17 | Open | history-investigator.md 사용법 미기재 — 기능상 문제 없음 |

### 추가 리팩토링
| Item | Description |
|------|-------------|
| child `id` → `conversationId` 통일 | child entry에서 `id` 필드 제거, `conversationId`를 PK로 사용 (spawn 시 생성한 UUID = Claude Code session_id) |
| `itermSessionId` 제거 | 사용처 없어 전면 제거 |
| `interactive-child.txt` 분리 | child session용 prompt에서 Session Manager 섹션 제거 |
| `.claude/skills`, `.claude/agents` symlink | `global/` 원본에 대한 심볼릭 링크로 동기화 부담 제거 |
