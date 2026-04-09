---
type: brainstorm
pipeline: spark
topic: "architecture skill 설계"
date: 2026-03-28
status: final
tags: []
---
# Brainstorming: architecture skill 설계

## Context
co-think-requirement → co-think-domain → co-revise-requirement-with-domain까지 완성된 상태에서, 파이프라인의 다음 단계인 architecture 스킬 설계를 위한 brainstorming. spark-decide 스킬과의 관계 정리, 스킬 범위와 산출물 정의가 목표.

## Discussion Journey

1. **spark-decide와의 관계 정리** — spark-decide는 개별 결정(ADR)을 위한 범용 유틸리티(spark-* 계열)이지, co-* 파이프라인의 architecture 단계가 아님. architecture 과정에서 도구로 쓰일 수 있을 뿐.

2. **범위 결정** — 처음에 컴포넌트, 레이어, 통신, DB schema 등 넓게 시작 → 레이어 구조는 실제 서비스에서 의미 없는 경우가 많아 제외 → "큰 컴포넌트는 무엇이 있고, 컴포넌트 간 어떤 정보를 주고받는가" 수준으로 확정.

3. **DB schema와 컴포넌트 분리 불가** — 개념적으로는 나눌 수 있지만, DB schema가 컴포넌트 경계를 결정하는 경우가 많아 하나의 스킬에서 같이 다루기로.

4. **기술 선택 처리** — 매번 spark-decide로 빠지면 흐름이 끊김. 가벼운 건 인라인, 무거운 건 사용자 판단으로 spark-decide 위임.

5. **domain model의 역할** — 기계적 매핑이 아닌 참고 자료. 단, glossary 개념, concept relationships, state transitions 세 가지는 architecture에서 빠지면 안 되는 내용 → 정합성 확인 시 체크리스트로 활용.

6. **architecture-reviewer 필요** — 이전 산출물(story, requirement, domain model) 대비 architecture 산출물의 완성도를 검증하는 agent.

## Ideas

### Theme: co-think-architecture skill
- **Input**: story + requirement + domain model (reference material)
- **Scope**: component identification, inter-component information flow, DB schema
- **Abstraction level**: "A sends user information to B" level. Communication method/data format undetermined
- **Out of scope**: detailed API design, infrastructure/deployment, auth/security details, error handling, code structure, layer structure
- **Artifact format**:
  - PlantUML component diagram (overall structure) + text
  - PlantUML sequence diagram (per-story information flow) + text
  - PlantUML IE diagram (DB schema) + text
- **Flow**:
  1. Big picture — identify major components from input (consensus through conversation)
  2. Per-component deep dive — DB schema (if applicable) + information flow (design through conversation)
  3. Overall consistency check — cross-diagram consistency + verification against domain model
- **Tech choices**: lightweight decisions inline, heavy ones delegated to spark-decide (user judgment)
- **Conversation style**: same as co-* family. Facilitator asks questions and guides, user controls topic switching/revisiting/pausing

### Theme: architecture-reviewer agent
- **Input**: architecture artifact + story + requirement + domain model
- **Verification items**:
  - All stories covered by sequence diagrams
  - Domain model core concepts reflected in components
  - Cross-boundary relationships reflected in information flow
  - State transition trigger/management responsibilities assigned to components
  - DB schema consistent with components
- **Output**: issue list + improvement suggestions
- **Form**: same agent pattern as existing reviewers (story-reviewer, requirement-reviewer, domain-reviewer)

### Theme: spark-decide relationship
- **spark-decide ≠ architecture skill**: general-purpose utility for choosing between individual options
- **Not part of co-* pipeline**: spark-* family are independent utilities, callable from anywhere in the pipeline
- **Role in architecture**: delegation target when heavy tech choices are needed
