---
type: brainstorm
pipeline: spark
topic: "co-think-requirement 이후 cross-cutting 스킬 설계 논의"
date: 2026-03-24
status: final
---
# Discussion: co-think-requirement 산출물의 다음 단계

## Context
co-think-requirement 산출물(Functional Requirement)이 다음 단계로 어떻게 연결되는지에 대한 논의. requirement 이후 솔루션 영역으로 바로 넘어갈지, 문제 영역을 더 구체화할지가 핵심 질문.

## Discussion Journey

### 1. Requirement 산출물의 성격 확인
- spec은 story를 한 단계 구체화한 것
- story(왜, 어떤 가치) → requirement(무엇을 해야 하는가 — 행동, 입출력, 에러)
- 둘 다 **문제 영역(problem space)**에 있음, 구현 영역은 아님

### 2. Spec만으로 아키텍처 결정이 가능한가?
spec의 FR은 **스토리 단위로 수직 절단**되어 있어서, 아키텍처 결정에 필요한 **수평 절단(cross-cutting)** 관점이 부족함.

**spec이 잘 담고 있는 것:**
- 각 FR별 행동, 입출력, 에러 케이스
- FR 간 의존성

**아키텍처 결정에 필요하지만 spec에 없는 것:**
1. 데이터 엔티티 — FR들에 흩어진 데이터를 종합한 엔티티와 관계
2. 비기능 요구사항 — 성능, 보안, 확장성
3. 시스템 경계 — 외부 연동, 인증, 제3자 서비스
4. 상태 전이 — 시스템 전체 관점의 상태 흐름

### 3. 네 가지 관심사의 성격 구분
- **1, 4 (데이터 엔티티, 상태 전이)**: FR들을 종합해서 패턴을 추출하는 작업. spec에 이미 있는 정보를 다른 각도로 보는 것.
- **2, 3 (비기능, 시스템 경계)**: FR에 없는 새로운 정보를 사용자에게 물어서 채우는 작업. 제품을 어떤 환경에서 쓸지에 따라 결정됨 → interview를 통해 별도 시점에 다루는 게 적합.

### 4. Cross-cutting의 본질 재발견
처음에는 cross-cutting을 "문제 영역의 구체화"로 시작했으나, 산출물을 구체적으로 정의하면서 데이터 모델, 상태 전이, 인터페이스 계약 등 **아키텍처 설계에 가까운 내용**으로 흘러감.

이를 인식하고 다시 문제 영역으로 돌아옴. 순수한 문제 영역에서의 cross-cutting은:
- FR들에 반복 등장하는 **개념(concept) 식별**
- 개념들 간의 **관계 파악**
- FR 간 **의존성과 충돌 발견**

"엔티티로 정의하고 속성을 붙이는" 순간 설계로 넘어가는 것. → **Conceptual Modeling**으로 정의.

### 5. 추상화 레벨 결정
수도코드 비유 — 실제 코드와 거의 같되 문법적 디테일만 빠진 것처럼:
- 구현 수준에서 바뀔 아주 세세한 것만 뺀다
- 데이터의 구체적 type만 정하지 않을 뿐 필요한 내용은 다 포함

**경계:** "무엇이 있고 어떻게 연결되는가"는 확정, "어떻게 만드는가"는 미확정.

개발자는 추상화 레벨을 의식적으로 유지하기 어려움 → **스킬이 가드레일 역할**을 해서 사용자가 구현으로 빠지지 않게 가이드.

### 6. 별도 스킬로 분리하는 이유
실제 사람의 사고에서는 requirement↔concept을 오가는 게 자연스럽지만 AI 스킬로는 분리가 적합:
- 컨텍스트 집중 — 두 모드를 오가면 대화가 산만해짐
- 산출물 분리 — 성격이 다른 문서
- 입력/출력 명확성 — requirement → concept 흐름이 깔끔
- 추상화 가드레일 — 스킬이 경계를 강제

### 7. 산출물 포맷 결정
- **도메인 용어 정의**: glossary 테이블 (이름, 정의, 핵심 속성 1-2개, 관련 FR)
- **용어 간 관계**: PlantUML class diagram + 텍스트 설명. 핵심 속성만, 구현 타입 없음
- **상태 전이**: PlantUML state diagram + 텍스트 설명. 여러 엔티티 걸치면 복합 상태로 표현
- **의존성/충돌/누락**: TODO 체크리스트 (관련 FR 번호 + 이유)
- **frontmatter**: topic, date, source (requirement 파일 wikilinks)

PlantUML 선택 이유:
- class diagram: 데이터 모델 표현에 적합, Mermaid보다 문법 풍부
- state diagram: 엔티티 라이프사이클 + 복합 상태로 다중 엔티티 프로세스도 표현 가능
- activity diagram은 이 단계에서 불필요 (구현 단계에서 더 유용)

### 8. Requirement 피드백 루프
1. co-think-domain → TODO 목록 생성, requirement 리뷰 제안
2. 사용자가 co-revise-requirement-with-domain-model 실행 (domain model 문서를 입력으로)
3. TODO 항목별 interview → requirement FR 보완
4. 처리한 TODO에 체크 + 설명 기록 (co-revise 스킬이 domain model 문서에 marking)
5. TODO 체크 확인은 사용자 판단

### 9. co-revise-requirement-with-domain-model 스킬 분리
co-think-requirement과 co-revise-requirement-with-domain-model은 목적과 대화 흐름이 다름:
- co-think-requirement: story → 새로 requirement 작성. story별 순차 진행
- co-revise-requirement-with-domain-model: domain model feedback → 기존 requirement 보완. TODO 항목별 진행

이름: `co-revise-requirement-with-domain-model` — concept에서 출발해서 requirement으로 가는 흐름이 이름에 드러남.

### 10. 시스템 경계의 위치 재조정
처음에는 시스템 경계를 별도 interview로 분리했으나, 논의 중 FR에서 시스템 간 관계가 자연스럽게 드러남을 확인:
- 같은 코드베이스의 frontend/backend도 두 시스템 간 인터페이스가 필요
- FR을 수평으로 읽으면 "이 데이터는 여기서 만들어지고 저기서 쓰인다" → 경계가 보임

→ FR에서 도출 가능한 시스템 경계는 domain model에서 다루고, 외부 환경(인프라, 보안 등)만 별도로.

## Decisions

### 스킬 이름과 파이프라인
- `co-think-domain` — FR에서 도메인 개념 추출 (conceptual modeling)
- `co-revise-requirement-with-domain-model` — domain model 피드백 기반으로 requirement 보완
- 파이프라인: story → requirement ↔ domain-model → architecture → implementation

### Cross-cutting 스킬 경계
- **확정 영역**: 무엇이 있고 어떻게 연결되는가 (도메인 용어, 관계, 상태 전이)
- **미확정 영역**: 어떻게 만드는가 (구현 타입, 기술 선택, API 설계)
- **스킬 역할**: 추상화 가드레일 — 사용자가 구현으로 빠지지 않게 가이드

### 사용자 제어 원칙
- Topic 순서(개념 추출 → 관계 → 상태 → 피드백)는 자연스러운 가이드이되 강제 아님
- 사용자가 제어: 다음 topic 전환, 이전 topic 재방문, 일시 정지, 세션 종료
- Topic 간 인터리브 허용 (관계 논의 중 새 개념 발견 시 돌아가기 가능)

### 비기능/시스템 경계는 별도
- 비기능 요구사항과 외부 환경 시스템 경계는 별도 interview로 다룸
- FR에서 도출 가능한 시스템 간 관계는 domain model에서 다룸

## TODOs
- [x] co-revise-requirement-with-domain-model 스킬 설계 및 생성 ✅ 2026-03-26
- [ ] 비기능/시스템 경계 interview를 어디서 다룰지 결정 (co-think-story? 별도 스킬?)
- [ ] architecture 스킬 정의
- [ ] 문제 영역 → 솔루션 영역 전환점의 전체 파이프라인 설계
